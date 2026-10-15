from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient

try:
    from backend.src.database import get_stats, init_db, upsert_incident
    from backend.src.main import app, get_db_path
    from backend.src.schemas import Category, ClassifiedIncident, Source, Status
except ModuleNotFoundError:
    from src.database import get_stats, init_db, upsert_incident
    from src.main import app, get_db_path
    from src.schemas import Category, ClassifiedIncident, Source, Status


@pytest.fixture
def test_db_path(tmp_path):
    db_file = str(tmp_path / "test_stats_razorbill.db")
    init_db(db_file)
    return db_file


@pytest.fixture
def client(test_db_path):
    app.dependency_overrides[get_db_path] = lambda: test_db_path
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _make_incident(
    event_id: str = "evt_1",
    camera_id: str = "CAM_01",
    category: Category = Category.person_down,
    status: Status = Status.classified,
    created_at: str = "2026-10-15T12:00:00Z",
) -> ClassifiedIncident:
    return ClassifiedIncident(
        event_id=event_id,
        camera_id=camera_id,
        timestamp_seconds=10.0,
        category=category,
        summary=f"Incident summary for {event_id}",
        confidence=0.85,
        frame_path=f"data/frames/{camera_id}/{event_id}.jpg",
        source=Source.vlm,
        status=status,
        created_at=created_at,
    )


def test_stats_empty_database(client, test_db_path):
    """Test statistics on a completely empty database."""
    # Via direct DB helper
    stats = get_stats(db_path=test_db_path)
    assert stats.total == 0
    assert stats.recent_activity_count == 0
    assert stats.by_camera == {}

    # Ensure all canonical categories are present with count 0
    for cat in Category:
        assert cat.value in stats.by_category
        assert stats.by_category[cat.value] == 0

    # Ensure all canonical statuses are present with count 0
    for st in Status:
        assert st.value in stats.by_status
        assert stats.by_status[st.value] == 0

    # Via API endpoint
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["recent_activity_count"] == 0
    assert data["by_camera"] == {}


def test_stats_correct_total_count(client, test_db_path):
    """Test that total count reflects exact number of persisted records."""
    upsert_incident(_make_incident("evt_1", category=Category.fighting), db_path=test_db_path)
    upsert_incident(_make_incident("evt_2", category=Category.tailgating), db_path=test_db_path)
    upsert_incident(_make_incident("evt_3", category=Category.person_down), db_path=test_db_path)

    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3


def test_stats_counts_by_category(client, test_db_path):
    """Test that counts by canonical category are grouped correctly."""
    upsert_incident(_make_incident("evt_1", category=Category.person_down), db_path=test_db_path)
    upsert_incident(_make_incident("evt_2", category=Category.person_down), db_path=test_db_path)
    upsert_incident(_make_incident("evt_3", category=Category.fighting), db_path=test_db_path)
    upsert_incident(_make_incident("evt_4", category=Category.tailgating), db_path=test_db_path)

    response = client.get("/api/stats")
    assert response.status_code == 200
    by_cat = response.json()["by_category"]

    assert by_cat["person_down"] == 2
    assert by_cat["fighting"] == 1
    assert by_cat["tailgating"] == 1
    assert by_cat["crowd_incident"] == 0
    assert by_cat["suspicious_activity"] == 0
    assert by_cat["other"] == 0
    assert by_cat["unknown"] == 0


def test_stats_counts_by_status(client, test_db_path):
    """Test that counts by canonical status are grouped correctly."""
    upsert_incident(_make_incident("evt_1", status=Status.classified), db_path=test_db_path)
    upsert_incident(_make_incident("evt_2", status=Status.classified), db_path=test_db_path)
    upsert_incident(_make_incident("evt_3", status=Status.candidate), db_path=test_db_path)
    upsert_incident(_make_incident("evt_4", status=Status.needs_review), db_path=test_db_path)

    response = client.get("/api/stats")
    assert response.status_code == 200
    by_status = response.json()["by_status"]

    assert by_status["classified"] == 2
    assert by_status["candidate"] == 1
    assert by_status["needs_review"] == 1
    assert by_status["failed"] == 0


def test_stats_counts_by_camera(client, test_db_path):
    """Test that counts by camera ID are grouped correctly."""
    upsert_incident(_make_incident("evt_1", camera_id="CAM_NORTH"), db_path=test_db_path)
    upsert_incident(_make_incident("evt_2", camera_id="CAM_NORTH"), db_path=test_db_path)
    upsert_incident(_make_incident("evt_3", camera_id="CAM_SOUTH"), db_path=test_db_path)

    response = client.get("/api/stats")
    assert response.status_code == 200
    by_cam = response.json()["by_camera"]

    assert by_cam == {
        "CAM_NORTH": 2,
        "CAM_SOUTH": 1,
    }


