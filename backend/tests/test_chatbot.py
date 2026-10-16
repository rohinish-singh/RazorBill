from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

try:
    from backend.src.main import app
    from backend.src.chatbot import (
        normalize_camera_ids,
        parse_temporal_filters,
        extract_category_regex,
        extract_category_and_negation,
        process_incident_query,
        QueryRequest,
    )
    from backend.src.database import init_db, seed_default_incidents, query_incidents
except ModuleNotFoundError:
    from src.main import app
    from src.chatbot import (
        normalize_camera_ids,
        parse_temporal_filters,
        extract_category_regex,
        extract_category_and_negation,
        process_incident_query,
        QueryRequest,
    )
    from src.database import init_db, seed_default_incidents, query_incidents


@pytest.fixture(autouse=True)
def setup_database(tmp_path, monkeypatch):
    test_db = tmp_path / "test_razorbill.db"
    monkeypatch.setenv("RAZORBILL_DB_PATH", str(test_db))
    init_db(test_db)
    seed_default_incidents(test_db)
    return test_db


def test_camera_id_normalization():
    assert normalize_camera_ids("Show tailgating on camera 2") == ["CAM_02"]
    assert normalize_camera_ids("Alert from cam 2") == ["CAM_02"]
    assert normalize_camera_ids("Incident on CAM-02") == ["CAM_02"]
    assert normalize_camera_ids("Check camera two please") == ["CAM_02"]
    assert normalize_camera_ids("Review cameras 1 and 2") == ["CAM_01", "CAM_02"]
    assert normalize_camera_ids("No camera mentioned here") == []


def test_category_regex_extraction():
    assert extract_category_regex("Show all tailgating events") == "tailgating"
    assert extract_category_regex("Any person down detected?") == "person_down"
    assert extract_category_regex("Was there any fighting?") == "fighting"
    assert extract_category_regex("Check for suspicious activity") == "suspicious_activity"
    assert extract_category_regex("Clear the gate") is None


def test_temporal_filter_parsing():
    fixed_now = datetime(2026, 10, 16, 14, 0, 0, tzinfo=timezone.utc)
    start, end = parse_temporal_filters("Show events from today", now=fixed_now)
    assert start == datetime(2026, 10, 16, 0, 0, 0, tzinfo=timezone.utc)
    assert end is None

    start_hrs, end_hrs = parse_temporal_filters("Alerts in the last 3 hours", now=fixed_now)
    assert start_hrs == datetime(2026, 10, 16, 11, 0, 0, tzinfo=timezone.utc)
    assert end_hrs == fixed_now


def test_prompt_injection_sanitization():
    # ASCII control characters stripped and spaces normalized
    clean = QueryRequest(question="Check camera 1 \x00\x08alert")
    assert "\x00" not in clean.question
    assert clean.question == "Check camera 1 alert"

    with pytest.raises(Exception):
        QueryRequest(question="   ")


def test_database_parameterized_query(setup_database):
    db_path = setup_database
    results = query_incidents(camera_id="CAM_02", category="tailgating", db_path=db_path)
    assert len(results) == 2
    for r in results:
        assert r.camera_id == "CAM_02"
        assert r.category.value == "tailgating"


@pytest.mark.anyio
async def test_end_to_end_query_processing(setup_database):
    # Test query with camera + category
    resp = await process_incident_query("Show all tailgating events from camera 2 today")
    assert resp.interpreted_filters.get("camera_id") == "CAM_02"
    assert resp.interpreted_filters.get("category") == "tailgating"
    assert len(resp.incidents) >= 1
    assert "tailgating" in resp.answer.lower()
    assert "cam_02" in resp.answer.lower()


@pytest.mark.anyio
async def test_zero_match_query(setup_database):
    resp = await process_incident_query("Show crowd incidents on CAM_05")
    assert resp.interpreted_filters.get("camera_id") == "CAM_05"
    assert resp.interpreted_filters.get("category") == "crowd_incident"
    assert len(resp.incidents) == 0
    assert "no crowd incident events detected" in resp.answer.lower()


