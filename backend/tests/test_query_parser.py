from datetime import datetime, timezone
import pytest

try:
    from backend.src.query_parser import parse_query
    from backend.src.schemas import Category
except ModuleNotFoundError:
    from src.query_parser import parse_query
    from src.schemas import Category


def test_parse_valid_category_question():
    res = parse_query("Show fighting incidents.")
    assert res.is_supported is True
    assert res.category == Category.fighting
    assert res.interpreted_filters.get("category") == "fighting"

    res_pd = parse_query("Any person down events?")
    assert res_pd.is_supported is True
    assert res_pd.category == Category.person_down


def test_parse_valid_camera_question():
    res1 = parse_query("Show incidents from CAM_01.")
    assert res1.is_supported is True
    assert res1.camera_id == "CAM_01"
    assert res1.interpreted_filters.get("camera_id") == "CAM_01"

    # "camera 2" should map to "CAM_02" per contract
    res2 = parse_query("What happened on camera 2?")
    assert res2.is_supported is True
    assert res2.camera_id == "CAM_02"


def test_parse_combined_category_and_camera_question():
    res = parse_query("Show all tailgating events from camera 2 today")
    assert res.is_supported is True
    assert res.category == Category.tailgating
    assert res.camera_id == "CAM_02"
    assert res.start is not None
    assert res.end is not None


def test_parse_date_based_question():
    fixed_now = datetime(2026, 10, 15, 14, 0, 0, tzinfo=timezone.utc)
    res_today = parse_query("Show incidents from today", reference_time=fixed_now)
    assert res_today.is_supported is True
    assert res_today.start == "2026-10-15T00:00:00Z"
    assert res_today.end == "2026-10-15T23:59:59.999999Z"

    res_explicit = parse_query("Show incidents from 2026-10-14")
    assert res_explicit.is_supported is True
    assert res_explicit.start == "2026-10-14T00:00:00Z"
    assert res_explicit.end == "2026-10-14T23:59:59.999999Z"


def test_parse_latest_n_question():
    res = parse_query("Show the latest 10 incidents.")
    assert res.is_supported is True
    assert res.limit == 10
    assert res.interpreted_filters.get("limit") == 10

    res_last = parse_query("Show last 5 events")
    assert res_last.is_supported is True
    assert res_last.limit == 5


def test_parse_count_question():
    res = parse_query("How many incidents were detected?")
    assert res.is_supported is True
    assert res.is_count is True

    res2 = parse_query("Count fighting events on CAM_01")
    assert res2.is_supported is True
    assert res2.is_count is True
    assert res2.category == Category.fighting
    assert res2.camera_id == "CAM_01"


def test_parse_empty_and_whitespace_question():
    res_empty = parse_query("")
    assert res_empty.is_supported is False
    assert "empty" in res_empty.error_message.lower()

    res_ws = parse_query("   \n\t   ")
    assert res_ws.is_supported is False
    assert "empty" in res_ws.error_message.lower()


def test_parse_unsupported_question():
    res = parse_query("What is the capital of France?")
    assert res.is_supported is False
    assert "unsupported" in res.error_message.lower()


def test_parse_invalid_category_question():
    res = parse_query("Show fire incidents.")
    assert res.is_supported is False
    assert "not recognized" in res.error_message.lower()


def test_parse_invalid_date_question():
    res = parse_query("Show incidents from 2026-02-31")
    assert res.is_supported is False
    assert "invalid date" in res.error_message.lower()


def test_parse_ambiguous_question():
    res = parse_query("Show fighting and person down incidents")
    assert res.is_supported is False
    assert "ambiguous" in res.error_message.lower()


def test_parse_camera_stopwords_and_named_cameras():
    # Stop words like "camera feed", "cameras", "campus" should not become camera IDs
    res_feed = parse_query("Show camera feed")
    assert res_feed.camera_id is None

    res_campus = parse_query("Show campus incidents")
    assert res_campus.camera_id is None

    res_active = parse_query("How many cameras were active?")
    assert res_active.camera_id is None

    # Named cameras like "camera north", "camera CAM_A", "CAM-02", "CAM1"
    res_north = parse_query("Show incidents from camera north")
    assert res_north.camera_id == "CAM_NORTH"

    res_cam_a = parse_query("Show incidents from camera CAM_A")
    assert res_cam_a.camera_id == "CAM_A"

    res_hyphen = parse_query("Show incidents from CAM-02")
    assert res_hyphen.camera_id == "CAM_02"

    res_digits = parse_query("Show incidents from CAM1")
    assert res_digits.camera_id == "CAM_01"


def test_parse_inverted_date_range():
    res = parse_query("Show incidents between 2026-10-20 and 2026-10-10")
    assert res.is_supported is False
    assert "cannot be later than" in res.error_message.lower()
