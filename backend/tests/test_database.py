import sqlite3
import pytest

try:
    from backend.src.database import (
        get_connection,
        get_incident_by_id,
        init_db,
        upsert_incident,
    )
    from backend.src.schemas import (
        Category,
        ClassifiedIncident,
        Source,
        Status,
    )
except ModuleNotFoundError:
    from src.database import (
        get_connection,
        get_incident_by_id,
        init_db,
        upsert_incident,
    )
    from src.schemas import (
        Category,
        ClassifiedIncident,
        Source,
        Status,
    )


@pytest.fixture
def db_path(tmp_path):
    path = str(tmp_path / "test_razorbill.db")
    init_db(path)
    return path


def test_init_db_creates_table_and_indexes(db_path):
    with get_connection(db_path) as conn:
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='incidents';")
        assert cursor.fetchone() is not None

        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_incidents_%';")
        indexes = {row["name"] for row in cursor.fetchall()}
        expected = {
            "idx_incidents_camera_id",
            "idx_incidents_category",
            "idx_incidents_created_at",
            "idx_incidents_timestamp_seconds",
            "idx_incidents_status",
        }
        assert expected.issubset(indexes)


def test_init_db_is_idempotent(db_path):
    # Calling init_db multiple times must succeed without error
    init_db(db_path)
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.execute("SELECT COUNT(*) as cnt FROM sqlite_master WHERE type='table' AND name='incidents';")
        assert cursor.fetchone()["cnt"] == 1


def test_transaction_rollback_on_error(db_path):
    # Verify that unhandled exceptions roll back the transaction
    with pytest.raises(RuntimeError):
        with get_connection(db_path) as conn:
            conn.execute("""
                INSERT INTO incidents (
                    event_id, camera_id, timestamp_seconds, category, summary,
                    frame_path, source, status, created_at
                ) VALUES ('evt_rollback', 'CAM_1', 1.0, 'other', 'test', 'p.jpg', 'rule', 'candidate', '2026-10-15T10:00:00Z');
            """)
            raise RuntimeError("Simulated failure inside transaction")

    with get_connection(db_path) as conn:
        cursor = conn.execute("SELECT * FROM incidents WHERE event_id = 'evt_rollback';")
        assert cursor.fetchone() is None


def test_upsert_incident_inserts_new_record(db_path):
    incident = ClassifiedIncident(
        event_id="evt_001",
        camera_id="CAM_01",
        timestamp_seconds=45.2,
        category=Category.person_down,
        summary="Person slipped and fell.",
        confidence=0.88,
        confidence_type="vlm_calibrated",
        frame_path="data/frames/CAM_01/evt_001.jpg",
        source=Source.vlm,
        processing_ms=350,
        status=Status.classified,
        evidence_notes="Motion ceased.",
        created_at="2026-10-15T12:00:00Z",
    )

    upsert_incident(incident, db_path=db_path)
    retrieved = get_incident_by_id("evt_001", db_path=db_path)

    assert retrieved is not None
    assert retrieved.event_id == "evt_001"
    assert retrieved.camera_id == "CAM_01"
    assert retrieved.timestamp_seconds == 45.2
    assert retrieved.category == Category.person_down
    assert retrieved.summary == "Person slipped and fell."
    assert retrieved.confidence == 0.88
    assert retrieved.confidence_type == "vlm_calibrated"
    assert retrieved.frame_path == "data/frames/CAM_01/evt_001.jpg"
    assert retrieved.source == Source.vlm
    assert retrieved.processing_ms == 350
    assert retrieved.status == Status.classified
    assert retrieved.evidence_notes == "Motion ceased."
    assert retrieved.created_at == "2026-10-15T12:00:00Z"


def test_upsert_incident_updates_on_duplicate_event_id(db_path):
    initial = ClassifiedIncident(
        event_id="evt_dup_01",
        camera_id="CAM_01",
        timestamp_seconds=10.0,
        category=Category.unknown,
        summary="Candidate motion detected.",
        confidence=None,
        confidence_type="unavailable",
        frame_path="data/frames/CAM_01/evt_dup_01.jpg",
        source=Source.rule,
        processing_ms=10,
        status=Status.candidate,
        evidence_notes=None,
        created_at="2026-10-15T12:00:00Z",
    )
    upsert_incident(initial, db_path=db_path)

    # Second write from VLM enriches existing event_id
    updated = ClassifiedIncident(
        event_id="evt_dup_01",
        camera_id="CAM_01",
        timestamp_seconds=10.0,
        category=Category.fighting,
        summary="Two individuals in aggressive physical confrontation.",
        confidence=0.92,
        confidence_type="vlm_calibrated",
        frame_path="data/frames/CAM_01/evt_dup_01.jpg",
        source=Source.vlm,
        processing_ms=520,
        status=Status.classified,
        evidence_notes="Rapid trajectory convergence.",
        created_at="2026-10-15T12:00:01Z",
    )
    upsert_incident(updated, db_path=db_path)

    # Total row count should still be 1
    with get_connection(db_path) as conn:
        cursor = conn.execute("SELECT COUNT(*) as cnt FROM incidents WHERE event_id='evt_dup_01';")
        assert cursor.fetchone()["cnt"] == 1

    result = get_incident_by_id("evt_dup_01", db_path=db_path)
    assert result is not None
    assert result.category == Category.fighting
    assert result.status == Status.classified
    assert result.confidence == 0.92
    assert result.source == Source.vlm


def test_get_incident_by_id_returns_none_when_not_found(db_path):
    assert get_incident_by_id("nonexistent_event", db_path=db_path) is None


def test_null_fields_persisted_and_retrieved_accurately(db_path):
    incident = ClassifiedIncident(
        event_id="evt_null_01",
        camera_id="CAM_02",
        timestamp_seconds=0.0,
        category=Category.other,
        summary="Stationary object left near exit.",
        confidence=None,
        confidence_type=None,
        frame_path="data/frames/CAM_02/evt_null_01.jpg",
        source=Source.rule,
        processing_ms=None,
        status=Status.candidate,
        evidence_notes=None,
        created_at="2026-10-15T12:05:00Z",
    )
    upsert_incident(incident, db_path=db_path)

    retrieved = get_incident_by_id("evt_null_01", db_path=db_path)
    assert retrieved is not None
    assert retrieved.confidence is None
    assert retrieved.confidence_type is None
    assert retrieved.processing_ms is None
    assert retrieved.evidence_notes is None


def test_razorbill_db_path_env_override_and_dir_creation(tmp_path, monkeypatch):
    custom_dir = tmp_path / "deep" / "nested" / "dir"
    custom_db = str(custom_dir / "custom_razorbill.db")
    monkeypatch.setenv("RAZORBILL_DB_PATH", custom_db)

    # Calling init_db() with default db_path (None) must create the directory and initialize DB at custom_db
    init_db()
    assert custom_dir.exists()
    assert (custom_dir / "custom_razorbill.db").exists()

    incident = ClassifiedIncident(
        event_id="evt_env_override",
        camera_id="CAM_01",
        timestamp_seconds=5.0,
        category=Category.fighting,
        summary="Test dynamic env override",
        frame_path="data/frames/CAM_01/evt.jpg",
        source=Source.vlm,
        status=Status.classified,
        created_at="2026-10-15T12:00:00Z",
    )
    upsert_incident(incident)
    retrieved = get_incident_by_id("evt_env_override")
    assert retrieved is not None
    assert retrieved.event_id == "evt_env_override"
