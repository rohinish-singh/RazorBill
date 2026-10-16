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
def client(tmp_path):
    test_db = str(tmp_path / "test_list_razorbill.db")
    init_db(test_db)
    app.dependency_overrides[get_db_path] = lambda: test_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def seeded_client(client, tmp_path):
    # Seed 5 distinct incidents
    incidents = [
        ClassifiedIncident(
            event_id="evt_1",
            camera_id="CAM_A",
            timestamp_seconds=10.0,
            category=Category.person_down,
            summary="Worker down at station A",
            confidence=0.90,
            frame_path="data/frames/CAM_A/evt_1.jpg",
            source=Source.vlm,
            status=Status.classified,
            created_at="2026-10-15T10:00:00Z",
        ),
        ClassifiedIncident(
            event_id="evt_2",
            camera_id="CAM_A",
            timestamp_seconds=20.0,
            category=Category.fighting,
            summary="Altercation near dock",
            confidence=0.85,
            frame_path="data/frames/CAM_A/evt_2.jpg",
            source=Source.vlm,
            status=Status.classified,
            created_at="2026-10-15T10:05:00Z",
        ),
        ClassifiedIncident(
            event_id="evt_3",
            camera_id="CAM_B",
            timestamp_seconds=30.0,
            category=Category.tailgating,
            summary="Tailgating at entrance",
            confidence=0.92,
            frame_path="data/frames/CAM_B/evt_3.jpg",
            source=Source.vlm,
            status=Status.classified,
            created_at="2026-10-15T10:10:00Z",
        ),
        ClassifiedIncident(
            event_id="evt_4",
            camera_id="CAM_B",
            timestamp_seconds=40.0,
            category=Category.person_down,
            summary="Second person down at lobby",
            confidence=0.78,
            frame_path="data/frames/CAM_B/evt_4.jpg",
            source=Source.vlm,
            status=Status.classified,
            created_at="2026-10-15T10:15:00Z",
        ),
        ClassifiedIncident(
            event_id="evt_5",
            camera_id="CAM_C",
            timestamp_seconds=50.0,
            category=Category.suspicious_activity,
            summary="Loitering behind warehouse",
            confidence=0.88,
            frame_path="data/frames/CAM_C/evt_5.jpg",
            source=Source.vlm,
            status=Status.classified,
            created_at="2026-10-15T10:20:00Z",
        ),
    ]
    for inc in incidents:
        client.post("/api/incidents", json=inc.model_dump())
    return client


# 1. Listing an empty database
def test_list_empty_database(client):
    response = client.get("/api/incidents")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["limit"] == 50
    assert data["offset"] == 0


# 2. Listing multiple incidents
def test_list_multiple_incidents(seeded_client):
    response = seeded_client.get("/api/incidents")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["items"]) == 5


# 3. Filtering by camera_id
def test_filter_by_camera_id(seeded_client):
    response = seeded_client.get("/api/incidents?camera_id=CAM_A")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert all(item["camera_id"] == "CAM_A" for item in data["items"])


# 4. Filtering by category
def test_filter_by_category(seeded_client):
    response = seeded_client.get("/api/incidents?category=person_down")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert all(item["category"] == "person_down" for item in data["items"])


# 5. Applying start and end boundaries (ISO UTC timestamps and date-only)
def test_filter_by_start_and_end_boundaries_iso(seeded_client):
    response = seeded_client.get("/api/incidents?start=2026-10-15T10:05:00Z&end=2026-10-15T10:15:00Z")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    returned_ids = {item["event_id"] for item in data["items"]}
    assert returned_ids == {"evt_2", "evt_3", "evt_4"}


def test_filter_start_only_iso_datetime(seeded_client):
    response = seeded_client.get("/api/incidents?start=2026-10-15T10:10:00Z")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    returned_ids = {item["event_id"] for item in data["items"]}
    assert returned_ids == {"evt_3", "evt_4", "evt_5"}


