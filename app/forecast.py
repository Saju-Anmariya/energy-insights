import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error

FEATURES = ["lag_1", "lag_24", "lag_168", "hour", "dayofweek"]


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """Expects columns 'timestamp' and 'mwh'. Adds past values and calendar features."""
    d = df.sort_values("timestamp").reset_index(drop=True).copy()
    d["lag_1"] = d["mwh"].shift(1)       # 1 hour ago
    d["lag_24"] = d["mwh"].shift(24)     # same hour yesterday
    d["lag_168"] = d["mwh"].shift(168)   # same hour last week
    d["hour"] = d["timestamp"].dt.hour
    d["dayofweek"] = d["timestamp"].dt.day_of_week
    return d.dropna().reset_index(drop=True)


def backtest(df: pd.DataFrame, test_fraction: float = 0.2):
    """Train on the first part of the data, forecast the last part, return results and errors."""
    d = add_features(df)
    split = int(len(d) * (1 - test_fraction))
    train, test = d.iloc[:split], d.iloc[split:].copy()

    model = HistGradientBoostingRegressor(random_state=42)
    model.fit(train[FEATURES], train["mwh"])
    test["forecast"] = model.predict(test[FEATURES])

    metrics = {
        "model_mae": float(mean_absolute_error(test["mwh"], test["forecast"])),
        "baseline_mae": float(mean_absolute_error(test["mwh"], test["lag_1"])),
        "average_load": float(test["mwh"].mean()),
    }
    return test, metrics