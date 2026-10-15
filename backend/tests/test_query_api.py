from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

try:
    from backend.src.database import init_db, upsert_incident
    from backend.src.main import app, get_db_path
    from backend.src.schemas import Category, ClassifiedIncident, Source, Status
except ModuleNotFoundError:
    from src.database import init_db, upsert_incident
    from src.main import app, get_db_path
    from src.schemas import Category, ClassifiedIncident, Source, Status


@pytest.fixture
def test_db_path(tmp_path):
    db_file = str(tmp_path / "test_query_razorbill.db")
    init_db(db_file)
    return db_file


@pytest.fixture
def client(test_db_path):
    app.dependency_overrides[get_db_path] = lambda: test_db_path
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def seeded_client(client, test_db_path):
    incidents = [
        ClassifiedIncident(
            event_id="evt_1",
            camera_id="CAM_01",
            timestamp_seconds=10.0,
            category=Category.fighting,
            summary="Fight in lobby",
            confidence=0.90,
            frame_path="data/frames/CAM_01/evt_1.jpg",
            source=Source.vlm,
            status=Status.classified,
            created_at="2026-10-15T10:00:00Z",
        ),
        ClassifiedIncident(
            event_id="evt_2",
            camera_id="CAM_02",
            timestamp_seconds=20.0,
            category=Category.tailgating,
            summary="Tailgating at secure door",
            confidence=0.85,
            frame_path="data/frames/CAM_02/evt_2.jpg",
            source=Source.vlm,
            status=Status.classified,
            created_at="2026-10-15T10:05:00Z",
        ),
        ClassifiedIncident(
            event_id="evt_3",
            camera_id="CAM_02",
            timestamp_seconds=30.0,
            category=Category.tailgating,
            summary="Second tailgating event",
            confidence=0.88,
            frame_path="data/frames/CAM_02/evt_3.jpg",
            source=Source.vlm,
            status=Status.classified,
            created_at="2026-10-15T10:10:00Z",
        ),
        ClassifiedIncident(
            event_id="evt_4",
            camera_id="CAM_01",
            timestamp_seconds=40.0,
            category=Category.person_down,
            summary="Person slipped and fell",
            confidence=0.92,
            frame_path="data/frames/CAM_01/evt_4.jpg",
            source=Source.vlm,
            status=Status.classified,
            created_at="2026-10-14T15:00:00Z",
        ),
    ]
    for inc in incidents:
        upsert_incident(inc, db_path=test_db_path)
    return client


def test_query_valid_category(seeded_client):
    """Test 1: Valid category question."""
    response = seeded_client.post("/api/query", json={"question": "Show fighting incidents."})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["interpreted_filters"]["category"] == "fighting"
    assert len(data["incidents"]) == 1
    assert data["incidents"][0]["event_id"] == "evt_1"
    assert "Found 1 matching incident" in data["answer"]


def test_query_valid_camera(seeded_client):
    """Test 2: Valid camera question."""
    response = seeded_client.post("/api/query", json={"question": "Show incidents from CAM_01."})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["interpreted_filters"]["camera_id"] == "CAM_01"
    assert len(data["incidents"]) == 2
    event_ids = {i["event_id"] for i in data["incidents"]}
    assert event_ids == {"evt_1", "evt_4"}


def test_query_combined_category_and_camera(seeded_client):
    """Test 3: Combined category and camera question (matching SHARED_CONTRACTS.md example)."""
    response = seeded_client.post(
        "/api/query",
        json={"question": "Show all tailgating events from camera 2 on 2026-10-15"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["interpreted_filters"]["category"] == "tailgating"
    assert data["interpreted_filters"]["camera_id"] == "CAM_02"
    assert len(data["incidents"]) == 2
    assert "Found 2 matching incidents" in data["answer"]


def test_query_date_based(seeded_client):
    """Test 4: Date-based question."""
    response = seeded_client.post("/api/query", json={"question": "Show incidents from 2026-10-14"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert len(data["incidents"]) == 1
    assert data["incidents"][0]["event_id"] == "evt_4"


def test_query_latest_n(seeded_client):
    """Test 5: Latest-N question."""
    response = seeded_client.post("/api/query", json={"question": "Show the latest 2 incidents."})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["interpreted_filters"]["limit"] == 2
    assert len(data["incidents"]) == 2


def test_query_count(seeded_client):
    """Test 6: Count question."""
    response = seeded_client.post("/api/query", json={"question": "How many incidents were detected?"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "4" in data["answer"]


def test_query_empty_question(seeded_client):
    """Test 7: Empty question."""
    response = seeded_client.post("/api/query", json={"question": ""})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "unsupported_query"
    assert "empty" in data["answer"].lower()
    assert data["incidents"] == []


def test_query_whitespace_only_question(seeded_client):
    """Test 8: Whitespace-only question."""
    response = seeded_client.post("/api/query", json={"question": "    \t\n  "})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "unsupported_query"
    assert "empty" in data["answer"].lower()
    assert data["incidents"] == []


def test_query_unsupported_question(seeded_client):
    """Test 9: Unsupported question."""
    response = seeded_client.post("/api/query", json={"question": "What is the weather in Tokyo?"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "unsupported_query"
    assert "unsupported" in data["answer"].lower()
    assert data["incidents"] == []


def test_query_invalid_category(seeded_client):
    """Test 10: Invalid category."""
    response = seeded_client.post("/api/query", json={"question": "Show fire incidents."})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "unsupported_query"
    assert "fire" in data["answer"].lower()
    assert "not recognized" in data["answer"].lower()
    assert data["incidents"] == []


def test_query_invalid_date(seeded_client):
    """Test 11: Invalid date."""
    response = seeded_client.post("/api/query", json={"question": "Show incidents from 2026-02-31"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "unsupported_query"
    assert "invalid date" in data["answer"].lower()
    assert data["incidents"] == []


def test_query_valid_question_zero_matches(seeded_client):
    """Test 12: Valid question returning zero matches."""
    response = seeded_client.post("/api/query", json={"question": "Show crowd incident events."})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["interpreted_filters"]["category"] == "crowd_incident"
    assert data["incidents"] == []
    assert "0 matching incidents" in data["answer"]


def test_query_sql_injection_treated_as_data(seeded_client):
    """Test 13: SQL-injection-style question treated strictly as input data."""
    injection = "Show incidents from CAM_01'; DROP TABLE incidents; --"
    response = seeded_client.post("/api/query", json={"question": injection})
    assert response.status_code == 200

    # Ensure table was NOT dropped and still functions
    verify_res = seeded_client.get("/api/incidents")
    assert verify_res.status_code == 200
    assert verify_res.json()["total"] == 4


def test_query_count_with_truncated_list(seeded_client):
    """Verify count query answer represents total matching rows (4) even when incidents list is truncated."""
    # seeded_client has 4 total incidents across CAM_01 and CAM_02
    response = seeded_client.post(
        "/api/query",
        json={"question": "How many total incidents occurred? Show latest 2"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    # Total count in database is 4
    assert "4" in data["answer"]
    # Returned items is truncated to limit=2
    assert len(data["incidents"]) == 2


def test_query_inverted_date_range_rejected(seeded_client):
    """Verify inverted date range returns unsupported_query with clarification."""
    response = seeded_client.post(
        "/api/query",
        json={"question": "Show incidents between 2026-10-25 and 2026-10-15"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "unsupported_query"
    assert "cannot be later than" in data["answer"].lower()
    assert data["incidents"] == []
