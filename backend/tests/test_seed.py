from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

try:
    from backend.src.database import (
        get_incident_by_id,
        init_db,
        list_incidents,
        upsert_incident,
    )
    from backend.src.main import app, get_db_path, get_frames_dir
    from backend.src.schemas import (
        Category,
        ClassifiedIncident,
        Source,
        Status,
    )
    from backend.src.seed import (
        build_synthetic_incidents,
        resolve_seed_frame_path,
        seed_demo_data,
    )
except ModuleNotFoundError:
    from src.database import (
        get_incident_by_id,
        init_db,
        list_incidents,
        upsert_incident,
    )
    from src.main import app, get_db_path, get_frames_dir
    from src.schemas import (
        Category,
        ClassifiedIncident,
        Source,
        Status,
    )
    from src.seed import (
        build_synthetic_incidents,
        resolve_seed_frame_path,
        seed_demo_data,
    )


@pytest.fixture
def temp_env(tmp_path):
    test_db = str(tmp_path / "test_demo_seed.db")
    frames_dir = str(tmp_path / "data" / "frames")
    app.dependency_overrides[get_db_path] = lambda: test_db
    app.dependency_overrides[get_frames_dir] = lambda: frames_dir
    yield test_db, frames_dir
    app.dependency_overrides.clear()


def test_build_synthetic_incidents_structure():
    fixed_time = datetime(2026, 10, 16, 12, 0, 0, tzinfo=timezone.utc)
    incidents = build_synthetic_incidents(reference_time=fixed_time, frames_dir="/nonexistent/dir")

    assert len(incidents) == 6
    for inc in incidents:
        # Schema and contract compliance
        assert isinstance(inc, ClassifiedIncident)
        assert inc.event_id.startswith("demo_synth_")
        assert isinstance(inc.category, Category)
        assert isinstance(inc.status, Status)
        assert inc.source == Source.manual

        # Integrity: no fabricated metrics or fake confidence
        assert inc.confidence is None
        assert inc.confidence_type == "unavailable"
        assert inc.processing_ms is None

        # Visible synthetic labeling
        assert "[SYNTHETIC DEMO]" in inc.summary
        assert "[SYNTHETIC DEMO]" in inc.evidence_notes
        assert "Not a real detection" in inc.evidence_notes or "Synthetic" in inc.evidence_notes

        # Frame path is empty string when no frame file exists
        assert inc.frame_path == ""

        # Timestamps are valid UTC ISO format
        assert inc.created_at.endswith("Z")


def test_resolve_seed_frame_path(tmp_path):
    frames_dir = tmp_path / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    # 1. Nonexistent file returns empty string
    assert resolve_seed_frame_path("CAM_01/absent.jpg", str(frames_dir)) == ""

    # 2. Existing file returns canonical relative path
    cam_dir = frames_dir / "CAM_01"
    cam_dir.mkdir(parents=True, exist_ok=True)
    real_file = cam_dir / "present.jpg"
    real_file.write_bytes(b"image")

    resolved = resolve_seed_frame_path("CAM_01/present.jpg", str(frames_dir))
    assert resolved == "data/frames/CAM_01/present.jpg"


def test_seed_demo_data_idempotency_and_persistence(temp_env):
    test_db, frames_dir = temp_env
    fixed_time = datetime(2026, 10, 16, 12, 0, 0, tzinfo=timezone.utc)

    # First seeding run
    count1 = seed_demo_data(db_path=test_db, reference_time=fixed_time, frames_dir=frames_dir)
    assert count1 == 6

    incidents1, total1 = list_incidents(db_path=test_db, limit=100)
    assert total1 == 6
    assert len(incidents1) == 6

    # Second seeding run must be idempotent (no duplicate records)
    count2 = seed_demo_data(db_path=test_db, reference_time=fixed_time, frames_dir=frames_dir)
    assert count2 == 6

    incidents2, total2 = list_incidents(db_path=test_db, limit=100)
    assert total2 == 6
    assert len(incidents2) == 6


def test_seed_demo_data_preserves_real_incident(temp_env):
    test_db, frames_dir = temp_env
    init_db(test_db)

    # Insert a real detection from VLM with the same ID as a demo spec
    real_incident = ClassifiedIncident(
        event_id="demo_synth_001",
        camera_id="CAM_REAL",
        timestamp_seconds=999.0,
        category=Category.person_down,
        summary="REAL DETECTION: A person fell at real location.",
        confidence=0.88,
        confidence_type="calibrated_vlm",
        frame_path="data/frames/CAM_REAL/real_001.jpg",
        source=Source.vlm,
        processing_ms=450,
        status=Status.classified,
        evidence_notes="Real detection notes.",
        created_at="2026-10-16T10:00:00Z",
    )
    upsert_incident(real_incident, db_path=test_db)

    # Run seed
    seed_demo_data(db_path=test_db, frames_dir=frames_dir)

    # Verify real incident was NOT overwritten
    stored = get_incident_by_id("demo_synth_001", db_path=test_db)
    assert stored is not None
    assert stored.summary == "REAL DETECTION: A person fell at real location."
    assert stored.source == Source.vlm
    assert stored.confidence == 0.88
    assert stored.processing_ms == 450


def test_demo_workflow_end_to_end_via_api(temp_env):
    test_db, frames_dir = temp_env
    fixed_time = datetime(2026, 10, 16, 12, 0, 0, tzinfo=timezone.utc)
    seed_demo_data(db_path=test_db, reference_time=fixed_time, frames_dir=frames_dir)

    with TestClient(app) as client:
        # Step 4: Health check
        res_health = client.get("/health")
        assert res_health.status_code == 200
        assert res_health.json()["status"] == "healthy"

        # Step 5: List incidents
        res_list = client.get("/api/incidents?limit=10")
        assert res_list.status_code == 200
        body_list = res_list.json()
        assert body_list["total"] == 6
        assert len(body_list["items"]) == 6

        # Step 5b: Category filter
        res_filter = client.get("/api/incidents?category=tailgating")
        assert res_filter.status_code == 200
        assert res_filter.json()["total"] == 1
        assert res_filter.json()["items"][0]["event_id"] == "demo_synth_002"

        # Step 6: Statistics
        res_stats = client.get("/api/stats")
        assert res_stats.status_code == 200
        stats = res_stats.json()
        assert stats["total"] == 6
        assert stats["by_category"]["person_down"] == 1
        assert stats["by_category"]["tailgating"] == 1
        assert stats["by_camera"]["CAM_01"] == 3
        assert stats["by_camera"]["CAM_02"] == 2
        assert stats["by_camera"]["CAM_03"] == 1
        assert stats["by_status"]["classified"] == 3
        assert stats["by_status"]["candidate"] == 1
        assert stats["by_status"]["needs_review"] == 1
        assert stats["by_status"]["failed"] == 1

        # Step 7: Natural-language query
        res_query = client.post("/api/query", json={"question": "Show all tailgating events from camera 2"})
        assert res_query.status_code == 200
        q_data = res_query.json()
        assert q_data["status"] == "success"
        assert len(q_data["incidents"]) == 1
        assert q_data["incidents"][0]["event_id"] == "demo_synth_002"
        assert q_data["interpreted_filters"]["category"] == "tailgating"
        assert q_data["interpreted_filters"]["camera_id"] == "CAM_02"

        # Step 8 & 9: Evidence image missing vs present
        # Nonexistent image returns 404
        res_img_missing = client.get("/data/frames/CAM_01/nonexistent.jpg")
        assert res_img_missing.status_code == 404
        assert res_img_missing.json()["detail"] == "Evidence frame not found"