def test_filter_end_only_iso_datetime(seeded_client):
    response = seeded_client.get("/api/incidents?end=2026-10-15T10:10:00Z")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    returned_ids = {item["event_id"] for item in data["items"]}
    assert returned_ids == {"evt_1", "evt_2", "evt_3"}


def test_filter_date_only_inclusive_behavior(seeded_client):
    # Date-only start=2026-10-15 & end=2026-10-15 covers 00:00:00Z to 23:59:59.999999Z
    response = seeded_client.get("/api/incidents?start=2026-10-15&end=2026-10-15")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5

    # Day with no incidents returns 0
    resp_future = seeded_client.get("/api/incidents?start=2026-10-16&end=2026-10-16")
    assert resp_future.status_code == 200
    assert resp_future.json()["total"] == 0


def test_filter_same_calendar_date_different_times(client):
    # Distinct times on 2026-10-15 and one on 2026-10-16
    records = [
        ClassifiedIncident(
            event_id="evt_day_early",
            camera_id="CAM_1",
            timestamp_seconds=1.0,
            category=Category.other,
            summary="Early morning",
            frame_path="p.jpg",
            source=Source.rule,
            status=Status.candidate,
            created_at="2026-10-15T08:00:00Z",
        ),
        ClassifiedIncident(
            event_id="evt_day_mid",
            camera_id="CAM_1",
            timestamp_seconds=2.0,
            category=Category.other,
            summary="Midday",
            frame_path="p.jpg",
            source=Source.rule,
            status=Status.candidate,
            created_at="2026-10-15T14:30:00Z",
        ),
        ClassifiedIncident(
            event_id="evt_day_late",
            camera_id="CAM_1",
            timestamp_seconds=3.0,
            category=Category.other,
            summary="Late evening",
            frame_path="p.jpg",
            source=Source.rule,
            status=Status.candidate,
            created_at="2026-10-15T22:15:00Z",
        ),
        ClassifiedIncident(
            event_id="evt_next_day",
            camera_id="CAM_1",
            timestamp_seconds=4.0,
            category=Category.other,
            summary="Next day",
            frame_path="p.jpg",
            source=Source.rule,
            status=Status.candidate,
            created_at="2026-10-16T01:00:00Z",
        ),
    ]
    for r in records:
        client.post("/api/incidents", json=r.model_dump())

    # Date-only query for 2026-10-15 must capture all 3 records on that day and exclude 2026-10-16
    resp = client.get("/api/incidents?start=2026-10-15&end=2026-10-15")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 3
    event_ids = {i["event_id"] for i in data["items"]}
    assert event_ids == {"evt_day_early", "evt_day_mid", "evt_day_late"}


def test_filter_invalid_datetime_rejected(seeded_client):
    # Non-date string
    assert seeded_client.get("/api/incidents?start=invalid-date").status_code == 422
    # Pure numeric value (not a date format)
    assert seeded_client.get("/api/incidents?start=10.0").status_code == 422
    # Invalid calendar day
    assert seeded_client.get("/api/incidents?end=2026-99-99").status_code == 422
    # Timezone-naive datetime
    assert seeded_client.get("/api/incidents?start=2026-10-15T10:00:00").status_code == 422
    # Non-UTC timezone offset
    assert seeded_client.get("/api/incidents?start=2026-10-15T10:00:00+05:30").status_code == 422


def test_filter_start_later_than_end_rejected(seeded_client):
    # ISO datetime start > end
    resp1 = seeded_client.get("/api/incidents?start=2026-10-15T12:00:00Z&end=2026-10-15T10:00:00Z")
    assert resp1.status_code == 400
    assert "cannot be later than" in resp1.json()["detail"].lower()

    # Date-only start > end
    resp2 = seeded_client.get("/api/incidents?start=2026-10-16&end=2026-10-15")
    assert resp2.status_code == 400
    assert "cannot be later than" in resp2.json()["detail"].lower()


# 6. Combining multiple filters
def test_combine_multiple_filters(seeded_client):
    response = seeded_client.get("/api/incidents?camera_id=CAM_B&category=person_down")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["event_id"] == "evt_4"


