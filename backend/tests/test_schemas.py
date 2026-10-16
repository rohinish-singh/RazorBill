import pytest
from pydantic import ValidationError

try:
    from backend.src.schemas import (
        Category,
        Source,
        Status,
        Track,
        CandidateEventPacket,
        ClassifiedIncident,
    )
except ModuleNotFoundError:
    from src.schemas import (
        Category,
        Source,
        Status,
        Track,
        CandidateEventPacket,
        ClassifiedIncident,
    )


def test_valid_candidate_event_packet_accepted():
    payload = {
        "event_id": "evt_unique_id",
        "camera_id": "CAM_01",
        "video_source_id": "demo_video_01",
        "timestamp_seconds": 134.5,
        "frame_path": "data/frames/CAM_01/evt_unique_id.jpg",
        "frame_paths": [],
        "tracks": [
            {"track_id": 12, "class_name": "person", "bbox_xyxy": [120, 80, 260, 410]}
        ],
        "trigger": "sampled_frame",
        "created_at": "2026-10-15T10:00:00Z",
    }
    packet = CandidateEventPacket(**payload)
    assert packet.event_id == "evt_unique_id"
    assert packet.camera_id == "CAM_01"
    assert packet.timestamp_seconds == 134.5
    assert len(packet.tracks) == 1
    assert packet.tracks[0].track_id == 12
    assert packet.tracks[0].class_name == "person"
    assert packet.tracks[0].bbox_xyxy == [120.0, 80.0, 260.0, 410.0]


def test_valid_classified_incident_accepted():
    payload = {
        "event_id": "evt_unique_id",
        "camera_id": "CAM_01",
        "timestamp_seconds": 134.5,
        "category": "person_down",
        "summary": "A person appears to be lying on the floor near the entrance.",
        "confidence": None,
        "confidence_type": "unavailable",
        "frame_path": "data/frames/CAM_01/evt_unique_id.jpg",
        "source": "vlm",
        "processing_ms": 740,
        "status": "classified",
        "evidence_notes": "Visible posture is consistent with a person on the floor.",
        "created_at": "2026-10-15T10:00:01Z",
    }
    incident = ClassifiedIncident(**payload)
    assert incident.event_id == "evt_unique_id"
    assert incident.category == Category.person_down
    assert incident.confidence is None
    assert incident.confidence_type == "unavailable"
    assert incident.source == Source.vlm
    assert incident.status == Status.classified
    assert incident.processing_ms == 740


def test_all_canonical_category_values_accepted():
    expected_categories = [
        "person_down",
        "fighting",
        "tailgating",
        "crowd_incident",
        "suspicious_activity",
        "other",
        "unknown",
    ]
    for cat in expected_categories:
        assert Category(cat).value == cat


def test_all_canonical_source_values_accepted():
    for src in ["rule", "vlm", "manual"]:
        assert Source(src).value == src


def test_all_canonical_status_values_accepted():
    for st in ["candidate", "classified", "needs_review", "failed"]:
        assert Status(st).value == st


def test_invalid_enum_values_rejected():
    base_payload = {
        "event_id": "evt_1",
        "camera_id": "CAM_01",
        "timestamp_seconds": 10.0,
        "category": "person_down",
        "summary": "Sample summary",
        "frame_path": "path/to/frame.jpg",
        "source": "vlm",
        "status": "classified",
        "created_at": "2026-10-15T10:00:00Z",
    }

    # Invalid Category
    with pytest.raises(ValidationError):
        ClassifiedIncident(**{**base_payload, "category": "intruder"})

    # Invalid Source
    with pytest.raises(ValidationError):
        ClassifiedIncident(**{**base_payload, "source": "cloud_ai"})

    # Invalid Status
    with pytest.raises(ValidationError):
        ClassifiedIncident(**{**base_payload, "status": "resolved"})


def test_confidence_nullable_and_bounded():
    base_payload = {
        "event_id": "evt_1",
        "camera_id": "CAM_01",
        "timestamp_seconds": 10.0,
        "category": "person_down",
        "summary": "Sample summary",
        "frame_path": "path/to/frame.jpg",
        "source": "vlm",
        "status": "classified",
        "created_at": "2026-10-15T10:00:00Z",
    }

    # Explicit None
    inc_null = ClassifiedIncident(**{**base_payload, "confidence": None})
    assert inc_null.confidence is None

    # Omitted defaults to None
    inc_default = ClassifiedIncident(**base_payload)
    assert inc_default.confidence is None

    # Valid bounds
    inc_zero = ClassifiedIncident(**{**base_payload, "confidence": 0.0})
    assert inc_zero.confidence == 0.0

    inc_one = ClassifiedIncident(**{**base_payload, "confidence": 1.0})
    assert inc_one.confidence == 1.0

    inc_mid = ClassifiedIncident(**{**base_payload, "confidence": 0.85})
    assert inc_mid.confidence == 0.85

    # Out of bounds: negative
    with pytest.raises(ValidationError):
        ClassifiedIncident(**{**base_payload, "confidence": -0.1})

    # Out of bounds: > 1.0
    with pytest.raises(ValidationError):
        ClassifiedIncident(**{**base_payload, "confidence": 1.05})


def test_missing_required_fields_rejected():
    # CandidateEventPacket missing event_id
    with pytest.raises(ValidationError):
        CandidateEventPacket(
            camera_id="CAM_01",
            video_source_id="clip.mp4",
            timestamp_seconds=1.0,
            frame_path="path.jpg",
            trigger="trigger",
            created_at="2026-10-15T10:00:00Z",
        )

    # ClassifiedIncident missing summary
    with pytest.raises(ValidationError):
        ClassifiedIncident(
            event_id="evt_1",
            camera_id="CAM_01",
            timestamp_seconds=1.0,
            category=Category.person_down,
            frame_path="path.jpg",
            source=Source.vlm,
            status=Status.classified,
            created_at="2026-10-15T10:00:00Z",
        )


