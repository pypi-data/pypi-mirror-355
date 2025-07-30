from .types import Param, ParamSet, BestParams, Trial
from typing import Union, Dict, Literal, List, Tuple
import torch
from botorch.utils.sampling import draw_sobol_samples
from botorch.acquisition.logei import qLogNoisyExpectedImprovement
from botorch.optim import optimize_acqf
from botorch.models.gp_regression_mixed import MixedSingleTaskGP, SingleTaskGP
from botorch.sampling.normal import SobolQMCNormalSampler
from botorch.fit import fit_gpytorch_mll
from botorch.models.transforms import (
    Log,
    Standardize,
    Normalize,
    ChainedOutcomeTransform,
)
from gpytorch.mlls import ExactMarginalLogLikelihood
import dill
import math
import rich.box
from rich.pretty import Pretty
from rich.columns import Columns
from rich import print
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.console import Group


# NEI per time acquisition function in log-space for numerical stability.
# Time is clipped to a minimum value to avoid feedback loops where the optimizer gets stuck evaluating ultra fast but bad configurations.
class qLogClippedNEIPerTime(qLogNoisyExpectedImprovement):
    def __init__(
        self,
        obj_model: Union[MixedSingleTaskGP, SingleTaskGP],
        cost_model: Union[MixedSingleTaskGP, SingleTaskGP],
        X_baseline: torch.Tensor,
        min_cost: float,
        sampler: SobolQMCNormalSampler,
        prune_baseline: bool = True,
    ):
        super().__init__(
            model=obj_model,
            X_baseline=X_baseline,
            sampler=sampler,
            prune_baseline=prune_baseline,
        )
        self.cost_model = cost_model
        self.log_min_cost = math.log(min_cost)

    def forward(self, X: torch.Tensor) -> torch.Tensor:
        nei = super().forward(X)
        cost_posterior = self.cost_model.posterior(X)
        log_cost = torch.log(cost_posterior.mean.flatten())
        clipped_log_cost = log_cost.clamp(min=self.log_min_cost)

        return nei - clipped_log_cost