# 7. Correct total count when limit/offset are applied
def test_total_count_reflects_total_matches_with_limit(seeded_client):
    response = seeded_client.get("/api/incidents?limit=2&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["limit"] == 2
    assert data["offset"] == 0


# 8. First page and subsequent page
def test_pagination_pages(seeded_client):
    page1 = seeded_client.get("/api/incidents?limit=2&offset=0").json()
    page2 = seeded_client.get("/api/incidents?limit=2&offset=2").json()
    page3 = seeded_client.get("/api/incidents?limit=2&offset=4").json()

    assert len(page1["items"]) == 2
    assert len(page2["items"]) == 2
    assert len(page3["items"]) == 1

    ids_p1 = [i["event_id"] for i in page1["items"]]
    ids_p2 = [i["event_id"] for i in page2["items"]]
    ids_p3 = [i["event_id"] for i in page3["items"]]

    # Verify no overlaps across pages
    all_paged = ids_p1 + ids_p2 + ids_p3
    assert len(set(all_paged)) == 5


# 9. Stable ordering when timestamps are equal
def test_stable_ordering_when_timestamps_equal(client):
    ties = [
        ClassifiedIncident(
            event_id="evt_tie_B",
            camera_id="CAM_1",
            timestamp_seconds=10.0,
            category=Category.other,
            summary="Tie test B",
            frame_path="p.jpg",
            source=Source.rule,
            status=Status.candidate,
            created_at="2026-10-15T12:00:00Z",
        ),
        ClassifiedIncident(
            event_id="evt_tie_A",
            camera_id="CAM_1",
            timestamp_seconds=10.0,
            category=Category.other,
            summary="Tie test A",
            frame_path="p.jpg",
            source=Source.rule,
            status=Status.candidate,
            created_at="2026-10-15T12:00:00Z",
        ),
        ClassifiedIncident(
            event_id="evt_tie_C",
            camera_id="CAM_1",
            timestamp_seconds=10.0,
            category=Category.other,
            summary="Tie test C",
            frame_path="p.jpg",
            source=Source.rule,
            status=Status.candidate,
            created_at="2026-10-15T12:00:00Z",
        ),
    ]
    for inc in ties:
        client.post("/api/incidents", json=inc.model_dump())

    resp1 = client.get("/api/incidents").json()
    resp2 = client.get("/api/incidents").json()

    ids1 = [item["event_id"] for item in resp1["items"]]
    ids2 = [item["event_id"] for item in resp2["items"]]

    assert ids1 == ids2
    # Verify deterministic tie-breaker (alphabetical by event_id ascending when timestamps equal)
    assert ids1 == ["evt_tie_A", "evt_tie_B", "evt_tie_C"]


# 10. No results for a nonmatching filter
def test_no_results_for_nonmatching_filter(seeded_client):
    response = seeded_client.get("/api/incidents?camera_id=NONEXISTENT_CAM")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


# 11. Invalid category rejection
def test_invalid_category_rejected(seeded_client):
    response = seeded_client.get("/api/incidents?category=not_a_valid_category")
    assert response.status_code == 422


# 12. Invalid limit/offset rejection
def test_invalid_limit_and_offset_rejected(seeded_client):
    # limit < 1
    assert seeded_client.get("/api/incidents?limit=0").status_code == 422
    # limit > 100
    assert seeded_client.get("/api/incidents?limit=101").status_code == 422
    # offset < 0
    assert seeded_client.get("/api/incidents?offset=-1").status_code == 422


# 13. SQL injection-style input treated as data
def test_sql_injection_treated_as_data(seeded_client):
    injection_payload = "'; DROP TABLE incidents; --"
    response = seeded_client.get(f"/api/incidents?camera_id={injection_payload}")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0

    # Verify table was not dropped
    check_response = seeded_client.get("/api/incidents")
    assert check_response.status_code == 200
    assert check_response.json()["total"] == 5