def test_invalid_field_types_rejected():
    base_payload = {
        "event_id": "evt_1",
        "camera_id": "CAM_01",
        "timestamp_seconds": 10.0,
        "category": "person_down",
        "summary": "Sample summary",
        "frame_path": "path/to/frame.jpg",
        "source": "vlm",
        "status": "classified",
        "created_at": "2026-10-15T10:00:00Z",
    }

    # timestamp_seconds not numeric
    with pytest.raises(ValidationError):
        ClassifiedIncident(**{**base_payload, "timestamp_seconds": "not-a-number"})

    # processing_ms not an int
    with pytest.raises(ValidationError):
        ClassifiedIncident(**{**base_payload, "processing_ms": "not-an-int"})

    # negative processing_ms rejected
    with pytest.raises(ValidationError):
        ClassifiedIncident(**{**base_payload, "processing_ms": -50})

    # bbox_xyxy not 4 elements
    with pytest.raises(ValidationError):
        Track(track_id=1, class_name="person", bbox_xyxy=[10.0, 20.0])


def test_timestamp_seconds_nonnegative():
    base_payload = {
        "event_id": "evt_1",
        "camera_id": "CAM_01",
        "category": "person_down",
        "summary": "Sample summary",
        "frame_path": "path/to/frame.jpg",
        "source": "vlm",
        "status": "classified",
        "created_at": "2026-10-15T10:00:00Z",
    }

    # timestamp_seconds = 0.0 is valid
    inc_zero = ClassifiedIncident(**{**base_payload, "timestamp_seconds": 0.0})
    assert inc_zero.timestamp_seconds == 0.0

    # timestamp_seconds negative rejected
    with pytest.raises(ValidationError):
        ClassifiedIncident(**{**base_payload, "timestamp_seconds": -0.01})

    with pytest.raises(ValidationError):
        CandidateEventPacket(
            event_id="evt_1",
            camera_id="CAM_01",
            video_source_id="clip.mp4",
            timestamp_seconds=-1.0,
            frame_path="path.jpg",
            trigger="trigger",
            created_at="2026-10-15T10:00:00Z",
        )


def test_created_at_validation():
    from datetime import datetime, timezone, timedelta

    base_payload = {
        "event_id": "evt_1",
        "camera_id": "CAM_01",
        "timestamp_seconds": 5.0,
        "category": "person_down",
        "summary": "Sample summary",
        "frame_path": "path/to/frame.jpg",
        "source": "vlm",
        "status": "classified",
    }

    # 1. Valid UTC timestamps
    inc_z = ClassifiedIncident(**{**base_payload, "created_at": "2026-10-15T10:00:00Z"})
    assert inc_z.created_at == "2026-10-15T10:00:00Z"

    inc_offset_zero = ClassifiedIncident(
        **{**base_payload, "created_at": "2026-10-15T10:00:00+00:00"}
    )
    assert inc_offset_zero.created_at == "2026-10-15T10:00:00+00:00"

    utc_dt = datetime(2026, 10, 15, 10, 0, 0, tzinfo=timezone.utc)
    inc_dt = ClassifiedIncident(**{**base_payload, "created_at": utc_dt})
    assert inc_dt.created_at == "2026-10-15T10:00:00Z"

    # CandidateEventPacket also validates valid UTC
    cand_z = CandidateEventPacket(
        event_id="evt_1",
        camera_id="CAM_01",
        video_source_id="clip.mp4",
        timestamp_seconds=1.0,
        frame_path="path.jpg",
        trigger="trigger",
        created_at="2026-10-15T10:00:00Z",
    )
    assert cand_z.created_at == "2026-10-15T10:00:00Z"

    # 2. Timestamps with non-UTC offset must be REJECTED
    with pytest.raises(ValidationError, match="UTC offset"):
        ClassifiedIncident(**{**base_payload, "created_at": "2026-10-15T10:00:00+05:30"})

    with pytest.raises(ValidationError, match="UTC offset"):
        ClassifiedIncident(**{**base_payload, "created_at": "2026-10-15T10:00:00-04:00"})

    tz_est = timezone(timedelta(hours=-5))
    with pytest.raises(ValidationError, match="UTC"):
        ClassifiedIncident(**{**base_payload, "created_at": datetime(2026, 10, 15, 10, 0, 0, tzinfo=tz_est)})

    # 3. Timestamps without timezone information must be REJECTED
    with pytest.raises(ValidationError, match="include timezone"):
        ClassifiedIncident(**{**base_payload, "created_at": "2026-10-15T10:00:00"})

    with pytest.raises(ValidationError, match="include timezone"):
        ClassifiedIncident(**{**base_payload, "created_at": datetime(2026, 10, 15, 10, 0, 0)})

    with pytest.raises(ValidationError, match="include timezone"):
        CandidateEventPacket(
            event_id="evt_1",
            camera_id="CAM_01",
            video_source_id="clip.mp4",
            timestamp_seconds=1.0,
            frame_path="path.jpg",
            trigger="trigger",
            created_at="2026-10-15T10:00:00",
        )

    # 4. Invalid timestamp strings must be REJECTED
    with pytest.raises(ValidationError):
        ClassifiedIncident(**{**base_payload, "created_at": "invalid-timestamp"})

    with pytest.raises(ValidationError):
        ClassifiedIncident(**{**base_payload, "created_at": "2026-99-99T99:99:99Z"})

    with pytest.raises(ValidationError):
        ClassifiedIncident(**{**base_payload, "created_at": 1234567890})
