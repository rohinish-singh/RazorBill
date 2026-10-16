import pytest
from fastapi.testclient import TestClient

try:
    from backend.src.database import init_db
    from backend.src.main import app, get_db_path
    from backend.src.schemas import Category, Source, Status
except ModuleNotFoundError:
    from src.database import init_db
    from src.main import app, get_db_path
    from src.schemas import Category, Source, Status


@pytest.fixture
def client(tmp_path):
    test_db = str(tmp_path / "test_api_razorbill.db")
    init_db(test_db)
    app.dependency_overrides[get_db_path] = lambda: test_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def test_post_incident_creates_record(client):
    payload = {
        "event_id": "evt_api_01",
        "camera_id": "CAM_GATE",
        "timestamp_seconds": 12.5,
        "category": "tailgating",
        "summary": "Second person followed through secure gate.",
        "confidence": 0.95,
        "confidence_type": "vlm_calibrated",
        "frame_path": "data/frames/CAM_GATE/evt_api_01.jpg",
        "source": "vlm",
        "processing_ms": 420,
        "status": "classified",
        "evidence_notes": "Turnstile badge count was 1, detected person count was 2.",
        "created_at": "2026-10-15T12:00:00Z",
    }

    response = client.post("/api/incidents", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["event_id"] == "evt_api_01"
    assert data["category"] == "tailgating"
    assert data["confidence"] == 0.95


def test_get_incident_by_id_success(client):
    payload = {
        "event_id": "evt_api_lookup_01",
        "camera_id": "CAM_DOCK",
        "timestamp_seconds": 33.1,
        "category": "person_down",
        "summary": "Fallen worker near dock door.",
        "confidence": 0.91,
        "confidence_type": "vlm_calibrated",
        "frame_path": "data/frames/CAM_DOCK/evt_api_lookup_01.jpg",
        "source": "vlm",
        "processing_ms": 380,
        "status": "classified",
        "evidence_notes": "Prone posture detected.",
        "created_at": "2026-10-15T12:10:00Z",
    }
    post_resp = client.post("/api/incidents", json=payload)
    assert post_resp.status_code == 200

    get_resp = client.get("/api/incidents/evt_api_lookup_01")
    assert get_resp.status_code == 200
    retrieved = get_resp.json()
    assert retrieved["event_id"] == "evt_api_lookup_01"
    assert retrieved["camera_id"] == "CAM_DOCK"
    assert retrieved["timestamp_seconds"] == 33.1
    assert retrieved["category"] == "person_down"
    assert retrieved["summary"] == "Fallen worker near dock door."
    assert retrieved["confidence"] == 0.91
    assert retrieved["confidence_type"] == "vlm_calibrated"
    assert retrieved["source"] == "vlm"
    assert retrieved["processing_ms"] == 380
    assert retrieved["status"] == "classified"
    assert retrieved["created_at"] == "2026-10-15T12:10:00Z"


def test_post_incident_upserts_duplicate_event_id(client):
    initial_payload = {
        "event_id": "evt_api_02",
        "camera_id": "CAM_NORTH",
        "timestamp_seconds": 88.0,
        "category": "unknown",
        "summary": "Motion candidate.",
        "confidence": None,
        "confidence_type": "unavailable",
        "frame_path": "data/frames/CAM_NORTH/evt_api_02.jpg",
        "source": "rule",
        "processing_ms": None,
        "status": "candidate",
        "evidence_notes": None,
        "created_at": "2026-10-15T12:00:00Z",
    }
    resp1 = client.post("/api/incidents", json=initial_payload)
    assert resp1.status_code == 200
    assert resp1.json()["status"] == "candidate"

    # Upsert with classified details
    updated_payload = {
        "event_id": "evt_api_02",
        "camera_id": "CAM_NORTH",
        "timestamp_seconds": 88.0,
        "category": "person_down",
        "summary": "Individual on warehouse floor motionless.",
        "confidence": 0.89,
        "confidence_type": "vlm_calibrated",
        "frame_path": "data/frames/CAM_NORTH/evt_api_02.jpg",
        "source": "vlm",
        "processing_ms": 610,
        "status": "classified",
        "evidence_notes": "Aspect ratio change confirmed.",
        "created_at": "2026-10-15T12:00:02Z",
    }
    resp2 = client.post("/api/incidents", json=updated_payload)
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["category"] == "person_down"
    assert data2["status"] == "classified"
    assert data2["confidence"] == 0.89

    # Verify retrieval returns the updated state
    get_resp = client.get("/api/incidents/evt_api_02")
    assert get_resp.status_code == 200
    assert get_resp.json()["category"] == "person_down"


def test_post_incident_rejects_invalid_payload(client):
    invalid_payload = {
        "event_id": "evt_invalid",
        "camera_id": "CAM_01",
        "timestamp_seconds": -5.0,  # Negative timestamp forbidden
        "category": "not_a_category",  # Invalid category
        "summary": "Invalid payload",
        "frame_path": "path.jpg",
        "source": "vlm",
        "status": "classified",
        "created_at": "invalid_date",
    }
    response = client.post("/api/incidents", json=invalid_payload)
    assert response.status_code == 422


def test_get_incident_by_id_returns_404_when_missing(client):
    response = client.get("/api/incidents/evt_does_not_exist")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
