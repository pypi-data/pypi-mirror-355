Making a hyperparameter tuning / NAS library for deep learning.

Usage:
```python
import smoothopt as smo

study = smo.minimize(
    'val_loss',
    params={
        'num_epochs': smo.range(1, 100),
        'learning_rate': smo.range(1e-6, 0.02, log_scale=True),
        'batch_size': smo.ordinal([64, 128, 256, 512]),
        'activation': smo.choice([nn.ReLU(), nn.SiLU(), nn.GELU(), nn.Tanh()]),
    }
)

while True:
    trial = study.start_trial()
    metrics = train_model(trial.params) # Your model training loop
    trial.report(metrics)
    study.save('study.pkl')
```
