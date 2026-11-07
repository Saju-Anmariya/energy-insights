from app.security import hash_password, verify_password

CREDENTIALS = {"username": "tester", "password": "correct-horse-battery"}


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_data_requires_login(client):
    assert client.get("/consumption").status_code == 401
    assert client.get("/consumption/stats").status_code == 401


def test_fake_token_is_rejected(client):
    response = client.get("/consumption", headers={"Authorization": "Bearer not-a-real-token"})
    assert response.status_code == 401


def test_register_and_login(client):
    assert client.post("/register", json=CREDENTIALS).status_code == 201
    response = client.post("/login", json=CREDENTIALS)
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_duplicate_registration_is_rejected(client):
    client.post("/register", json=CREDENTIALS)
    assert client.post("/register", json=CREDENTIALS).status_code == 409


def test_wrong_password_is_rejected(client):
    client.post("/register", json=CREDENTIALS)
    response = client.post("/login", json={**CREDENTIALS, "password": "wrong-password-1"})
    assert response.status_code == 401


def test_weak_input_is_rejected(client):
    assert client.post("/register", json={"username": "ab", "password": "short"}).status_code == 422
    bad_name = {"username": "bad name!", "password": "long-enough-pw"}
    assert client.post("/register", json=bad_name).status_code == 422


def test_password_hashing():
    hashed = hash_password("secret-password")
    assert hashed != "secret-password"
    assert verify_password("secret-password", hashed)
    assert not verify_password("other-password", hashed)


def test_consumption_returns_latest_first(client, auth_headers):
    response = client.get("/consumption?limit=2", headers=auth_headers)
    data = response.json()
    assert response.status_code == 200
    assert len(data) == 2
    assert data[0]["timestamp"] == "2025-01-01T02:00:00"
    assert data[0]["mwh"] == 52000.0


def test_consumption_filters_by_start(client, auth_headers):
    response = client.get("/consumption?start=2025-01-01T01:00:00", headers=auth_headers)
    assert len(response.json()) == 2


def test_stats(client, auth_headers):
    body = client.get("/consumption/stats", headers=auth_headers).json()
    assert body["count"] == 3
    assert body["average_mwh"] == 51000.0
    assert body["min_mwh"] == 50000.0
    assert body["max_mwh"] == 52000.0


def test_invalid_limit_is_rejected(client, auth_headers):
    assert client.get("/consumption?limit=0", headers=auth_headers).status_code == 422