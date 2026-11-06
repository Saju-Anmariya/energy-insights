def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_consumption_returns_latest_first(client):
    response = client.get("/consumption?limit=2")
    data = response.json()
    assert response.status_code == 200
    assert len(data) == 2
    assert data[0]["timestamp"] == "2025-01-01T02:00:00"
    assert data[0]["mwh"] == 52000.0


def test_consumption_filters_by_start(client):
    response = client.get("/consumption?start=2025-01-01T01:00:00")
    assert len(response.json()) == 2


def test_stats(client):
    body = client.get("/consumption/stats").json()
    assert body["count"] == 3
    assert body["average_mwh"] == 51000.0
    assert body["min_mwh"] == 50000.0
    assert body["max_mwh"] == 52000.0


def test_invalid_limit_is_rejected(client):
    assert client.get("/consumption?limit=0").status_code == 422