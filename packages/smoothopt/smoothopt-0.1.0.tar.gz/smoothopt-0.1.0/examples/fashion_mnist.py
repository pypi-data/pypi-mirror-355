import torch
import torch.nn as nn
from torch.utils.data import DataLoader
import lightning as L
from lightning.pytorch.callbacks import EarlyStopping, ModelCheckpoint
import datasets
import gc
from torchvision import transforms
from transformers import (
    get_cosine_schedule_with_warmup,
    get_linear_schedule_with_warmup,
)
import smoothopt as smo

torch.set_float32_matmul_precision("medium")


class FashionMnistDataset(L.LightningDataModule):
    def __init__(self, num_workers, hyperparams):
        super().__init__()
        self.num_workers = num_workers
        self.hyperparams = hyperparams

    def setup(self, stage=None):
        dataset = datasets.load_dataset(
            "zalando-datasets/fashion_mnist",
            revision="531be5e2ccc9dba0c201ad3ae567a4f3d16ecdd2",
        )

        def transform_train(batch):
            transform = transforms.Compose(
                [
                    transforms.RandomHorizontalFlip(self.hyperparams["random_flip_p"]),
                    transforms.RandomRotation(
                        self.hyperparams["random_rotation_range"]
                    ),
                    transforms.RandomResizedCrop(
                        28,
                        scale=(
                            self.hyperparams["random_scale_min"],
                            self.hyperparams["random_scale_max"],
                        ),
                    ),
                    transforms.ToTensor(),
                    transforms.Normalize((0.5,), (0.5,)),
                    transforms.RandomErasing(
                        p=self.hyperparams["random_erasing_p"],
                        scale=(
                            self.hyperparams["random_erasing_scale_min"],
                            self.hyperparams["random_erasing_scale_min"]
                            + self.hyperparams["random_erasing_scale_range"],
                        ),
                        ratio=(
                            self.hyperparams["random_erasing_ratio_min"],
                            self.hyperparams["random_erasing_ratio_min"]
                            + self.hyperparams["random_erasing_ratio_range"],
                        ),
                        value=0,
                    ),
                ]
            )
            batch["image"] = [transform(img) for img in batch["image"]]
            return batch

        def transform_val(batch):
            transform = transforms.Compose(
                [transforms.ToTensor(), transforms.Normalize((0.5,), (0.5,))]
            )
            batch["image"] = [transform(img) for img in batch["image"]]
            return batch

        train, val = dataset["train"].train_test_split(test_size=0.2, seed=42).values()
        self.train_dataset = train.with_transform(transform_train)
        self.val_dataset = val.with_transform(transform_val)
        self.test_dataset = dataset["test"].with_transform(transform_val)

    def train_dataloader(self):
        return DataLoader(
            self.train_dataset,
            batch_size=self.hyperparams["batch_size"],
            shuffle=True,
            num_workers=self.num_workers,
        )

    def val_dataloader(self):
        return DataLoader(
            self.val_dataset,
            batch_size=self.hyperparams["batch_size"],
            num_workers=self.num_workers,
        )

    def test_dataloader(self):
        return DataLoader(
            self.test_dataset,
            batch_size=self.hyperparams["batch_size"],
            num_workers=self.num_workers,
        )


