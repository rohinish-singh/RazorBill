from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

try:
    from backend.src.main import app
    from backend.src.chatbot import (
        normalize_camera_ids,
        parse_temporal_filters,
        extract_category_and_negation,
        generate_grounded_answer,
        process_incident_query,
        QueryRequest,
        InterpretedFilters,
    )
    from backend.src.database import init_db, seed_default_incidents, query_incidents
    from backend.src.schemas import ClassifiedIncident, Category, Status, Source
except ModuleNotFoundError:
    from src.main import app
    from src.chatbot import (
        normalize_camera_ids,
        parse_temporal_filters,
        extract_category_and_negation,
        generate_grounded_answer,
        process_incident_query,
        QueryRequest,
        InterpretedFilters,
    )
    from src.database import init_db, seed_default_incidents, query_incidents
    from src.schemas import ClassifiedIncident, Category, Status, Source


@pytest.fixture(autouse=True)
def setup_database(tmp_path, monkeypatch):
    test_db = tmp_path / "test_adversarial.db"
    monkeypatch.setenv("RAZORBILL_DB_PATH", str(test_db))
    init_db(test_db)
    seed_default_incidents(test_db)
    return test_db


# --- CATEGORY 1: Complex & Ambiguous Camera Phrasing ---

def test_camera_range_expansion():
    # "cameras 1 to 3" should expand to CAM_01, CAM_02, CAM_03
    assert normalize_camera_ids("check cameras 1 to 3") == ["CAM_01", "CAM_02", "CAM_03"]
    assert normalize_camera_ids("cameras 1 through 4") == ["CAM_01", "CAM_02", "CAM_03", "CAM_04"]
    assert normalize_camera_ids("cams 2-4") == ["CAM_02", "CAM_03", "CAM_04"]


def test_camera_zero_padding_and_leading_zeros():
    assert normalize_camera_ids("CAM01") == ["CAM_01"]
    assert normalize_camera_ids("cam002") == ["CAM_02"]
    assert normalize_camera_ids("cam_003") == ["CAM_03"]
    assert normalize_camera_ids("CAM_1") == ["CAM_01"]


def test_camera_generic_ambiguous_mentions():
    # Generic camera terms must NOT produce false IDs like CAM_00
    assert normalize_camera_ids("incident in the camera room") == []
    assert normalize_camera_ids("captured on security camera") == []
    assert normalize_camera_ids("action happened on-camera") == []
    assert normalize_camera_ids("camera 0") == []
    assert normalize_camera_ids("CAM_00") == []


# --- CATEGORY 2: Temporal Edge Cases & Boundary Conditions ---

def test_future_timestamps():
    fixed_now = datetime(2026, 10, 16, 14, 0, 0, tzinfo=timezone.utc)
    # Queries about tomorrow or next hour must not query into the future or create inverted bounds
    start, end = parse_temporal_filters("alerts tomorrow", now=fixed_now)
    assert start is None
    assert end is None

    start_nxt, end_nxt = parse_temporal_filters("events in the next hour", now=fixed_now)
    assert start_nxt is None
    assert end_nxt is None


def test_explicit_dates():
    # Explicit ISO / calendar dates: "incidents on 2026-10-15"
    start, end = parse_temporal_filters("incidents on 2026-10-15")
    assert start is not None
    assert end is not None
    assert start == datetime(2026, 10, 15, 0, 0, 0, tzinfo=timezone.utc)
    assert end == datetime(2026, 10, 15, 23, 59, 59, 999999, tzinfo=timezone.utc)

    # Date range: "from 2026-10-13 to 2026-10-15"
    start_r, end_r = parse_temporal_filters("events from 2026-10-13 to 2026-10-15")
    assert start_r == datetime(2026, 10, 13, 0, 0, 0, tzinfo=timezone.utc)
    assert end_r == datetime(2026, 10, 15, 23, 59, 59, 999999, tzinfo=timezone.utc)


def test_conflicting_temporal_windows():
    fixed_now = datetime(2026, 10, 16, 14, 0, 0, tzinfo=timezone.utc)
    start, end = parse_temporal_filters("yesterday in the last 15 minutes", now=fixed_now)
    # Bounds must never be inverted
    if start and end:
        assert start <= end
        assert end <= fixed_now


# --- CATEGORY 3: Case Sensitivity & Punctuation in Categories ---

def test_hyphenated_and_case_categories():
    assert extract_category_and_negation("Person-Down reported") == ("person_down", None)
    assert extract_category_and_negation("TAILGATING incident") == ("tailgating", None)
    assert extract_category_and_negation("Check crowd-incident") == ("crowd_incident", None)
    assert extract_category_and_negation("Suspicious Activity on CAM_01") == ("suspicious_activity", None)
    assert extract_category_and_negation("Is this 'fighting'?") == ("fighting", None)
    assert extract_category_and_negation("(tailgating) alert!") == ("tailgating", None)


# --- CATEGORY 4: Grounded Summary Grammar ---