def test_stats_recent_activity_count_window(client, test_db_path):
    """Test recent activity count with fixed 24h window."""
    now = datetime.now(timezone.utc)
    t_1h_ago = (now - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    t_12h_ago = (now - timedelta(hours=12)).strftime("%Y-%m-%dT%H:%M:%SZ")
    t_36h_ago = (now - timedelta(hours=36)).strftime("%Y-%m-%dT%H:%M:%SZ")

    upsert_incident(_make_incident("evt_recent_1", created_at=t_1h_ago), db_path=test_db_path)
    upsert_incident(_make_incident("evt_recent_2", created_at=t_12h_ago), db_path=test_db_path)
    upsert_incident(_make_incident("evt_old", created_at=t_36h_ago), db_path=test_db_path)

    # Fixed 24h window -> should include evt_recent_1 and evt_recent_2, but not evt_old
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert data["recent_activity_count"] == 2

    # Direct database test with fixed reference time
    ref_time = datetime(2026, 10, 15, 12, 0, 0, tzinfo=timezone.utc)
    upsert_incident(_make_incident("evt_ref_1", created_at="2026-10-15T11:30:00Z"), db_path=test_db_path)
    upsert_incident(_make_incident("evt_ref_2", created_at="2026-10-14T08:00:00Z"), db_path=test_db_path)

    stats_ref = get_stats(db_path=test_db_path, reference_time=ref_time)
    # Within 24h of 2026-10-15T12:00:00Z (cutoff 2026-10-14T12:00:00Z):
    # evt_ref_1 (10-15T11:30:00Z) is in. evt_ref_2 (10-14T08:00:00Z) is before cutoff.
    # Current wall-clock items from earlier in test are also >= cutoff
    assert stats_ref.recent_activity_count >= 1


def test_stats_insert_and_update_behavior(client, test_db_path):
    """Test that updating an incident updates category/status counts without increasing total."""
    inc = _make_incident("evt_shift", category=Category.tailgating, status=Status.candidate)
    upsert_incident(inc, db_path=test_db_path)

    res1 = client.get("/api/stats").json()
    assert res1["total"] == 1
    assert res1["by_category"]["tailgating"] == 1
    assert res1["by_category"]["fighting"] == 0
    assert res1["by_status"]["candidate"] == 1
    assert res1["by_status"]["classified"] == 0

    # Update the same incident to fighting and classified
    inc_updated = _make_incident("evt_shift", category=Category.fighting, status=Status.classified)
    upsert_incident(inc_updated, db_path=test_db_path)

    res2 = client.get("/api/stats").json()
    assert res2["total"] == 1
    assert res2["by_category"]["tailgating"] == 0
    assert res2["by_category"]["fighting"] == 1
    assert res2["by_status"]["candidate"] == 0
    assert res2["by_status"]["classified"] == 1


def test_stats_upsert_no_double_counting(client):
    """Ensure duplicate event_id upserts via API endpoint do not double-count."""
    payload = {
        "event_id": "evt_dup",
        "camera_id": "CAM_01",
        "timestamp_seconds": 12.5,
        "category": "person_down",
        "summary": "First post",
        "confidence": 0.8,
        "frame_path": "data/frames/CAM_01/evt_dup.jpg",
        "source": "vlm",
        "status": "classified",
        "created_at": "2026-10-15T10:00:00Z",
    }
    # Post first time
    post1 = client.post("/api/incidents", json=payload)
    assert post1.status_code == 200

    # Post second time with modified summary
    payload["summary"] = "Second post update"
    post2 = client.post("/api/incidents", json=payload)
    assert post2.status_code == 200

    stats = client.get("/api/stats").json()
    assert stats["total"] == 1
    assert stats["by_camera"] == {"CAM_01": 1}
    assert stats["by_category"]["person_down"] == 1


def test_stats_missing_categories_and_statuses_consistent(client, test_db_path):
    """Verify that every single canonical Category and Status enum member exists in the output."""
    upsert_incident(_make_incident("evt_single", category=Category.other, status=Status.failed), db_path=test_db_path)

    data = client.get("/api/stats").json()

    # All canonical categories present
    for cat in Category:
        assert cat.value in data["by_category"]
        expected = 1 if cat == Category.other else 0
        assert data["by_category"][cat.value] == expected

    # All canonical statuses present
    for st in Status:
        assert st.value in data["by_status"]
        expected = 1 if st == Status.failed else 0
        assert data["by_status"][st.value] == expected
