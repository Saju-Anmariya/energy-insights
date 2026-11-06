import numpy as np
import pandas as pd

from app.forecast import backtest


def make_data(hours=600):
    timestamps = pd.date_range("2025-01-01", periods=hours, freq="h")
    values = 50000 + 8000 * np.sin(np.arange(hours) * 2 * np.pi / 24)
    return pd.DataFrame({"timestamp": timestamps, "mwh": values})


def test_backtest_returns_forecasts_and_metrics():
    test, metrics = backtest(make_data())
    assert len(test) > 0
    assert {"mwh", "forecast"} <= set(test.columns)
    assert test["forecast"].notna().all()
    assert metrics["model_mae"] >= 0
    assert metrics["baseline_mae"] >= 0