def test_api_endpoint_integration(setup_database):
    client = TestClient(app)

    # 1. Camera + Category query
    res = client.post("/api/query", json={"question": "Show all tailgating events from camera 2 today"})
    assert res.status_code == 200
    data = res.json()
    assert data["interpreted_filters"]["camera_id"] == "CAM_02"
    assert data["interpreted_filters"]["category"] == "tailgating"
    assert len(data["incidents"]) == 2
    assert "Found 2 tailgating events on CAM_02" in data["answer"]

    # 2. Short informal query
    res = client.post("/api/query", json={"question": "cam 1 person down"})
    assert res.status_code == 200
    data = res.json()
    assert data["interpreted_filters"]["camera_id"] == "CAM_01"
    assert data["interpreted_filters"]["category"] == "person_down"
    assert len(data["incidents"]) == 1

    # 3. Relative time query
    res = client.post("/api/query", json={"question": "Any fighting alerts in the last 3 hours?"})
    assert res.status_code == 200
    data = res.json()
    assert data["interpreted_filters"]["category"] == "fighting"

    # 4. Zero match query
    res = client.post("/api/query", json={"question": "Show crowd incidents on CAM_05"})
    assert res.status_code == 200
    data = res.json()
    assert data["interpreted_filters"]["camera_id"] == "CAM_05"
    assert data["interpreted_filters"]["category"] == "crowd_incident"
    assert len(data["incidents"]) == 0
    assert "No crowd incident events detected" in data["answer"]


def test_category_synonym_resolution():
    # person_down jargon
    assert extract_category_regex("someone collapsed near lobby") == "person_down"
    assert extract_category_regex("worker has fallen on floor") == "person_down"
    assert extract_category_regex("security report: fainted in corridor") == "person_down"
    assert extract_category_regex("individual is unconscious") == "person_down"
    assert extract_category_regex("medical emergency near entrance") == "person_down"
    assert extract_category_regex("person lying on floor") == "person_down"

    # fighting jargon
    assert extract_category_regex("violent brawl reported") == "fighting"
    assert extract_category_regex("physical altercation in hallway") == "fighting"
    assert extract_category_regex("punching observed on camera") == "fighting"
    assert extract_category_regex("assault in parking lot") == "fighting"
    assert extract_category_regex("scuffle near turnstiles") == "fighting"
    assert extract_category_regex("physical violence detected") == "fighting"

    # tailgating jargon
    assert extract_category_regex("piggybacking at entrance turnstiles") == "tailgating"
    assert extract_category_regex("unauthorized entry without badge") == "tailgating"
    assert extract_category_regex("followed through turnstile") == "tailgating"
    assert extract_category_regex("gate jumping detected") == "tailgating"

    # suspicious_activity jargon
    assert extract_category_regex("individual loitering near back door") == "suspicious_activity"
    assert extract_category_regex("trespassing on restricted grounds") == "suspicious_activity"
    assert extract_category_regex("prowling around vehicle lot") == "suspicious_activity"
    assert extract_category_regex("tampering with electric panel") == "suspicious_activity"

    # crowd_incident jargon
    assert extract_category_regex("large gathering forming at gate") == "crowd_incident"
    assert extract_category_regex("panic stampede in lobby") == "crowd_incident"
    assert extract_category_regex("angry mob gathering") == "crowd_incident"
    assert extract_category_regex("severe congestion near escalator") == "crowd_incident"


def test_negation_and_exclusion_logic():
    # "not fighting" -> positive=None, exclude="fighting"
    pos, exc = extract_category_and_negation("incidents on CAM_01 that are not fighting")
    assert pos is None
    assert exc == "fighting"

    # "except tailgating"
    pos, exc = extract_category_and_negation("show all cameras except tailgating")
    assert pos is None
    assert exc == "tailgating"

    # "excluding person down"
    pos, exc = extract_category_and_negation("review events excluding person down")
    assert pos is None
    assert exc == "person_down"

    # "other than suspicious activity"
    pos, exc = extract_category_and_negation("find anything other than suspicious activity")
    assert pos is None
    assert exc == "suspicious_activity"

    # Positive category without negation
    pos, exc = extract_category_and_negation("check CAM_01 for fighting")
    assert pos == "fighting"
    assert exc is None


