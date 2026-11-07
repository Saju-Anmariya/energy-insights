import os
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-tests-only-0123456789")

from app.database import Base
from app.main import app, get_db
from app.models import Consumption


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(bind=engine, autoflush=False)
    Base.metadata.create_all(bind=engine)

    db = TestingSession()
    db.add_all(
        [Consumption(timestamp=datetime(2025, 1, 1, h), mwh=50000.0 + h * 1000) for h in range(3)]
    )
    db.commit()
    db.close()

    def override_get_db():
        session = TestingSession()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client):
    credentials = {"username": "fixture_user", "password": "correct-horse-battery"}
    client.post("/register", json=credentials)
    token = client.post("/login", json=credentials).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}