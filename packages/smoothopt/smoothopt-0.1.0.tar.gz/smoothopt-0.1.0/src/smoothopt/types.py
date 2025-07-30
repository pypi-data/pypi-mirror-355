from typing import Union, Tuple, Any, Optional, Literal, TYPE_CHECKING, List
import time

if TYPE_CHECKING:
    from .optimization import (
        Study,
    )  # Only imported for type checking (avoids circular import)


class Param:
    def __init__(
        self,
        param_type: Literal["numeric", "ordinal", "categorical"],
        bounds: Optional[Tuple[Union[float, int], Union[float, int]]] = None,
        values: Optional[List[Any]] = None,
        log_scale: bool = False,
        dtype: Optional[type] = None,
    ):
        self.param_type = param_type
        self.bounds = bounds
        self.values = values
        self.log_scale = log_scale
        self.dtype = dtype


class ParamSet(dict):
    def __init__(self, **suggestions: Any):
        super().__init__(suggestions)

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"No parameter '{name}' in {list(self.keys())}")

    def __setattr__(self, name, value):
        self[name] = value

    def __rich_repr__(self):
        for k, v in self.items():
            yield k, v

    def subset(self, *keys):
        """Get a subset of parameters"""
        return ParamSet(**{k: self[k] for k in keys if k in self})


class BestParams:
    def __init__(
        self,
        params: ParamSet,
        obj_mean: float,
        obj_std: float,
        cost_mean: float,
        cost_std: float,
        raw_metrics: dict[str, Any],
    ):
        self.params = params
        self.obj_mean = obj_mean
        self.obj_std = obj_std
        self.cost_mean = cost_mean
        self.cost_std = cost_std
        self.raw_metrics = raw_metrics


class Trial:
    def __init__(
        self,
        study: "Study",
        params: ParamSet,
        trial_number: int,
        strategy: Literal["sobol", "bayes_opt"],
        expected_cost: float | None,
    ):
        self.study = study
        self.params = params
        self.status: Literal["running", "completed", "failed"] = "running"
        self.metrics = None
        self.trial_number = trial_number
        self.strategy = strategy
        self.expected_cost = expected_cost

        self.start_time = time.time()
        self.elapsed_time = None

    def report(self, metrics: dict[str, Any], override_time: Optional[float] = None):
        if self.status == "completed":
            raise ValueError("Trial is already completed")

        self.status = "completed"
        self.metrics = metrics

        if override_time is not None:
            self.elapsed_time = override_time
        else:
            self.elapsed_time = time.time() - self.start_time

        self.study.model_refit_needed = True
        self.study.print_trial_results(self)
        self.study.print_best_params_summary()

    def to_dict(self):
        return {
            "params": self.params,
            "status": self.status,
            "metrics": self.metrics,
            "trial_number": self.trial_number,
            "strategy": self.strategy,
            "expected_cost": self.expected_cost,
            "start_time": self.start_time,
            "elapsed_time": self.elapsed_time,
        }

    @staticmethod
    def from_dict(study: "Study", data: dict[str, Any]):
        trial = Trial(
            study,
            data["params"],
            data["trial_number"],
            data["strategy"],
            data["expected_cost"],
        )
        trial.status = data["status"]
        trial.metrics = data["metrics"]
        trial.start_time = data["start_time"]
        trial.elapsed_time = data["elapsed_time"]
        return trial
