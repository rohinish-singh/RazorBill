import pytest
from fastapi.testclient import TestClient

try:
    from backend.src.database import init_db
    from backend.src.main import app, get_db_path
except ModuleNotFoundError:
    from src.database import init_db
    from src.main import app, get_db_path


@pytest.fixture
def client(tmp_path):
    test_db = str(tmp_path / "test_health.db")
    init_db(test_db)
    app.dependency_overrides[get_db_path] = lambda: test_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_health_endpoint_returns_200_and_healthy_status(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_cors_allowed_for_frontend_dev_origin(client):
    # Vite dev server default origin
    response = client.get("/health", headers={"Origin": "http://localhost:5173"})
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_cors_rejected_for_unauthorized_origin(client):
    response = client.get("/health", headers={"Origin": "http://unauthorized-domain.com"})
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers
