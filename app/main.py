from datetime import datetime
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import func
from sqlalchemy.orm import Session

from . import models, security
from .database import Base, engine, SessionLocal

Base.metadata.create_all(bind=engine)
app = FastAPI(title="Energy Insights API")
bearer = HTTPBearer(auto_error=False)


class Credentials(BaseModel):
    username: str = Field(min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_.-]+$")
    password: str = Field(min_length=8, max_length=64)

    @field_validator("password")
    @classmethod
    def password_fits_bcrypt(cls, value: str) -> str:
        if len(value.encode("utf-8")) > 72:
            raise ValueError("password is too long")
        return value


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer),
    db: Session = Depends(get_db),
):
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    username = security.decode_token(credentials.credentials)
    user = None
    if username is not None:
        user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
    return user


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/register", status_code=status.HTTP_201_CREATED)
def register(data: Credentials, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.username == data.username).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")
    db.add(models.User(username=data.username, password_hash=security.hash_password(data.password)))
    db.commit()
    return {"username": data.username}


@app.post("/login")
def login(data: Credentials, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == data.username).first()
    if user is None or not security.verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    return {"access_token": security.create_token(user.username), "token_type": "bearer"}


@app.get("/consumption")
def list_consumption(
    limit: int = Query(24, ge=1, le=1000),
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    query = db.query(models.Consumption)
    if start is not None:
        query = query.filter(models.Consumption.timestamp >= start)
    if end is not None:
        query = query.filter(models.Consumption.timestamp <= end)
    rows = query.order_by(models.Consumption.timestamp.desc()).limit(limit).all()
    return [{"timestamp": r.timestamp.isoformat(), "mwh": r.mwh} for r in rows]


@app.get("/consumption/stats")
def consumption_stats(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
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