def test_extended_temporal_intervals():
    fixed_now = datetime(2026, 10, 16, 15, 30, 0, tzinfo=timezone.utc)

    # Minute granularity
    start, end = parse_temporal_filters("any alerts in the last 15 minutes", now=fixed_now)
    assert start == datetime(2026, 10, 16, 15, 15, 0, tzinfo=timezone.utc)
    assert end == fixed_now

    start_45, end_45 = parse_temporal_filters("past 45 mins", now=fixed_now)
    assert start_45 == datetime(2026, 10, 16, 14, 45, 0, tzinfo=timezone.utc)
    assert end_45 == fixed_now

    # Multi-day lookback
    start_days, end_days = parse_temporal_filters("events in the past 2 days", now=fixed_now)
    assert start_days == datetime(2026, 10, 14, 15, 30, 0, tzinfo=timezone.utc)
    assert end_days == fixed_now

    # Calendar "this week" (2026-10-16 is Friday; Monday was 2026-10-12)
    start_week, end_week = parse_temporal_filters("alerts from this week", now=fixed_now)
    assert start_week == datetime(2026, 10, 12, 0, 0, 0, tzinfo=timezone.utc)
    assert end_week == fixed_now

    # Calendar "yesterday" (2026-10-15 full 24h)
    start_yest, end_yest = parse_temporal_filters("anything from yesterday", now=fixed_now)
    assert start_yest == datetime(2026, 10, 15, 0, 0, 0, tzinfo=timezone.utc)
    assert end_yest.day == 15
    assert end_yest.hour == 23 and end_yest.minute == 59


def test_ordering_and_pagination(setup_database):
    db_path = setup_database
    all_results = query_incidents(db_path=db_path)
    assert len(all_results) == 5

    # Check ordering is created_at DESC
    timestamps = [r.created_at for r in all_results]
    assert timestamps == sorted(timestamps, reverse=True)

    # Pagination: limit=2
    page1 = query_incidents(limit=2, offset=0, db_path=db_path)
    assert len(page1) == 2

    # Pagination: offset=2
    page2 = query_incidents(limit=2, offset=2, db_path=db_path)
    assert len(page2) == 2
    assert page1[0].event_id != page2[0].event_id

    # Limit clamping in database layer
    clamped_large = query_incidents(limit=500, db_path=db_path)
    assert len(clamped_large) == 5  # Total rows is 5, query didn't crash


def test_sql_injection_resistance(setup_database):
    db_path = setup_database
    # Attempt SQL injection via camera_id and category
    nasty_camera = "CAM_01' OR '1'='1"
    res = query_incidents(camera_id=nasty_camera, db_path=db_path)
    assert len(res) == 0

    nasty_cat = "tailgating'; DROP TABLE incidents; --"
    res2 = query_incidents(category=nasty_cat, db_path=db_path)
    assert len(res2) == 0

    # Ensure table is still intact and queryable
    res_intact = query_incidents(db_path=db_path)
    assert len(res_intact) == 5


def test_api_endpoint_advanced_queries(setup_database):
    client = TestClient(app)

    # 1. Synonym query: "someone collapsed near lobby"
    res1 = client.post("/api/query", json={"question": "someone collapsed near lobby"})
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["interpreted_filters"]["category"] == "person_down"
    assert len(data1["incidents"]) == 1
    assert data1["incidents"][0]["category"] == "person_down"

    # 2. Negation query: "incidents on CAM_01 that are not fighting"
    res2 = client.post("/api/query", json={"question": "incidents on CAM_01 that are not fighting"})
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["interpreted_filters"]["camera_id"] == "CAM_01"
    assert data2["interpreted_filters"].get("exclude_category") == "fighting"
    assert data2["interpreted_filters"].get("category") is None
    # CAM_01 has person_down and suspicious_activity (neither is fighting)
    assert len(data2["incidents"]) == 2
    for inc in data2["incidents"]:
        assert inc["camera_id"] == "CAM_01"
        assert inc["category"] != "fighting"

    # 3. Minute-level lookback query
    res3 = client.post("/api/query", json={"question": "any alerts in the last 15 minutes"})
    assert res3.status_code == 200
    data3 = res3.json()
    assert "start_time" in data3["interpreted_filters"]
    assert "end_time" in data3["interpreted_filters"]

    # 4. Pagination via API: limit and offset
    res4 = client.post("/api/query", json={"question": "show all incidents", "limit": 2, "offset": 0})
    assert res4.status_code == 200
    data4 = res4.json()
    assert len(data4["incidents"]) == 2