class CNNModel(L.LightningModule):
    def __init__(self, hyperparams):
        super().__init__()
        self.hyperparams = hyperparams

        # Build conv layers
        conv_layers = []
        channels = 1
        for i in range(hyperparams["num_conv_layers"]):
            next_channels = int(
                hyperparams["base_channels"] * (hyperparams["channel_multiplier"] ** i)
            )
            conv_layers.extend(
                [
                    nn.Conv2d(channels, next_channels, kernel_size=3, padding=1),
                    nn.BatchNorm2d(next_channels)
                    if hyperparams["use_conv_batchnorm"]
                    else nn.Identity(),
                    hyperparams["activation"],
                    nn.MaxPool2d(2),
                    nn.Dropout2d(hyperparams["conv_dropout_rate"]),
                ]
            )
            channels = next_channels

        self.conv_layers = nn.Sequential(*conv_layers)

        # Calculate the size after convolutions
        # Fashion-MNIST is 28x28, each maxpool divides by 2
        final_size = 28 // (2 ** hyperparams["num_conv_layers"])
        final_channels = channels

        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(
                final_channels * final_size * final_size, hyperparams["hidden_size"]
            ),
            nn.BatchNorm1d(hyperparams["hidden_size"])
            if hyperparams["use_fc_batchnorm"]
            else nn.Identity(),
            hyperparams["activation"],
            nn.Dropout(hyperparams["fc_dropout_rate"]),
            nn.Linear(hyperparams["hidden_size"], 10),
        )

    def forward(self, x):
        return self.classifier(self.conv_layers(x))

    def training_step(self, batch, batch_idx):
        x, y = batch["image"], batch["label"]
        preds = self(x)
        loss = nn.CrossEntropyLoss()(preds, y)
        self.log("train_loss", loss, prog_bar=True)
        return loss

    def validation_step(self, batch, batch_idx):
        x, y = batch["image"], batch["label"]
        preds = self(x)

        loss = nn.CrossEntropyLoss()(preds, y)
        self.log("val_loss", loss, prog_bar=True)

        acc = (preds.argmax(dim=1) == y).float().mean()
        self.log("val_acc", acc, prog_bar=True)

        return loss

    def test_step(self, batch, batch_idx):
        x, y = batch["image"], batch["label"]
        preds = self(x)

        acc = (preds.argmax(dim=1) == y).float().mean()
        self.log("test_acc", acc, prog_bar=True)

    def configure_optimizers(self):
        optimizer = torch.optim.AdamW(
            self.parameters(),
            lr=self.hyperparams["lr"],
            weight_decay=self.hyperparams["weight_decay"],
        )
        num_steps = self.trainer.estimated_stepping_batches
        scheduler = self.hyperparams["lr_scheduler"](
            optimizer,
            num_warmup_steps=self.hyperparams["warmup_steps"],
            num_training_steps=num_steps,
        )
        return {
            "optimizer": optimizer,
            "lr_scheduler": {
                "scheduler": scheduler,
                "interval": "step",
            },
        }


def train_model(hyperparams: smo.ParamSet, test=False):
    trainer = L.Trainer(
        max_epochs=hyperparams.num_epochs,
        callbacks=[
            ModelCheckpoint(monitor="val_loss", mode="min", save_top_k=1),
            EarlyStopping(monitor="val_loss", patience=10),
        ],
        accelerator="cuda",
        precision="bf16-mixed",
        enable_model_summary=False,
    )

    data_module = FashionMnistDataset(hyperparams=hyperparams, num_workers=8)

    with trainer.init_module():
        model = CNNModel(hyperparams=hyperparams)

    gc.collect()
    trainer.fit(model, data_module)

    best_model = CNNModel.load_from_checkpoint(
        trainer.checkpoint_callback.best_model_path, hyperparams=hyperparams
    )
    trainer.validate(best_model, data_module, verbose=False)
    metrics = {k: v.item() for k, v in trainer.callback_metrics.items()}

    if test:
        trainer.test(best_model, data_module)

    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    return metrics


if __name__ == "__main__":
    study = smo.minimize(
        "val_loss",
        params={
            "num_epochs": smo.range(1, 100),
            "batch_size": smo.ordinal([64, 128, 256, 512]),
            "random_rotation_range": smo.range(0, 180),
            "random_flip_p": smo.range(0.0, 0.5),
            "random_scale_min": smo.range(0.5, 1.0),
            "random_scale_max": smo.range(1.0, 1.5),
            "random_erasing_p": smo.range(0.0, 1.0),
            "random_erasing_scale_min": smo.range(0.0, 0.5),
            "random_erasing_scale_range": smo.range(0.0, 0.5),
            "random_erasing_ratio_min": smo.range(0.2, 1.0),
            "random_erasing_ratio_range": smo.range(0.0, 5.0),
            "lr": smo.range(1e-6, 0.02, log_scale=True),
            "lr_scheduler": smo.choice(
                [get_cosine_schedule_with_warmup, get_linear_schedule_with_warmup]
            ),
            "warmup_steps": smo.range(0, 1000),
            "weight_decay": smo.range(0.0, 0.2),
            "activation": smo.choice([nn.ReLU(), nn.SiLU(), nn.GELU(), nn.Tanh()]),
            "num_conv_layers": smo.range(1, 4),
            "base_channels": smo.range(8, 128),
            "channel_multiplier": smo.range(1.0, 3.5),
            "hidden_size": smo.range(20, 512),
            "conv_dropout_rate": smo.range(0.0, 0.5),
            "fc_dropout_rate": smo.range(0.0, 0.5),
            "use_conv_batchnorm": smo.choice([True, False]),
            "use_fc_batchnorm": smo.choice([True, False]),
        },
    )

    for i in range(100):
        trial = study.start_trial()
        metrics = train_model(trial.params)
        trial.report(metrics)
        study.save()
