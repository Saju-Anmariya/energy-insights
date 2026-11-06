from datetime import timedelta

import pandas as pd
import streamlit as st
from sqlalchemy import select

from app.database import engine
from app.forecast import backtest
from app.models import Consumption

st.set_page_config(page_title="Energy Insights", layout="wide")
st.title("Energy Insights: German electricity grid load")
st.caption("Source: Bundesnetzagentur | SMARD.de")


@st.cache_data
def load_data():
    df = pd.read_sql(select(Consumption.timestamp, Consumption.mwh), engine)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df.sort_values("timestamp").reset_index(drop=True)


@st.cache_data
def run_backtest(df):
    return backtest(df)


df = load_data()
min_date = df["timestamp"].min().date()
max_date = df["timestamp"].max().date()

st.subheader("Grid load over time")
default_start = max(min_date, max_date - timedelta(days=30))
selected = st.date_input(
    "Date range",
    value=(default_start, max_date),
    min_value=min_date,
    max_value=max_date,
)
if len(selected) != 2:
    st.info("Select a start date and an end date.")
    st.stop()

start, end = selected
mask = (df["timestamp"].dt.date >= start) & (df["timestamp"].dt.date <= end)
view = df.loc[mask].set_index("timestamp")

col1, col2, col3 = st.columns(3)
col1.metric("Hours shown", f"{len(view):,}")
col2.metric("Average load (MWh)", f"{view['mwh'].mean():,.0f}")
col3.metric("Peak load (MWh)", f"{view['mwh'].max():,.0f}")
st.line_chart(view["mwh"])

st.subheader("Forecast vs actual (one hour ahead)")
test, metrics = run_backtest(df)

c1, c2, c3 = st.columns(3)
c1.metric("Model error (MAE)", f"{metrics['model_mae']:,.0f} MWh")
c2.metric("Baseline error (previous hour)", f"{metrics['baseline_mae']:,.0f} MWh")
c3.metric("Model error vs average load", f"{metrics['model_mae'] / metrics['average_load']:.1%}")

days = st.slider("Days to show from the test period", 1, 14, 7)
recent = test.tail(days * 24).set_index("timestamp")[["mwh", "forecast"]]
recent = recent.rename(columns={"mwh": "Actual", "forecast": "Forecast"})
st.line_chart(recent)
st.caption("The model was trained on the first 80% of the data and evaluated on the last 20%.")