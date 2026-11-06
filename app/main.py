from fastapi import FastAPI, Depends, Query
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
def list_consumption(limit: int = Query(24, ge=1, le=1000), db: Session = Depends(get_db)):
    rows = (
        db.query(models.Consumption)
        .order_by(models.Consumption.timestamp.desc())
        .limit(limit)
        .all()
    )
    return [{"timestamp": r.timestamp.isoformat(), "mwh": r.mwh} for r in rows]