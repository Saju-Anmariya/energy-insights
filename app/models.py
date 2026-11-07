from sqlalchemy import Column, Integer, Float, DateTime, String
from .database import Base


class Consumption(Base):
    __tablename__ = "consumption"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, unique=True, index=True, nullable=False)
    mwh = Column(Float, nullable=False)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)