def test_summary_grammar_singular_plural_and_exclusion():
    # 1 incident singular
    inc_1 = [
        ClassifiedIncident(
            event_id="e1",
            camera_id="CAM_01",
            timestamp_seconds=10.0,
            category=Category.person_down,
            summary="test",
            confidence=0.9,
            confidence_type="vlm_calibrated",
            frame_path="path",
            source=Source.vlm,
            processing_ms=100,
            status=Status.classified,
            evidence_notes="note",
            created_at="2026-10-16T14:00:00Z",
        )
    ]
    f1 = InterpretedFilters(camera_id="CAM_01", category="person_down")
    ans1 = generate_grounded_answer("q", f1, inc_1)
    assert ans1 == "Found 1 person down event on CAM_01."

    # 0 incidents plural
    f0 = InterpretedFilters(camera_id="CAM_01", category="person_down")
    ans0 = generate_grounded_answer("q", f0, [])
    assert ans0 == "No person down events detected on CAM_01."

    # Exclusion grammar (0 incidents)
    f_exc0 = InterpretedFilters(camera_id="CAM_01", exclude_category="fighting")
    ans_exc0 = generate_grounded_answer("q", f_exc0, [])
    assert ans_exc0 == "No events (excluding fighting) detected on CAM_01."

    # Exclusion grammar (2 incidents)
    ans_exc2 = generate_grounded_answer("q", f_exc0, inc_1 + inc_1)
    assert ans_exc2 == "Found 2 events (excluding fighting) on CAM_01."


# --- CATEGORY 5: Extreme & Malformed Inputs ---

def test_extreme_inputs_and_pydantic_validation():
    client = TestClient(app)

    # 1. Over 500 characters must return 422
    long_question = "a" * 501
    res = client.post("/api/query", json={"question": long_question})
    assert res.status_code == 422

    # 2. String of solely zero-width spaces must fail validation
    zero_width = "\u200b\u200c\u200d\ufeff"
    res_zw = client.post("/api/query", json={"question": zero_width})
    assert res_zw.status_code == 422

    # 3. Unicode emojis and massive non-ASCII text within length bound
    emoji_q = "🚨⚠️🔥 Suspicious activity reported 📹👀 " + ("🚶‍♂️" * 30)
    res_emoji = client.post("/api/query", json={"question": emoji_q})
    assert res_emoji.status_code == 200
    assert res_emoji.json()["interpreted_filters"]["category"] == "suspicious_activity"

    # 4. SQL metacharacters: %, _, *, ?, ', "
    res_sql = client.post("/api/query", json={"question": "CAM_01 %_?*[]'\" tailgating"})
    assert res_sql.status_code == 200

    # 5. Exactly 500 chars (valid boundary)
    valid_500 = "alert " + ("x" * 494)
    res_500 = client.post("/api/query", json={"question": valid_500})
    assert res_500.status_code == 200


def test_database_inverted_bounds_safety(setup_database):
    db_path = setup_database
    t_early = datetime(2026, 10, 16, 10, 0, 0, tzinfo=timezone.utc)
    t_late = datetime(2026, 10, 16, 18, 0, 0, tzinfo=timezone.utc)

    # Inverted: start > end
    res = query_incidents(start_time=t_late, end_time=t_early, db_path=db_path)
    # Must safely swap start and end to return incidents
    assert len(res) == 5


def test_grammar_single_event_exclusion():
    inc_1 = [
        ClassifiedIncident(
            event_id="e1",
            camera_id="CAM_01",
            timestamp_seconds=10.0,
            category=Category.person_down,
            summary="test",
            confidence=0.9,
            confidence_type="vlm_calibrated",
            frame_path="path",
            source=Source.vlm,
            processing_ms=100,
            status=Status.classified,
            evidence_notes="note",
            created_at="2026-10-16T14:00:00Z",
        )
    ]
    f = InterpretedFilters(camera_id="CAM_01", exclude_category="fighting")
    ans = generate_grounded_answer("q", f, inc_1)
    assert ans == "Found 1 event (excluding fighting) on CAM_01."


@pytest.mark.anyio
async def test_end_to_end_adversarial_queries(setup_database):
    # 1. Camera range expansion E2E
    resp1 = await process_incident_query("Show alerts on cameras 1 to 2")
    assert resp1.interpreted_filters.get("camera_ids") == ["CAM_01", "CAM_02"]
    assert len(resp1.incidents) >= 2

    # 2. Hyphenated category E2E
    resp2 = await process_incident_query("Any Person-Down recorded on CAM_01?")
    assert resp2.interpreted_filters.get("camera_id") == "CAM_01"
    assert resp2.interpreted_filters.get("category") == "person_down"
    assert len(resp2.incidents) == 1
    assert "Found 1 person down event on CAM_01." in resp2.answer

    # 3. Future timestamp query E2E
    resp3 = await process_incident_query("Any incidents tomorrow?")
    assert resp3.interpreted_filters.get("start_time") is None
    assert resp3.interpreted_filters.get("end_time") is None

