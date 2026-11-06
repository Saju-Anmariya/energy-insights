from sqlalchemy import Column, Integer, Float, DateTime
from .database import Base


class Consumption(Base):
    __tablename__ = "consumption"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, unique=True, index=True, nullable=False)
    mwh = Column(Float, nullable=False)