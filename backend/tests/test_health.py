from fastapi.testclient import TestClient

try:
    from backend.src.main import app
except ModuleNotFoundError:
    from src.main import app

client = TestClient(app)


def test_health_endpoint_returns_200_and_healthy_status():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

