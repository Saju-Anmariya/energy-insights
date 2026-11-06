from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from . import models
from .database import Base, engine, SessionLocal

Base.metadata.create_all(bind=engine)
app = FastAPI(title="Energy Insights API")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/consumption")
def list_consumption(
    limit: int = Query(24, ge=1, le=1000),
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    db: Session = Depends(get_db),
):
    query = db.query(models.Consumption)
    if start is not None:
        query = query.filter(models.Consumption.timestamp >= start)
    if end is not None:
        query = query.filter(models.Consumption.timestamp <= end)
    rows = query.order_by(models.Consumption.timestamp.desc()).limit(limit).all()
    return [{"timestamp": r.timestamp.isoformat(), "mwh": r.mwh} for r in rows]


@app.get("/consumption/stats")
def consumption_stats(db: Session = Depends(get_db)):
    count, avg, low, high = db.query(
        func.count(models.Consumption.id),
        func.avg(models.Consumption.mwh),
        func.min(models.Consumption.mwh),
        func.max(models.Consumption.mwh),
    ).one()
    return {
        "count": count,
        "average_mwh": round(avg, 1) if avg is not None else None,
        "min_mwh": low,
        "max_mwh": high,
    }