class Study:
    def __init__(
        self,
        objective: str,
        direction: Literal["minimize", "maximize"],
        params: Dict[str, Param],
    ):
        self.objective = objective
        self.direction = direction
        self.params = params

        self.trials: List[Trial] = []

        self.model_refit_needed = True
        self.latest_models = None

        bounds_list = []
        for p in self.params.values():
            if p.param_type == "numeric":
                lower, upper = torch.tensor(p.bounds, dtype=torch.float64)
                if p.log_scale:
                    lower = torch.log(lower)
                    upper = torch.log(upper)
                bounds_list.append([lower, upper])
            else:
                # Oridinals and categoricals are converted to integer indices
                assert p.values is not None
                bounds_list.append([0, len(p.values) - 1])

        self.bounds = torch.tensor(bounds_list, dtype=torch.float64).transpose(0, 1)

        self.categorical_dims = [
            i
            for i, p in enumerate(self.params.values())
            if p.param_type == "categorical"
        ]
        self.qmc_sampler = SobolQMCNormalSampler(torch.Size([1024]), seed=42)

        self.sobol_samples = draw_sobol_samples(
            bounds=self.bounds,
            n=min(10, 2 * len(self.params) + 5),  # Untested heuristic
            q=1,
            seed=42,
        ).squeeze(-2)

    def get_observations_tensor(
        self,
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        assert len(self.trials) > 0, "No trials have been completed yet."

        x = []
        y = []
        t = []
        for trial in self.trials:
            if trial.status != "completed":
                continue
            assert trial.metrics is not None

            params = []
            for param_name, param in self.params.items():
                if param.param_type == "numeric":
                    value = trial.params[param_name]
                    if param.log_scale:
                        value = torch.log(
                            torch.tensor(value, dtype=torch.float64)
                        ).item()
                    params.append(value)
                else:
                    assert param.values is not None, "Parameter values are not set."
                    params.append(param.values.index(trial.params[param_name]))
            x.append(torch.tensor(params, dtype=torch.float64))
            y.append(trial.metrics[self.objective])
            t.append(trial.elapsed_time)

        return (
            torch.stack(x),
            torch.tensor(y, dtype=torch.float64).unsqueeze(-1),
            torch.tensor(t, dtype=torch.float64).unsqueeze(-1),
        )

    def get_params_from_tensor(self, tensor: torch.Tensor) -> ParamSet:
        result = ParamSet()
        for idx, (param_name, param) in enumerate(self.params.items()):
            if param.param_type == "numeric":
                value = tensor[idx]
                if param.log_scale:
                    value = torch.exp(value)
                value = value.item()
                if param.dtype == int:
                    value = round(value)
                assert param.dtype is not None
                result[param_name] = param.dtype(value)
            else:
                choice = round(tensor[idx].item())
                assert param.values is not None
                result[param_name] = param.values[choice]
        return result

    def fit_gaussian_process(self, **kwargs) -> Union[SingleTaskGP, MixedSingleTaskGP]:
        if len(self.categorical_dims) == 0:
            gp = SingleTaskGP(**kwargs)
        else:
            gp = MixedSingleTaskGP(cat_dims=self.categorical_dims, **kwargs)

        mll = ExactMarginalLogLikelihood(gp.likelihood, gp)
        fit_gpytorch_mll(mll)

        return gp

    def get_models(self, x: torch.Tensor, obj: torch.Tensor, cost: torch.Tensor):
        if not self.model_refit_needed:
            assert self.latest_models is not None
            return self.latest_models

        if self.direction == "minimize":
            obj = -obj

        # TODO: Find good priors for noise and lengthscale
        # Also explore using parametric models for the mean (eg alpha * sqrt((x + beta)^2 + gamma) + beta for modelling unimodal assumptions)
        obj_model = self.fit_gaussian_process(
            train_X=x,
            train_Y=torch.exp(
                obj
            ),  # Increases stability for loss-based objectives. TODO: Handle other objective types?
            input_transform=Normalize(d=x.shape[1]),
            outcome_transform=Standardize(m=1),
        )

        cost_model = self.fit_gaussian_process(
            train_X=x,
            train_Y=cost,
            input_transform=Normalize(d=x.shape[1]),
            outcome_transform=ChainedOutcomeTransform(
                tf1=Log(),
                tf2=Standardize(m=1),
            ),
        )

        self.latest_models = (obj_model, cost_model)
        self.model_refit_needed = False

        return self.latest_models

    def suggest_params(
        self,
    ) -> Tuple[ParamSet, Literal["sobol", "bayes_opt"], float | None]:
        if len(self.trials) < len(self.sobol_samples):
            # Few observations, use Sobol samples
            candidate = self.sobol_samples[len(self.trials)]
            expected_cost = None
            if len(self.trials) > 0:
                x, obs, cost = self.get_observations_tensor()
                obj_model, cost_model = self.get_models(x, obs, cost)
                expected_cost = cost_model.posterior(candidate.unsqueeze(0)).mean.item()

            return (self.get_params_from_tensor(candidate), "sobol", expected_cost)

        # Enough observations, use Bayesian optimization
        x, obs, cost = self.get_observations_tensor()
        obj_model, cost_model = self.get_models(x, obs, cost)

        posterior = obj_model.posterior(x)
        predicted_means = posterior.mean
        best_idx = int(torch.argmax(predicted_means).item())
        cost_at_best = cost[best_idx].item()

        acquisition_fn = qLogClippedNEIPerTime(
            obj_model=obj_model,
            cost_model=cost_model,
            X_baseline=x,
            min_cost=0.8 * cost_at_best,
            sampler=self.qmc_sampler,
            prune_baseline=True,
        )

        candidate, _ = optimize_acqf(
            acq_function=acquisition_fn,
            bounds=self.bounds,
            q=1,
            num_restarts=20,
            raw_samples=1024,
        )
        candidate = candidate.squeeze(0)

        expected_cost = cost_model.posterior(candidate.unsqueeze(0)).mean.item()

        return (self.get_params_from_tensor(candidate), "bayes_opt", expected_cost)

    def start_trial(self) -> Trial:
        params, strategy, expected_cost = self.suggest_params()
        trial = Trial(
            study=self,
            params=params,
            trial_number=len(self.trials),
            strategy=strategy,
            expected_cost=expected_cost,
        )
        self.print_pretrial_summary(trial)
        self.trials.append(trial)
        return trial

    def save(self, path: str = "study.pkl"):
        data = {
            "objective": self.objective,
            "direction": self.direction,
            "params": self.params,
            "trials": [
                trial.to_dict() for trial in self.trials if trial.status != "running"
            ],
        }
        with open(path, "wb") as f:
            dill.dump(data, f)

    @staticmethod
    def load(path: str):
        with open(path, "rb") as f:
            data = dill.load(f)
        study = Study(
            objective=data["objective"],
            direction=data["direction"],
            params=data["params"],
        )
        study.trials = [Trial.from_dict(study, trial) for trial in data["trials"]]
        return study

    def print_pretrial_summary(self, trial: Trial):
        strategy_names = {
            "sobol": "Sobol (quasi-random)",
            "bayes_opt": "Bayesian optimization",
        }
        trial_info = Table(box=rich.box.SIMPLE, highlight=True)
        trial_info.add_column("Trial number")
        trial_info.add_column("Strategy")
        trial_info.add_column("Expected runtime")
        trial_info.add_row(
            str(trial.trial_number),
            strategy_names[trial.strategy],
            f"{trial.expected_cost:.2f} seconds"
            if trial.expected_cost is not None
            else "Unknown",
        )

        def format_value(value):
            if isinstance(value, float):
                return f"{value:.2g}"
            elif hasattr(value, "__name__"):
                return value.__name__
            return str(value)

        param_table = Columns(
            [f"{k}: {format_value(v)}" for k, v in trial.params.items()],
            title=Text("Trial parameters", style="bold"),
            expand=False,
        )

        print(
            Panel.fit(
                Columns(
                    [
                        trial_info,
                        param_table,
                    ]
                ),
                box=rich.box.SIMPLE,
                width=100,
            )
        )

    def print_trial_results(self, trial: Trial):
        status_names = {
            "completed": "Completed",
            "failed": "Failed",
            "running": "Running",
        }

        trial_results = Table(
            title="Trial results", box=rich.box.SIMPLE, highlight=True
        )
        columns = ["Trial number", "Status", "Runtime"]
        rows = [
            f"{trial.trial_number}",
            f"{status_names[trial.status]}",
            f"{trial.elapsed_time:.2f} seconds",
        ]
        if trial.metrics is not None:
            for k, v in trial.metrics.items():
                columns.append(k)
                rows.append(f"{v:.4f}")

        for col in columns:
            trial_results.add_column(col)
        trial_results.add_row(*rows)

        print()
        print(trial_results)

    def print_best_params_summary(self):
        def format_uncertainty(value, std):
            num_decimals = max(0, -int(math.log10(max(std, 1e-10))) + 2)
            return f"{value:.{num_decimals}f} ± {std:.{num_decimals}f}"

        best_params = self.get_best_params()

        obj_estimate = format_uncertainty(best_params.obj_mean, best_params.obj_std)
        cost_estimate = f"{best_params.cost_mean:.2f} seconds"

        mean_estimate = Table(
            title="Mean estimates", box=rich.box.SIMPLE, highlight=True
        )
        mean_estimate.add_column("Runtime")
        mean_estimate.add_column(self.objective)
        mean_estimate.add_row(cost_estimate, obj_estimate)

        raw_metrics = Table(title="Raw metrics", box=rich.box.SIMPLE, highlight=True)
        for k in best_params.raw_metrics.keys():
            raw_metrics.add_column(str(k))
        raw_metrics.add_row(*[f"{v:.4f}" for v in best_params.raw_metrics.values()])

        best_params_stats = Columns(
            [
                mean_estimate,
                raw_metrics,
            ],
            align="center",
            expand=False,
            equal=True,
        )

        print()
        print(
            Panel.fit(
                Group(best_params_stats, Pretty(best_params.params)),
                title="Best parameters so far",
                box=rich.box.HORIZONTALS,
                padding=(1, 1),
                width=100,
            )
        )

    def get_best_params(self) -> BestParams:
        if len(self.trials) == 0:
            raise ValueError("No observations have been made yet.")

        x, obj, cost = self.get_observations_tensor()

        obj_model, cost_model = self.get_models(x, obj, cost)

        with torch.no_grad():
            posterior = obj_model.posterior(x)
            predicted_means = posterior.mean
            best_idx = int(torch.argmax(predicted_means).item())

            mu = predicted_means[best_idx].item()
            sigma = posterior.variance[best_idx].sqrt().item()

            # Transform back
            best_mean = math.log(mu) - sigma**2 / (2 * mu**2)
            best_std = sigma / mu

            cost_posterior = cost_model.posterior(x)
            cost_mean = cost_posterior.mean[best_idx].item()
            cost_std = cost_posterior.variance[best_idx].sqrt().item()

        if self.direction == "minimize":
            best_mean = -best_mean

        raw_metrics = self.trials[best_idx].metrics
        assert raw_metrics is not None

        return BestParams(
            params=self.get_params_from_tensor(x[best_idx]),
            obj_mean=best_mean,
            obj_std=best_std,
            cost_mean=cost_mean,
            cost_std=cost_std,
            raw_metrics=raw_metrics,
        )
