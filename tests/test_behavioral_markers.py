from __future__ import annotations

import numpy as np

from behavioral_markers.camera_health import observe_frame
from behavioral_markers.engine import MarkerEngine
from behavioral_markers.event_adapter import to_candidate_packet
from behavioral_markers.schemas import CameraConfig, Track, ZoneConfig
from datasets_incident_detection.contracts import validate_candidate_packet

ZONE = ZoneConfig("door", ((0, 0), (100, 0), (100, 100), (0, 100)), restricted=True, loiter_seconds=2, min_observations=2, crowd_threshold=2, crowd_persist_seconds=2, cooldown_seconds=5)
CONFIG = CameraConfig("CAM_01", "fixture", (ZONE,), darkness_mean_threshold=30, darkness_drop=30, health_persist_seconds=2, freeze_persist_seconds=2, obstruction_sharpness_threshold=1, obstruction_texture_threshold=1)

def track(identifier=1, x=10): return Track(identifier, (x, 10, x + 10, 50))

def test_restricted_entry_once_and_contract_packet():
    engine = MarkerEngine(CONFIG); events = engine.process_tracks(0, [track()])
    assert [event.marker_type for event in events] == ["restricted_zone_entry"]
    assert engine.process_tracks(1, [track()]) == []
    assert validate_candidate_packet(to_candidate_packet(events[0], "data/frame.jpg")) == []

def test_loiter_and_track_loss_reset_are_conservative():
    engine = MarkerEngine(CONFIG); engine.process_tracks(0, [track()]); engine.process_tracks(1, [track()])
    assert not engine.process_tracks(1.9, [track()])
    assert any(event.marker_type == "loitering" for event in engine.process_tracks(2, [track()]))
    engine.process_tracks(3, []); assert not any(event.marker_type == "loitering" for event in engine.process_tracks(4, [track(99)]))

def test_crowd_persistence_and_cooldown():
    engine = MarkerEngine(CONFIG); engine.process_tracks(0, [track(1), track(2, 50)])
    assert not engine.process_tracks(1, [track(1), track(2, 50)])
    assert any(event.marker_type == "crowd_gathering" for event in engine.process_tracks(2, [track(1), track(2, 50)]))
    assert not engine.process_tracks(3, [track(1), track(2, 50)])

def test_continuous_events_reset_before_reactivation():
    engine = MarkerEngine(CONFIG)
    engine.process_tracks(0, [track(1), track(2, 50)])
    assert any(event.marker_type == "crowd_gathering" for event in engine.process_tracks(2, [track(1), track(2, 50)]))
    assert not engine.process_tracks(8, [track(1), track(2, 50)])
    engine.process_tracks(9, [])
    engine.process_tracks(12, [track(1), track(2, 50)])
    assert any(event.marker_type == "crowd_gathering" for event in engine.process_tracks(14, [track(1), track(2, 50)]))

def test_camera_health_reactivation_requires_clear_frame():
    engine = MarkerEngine(CONFIG); dark = np.zeros((16, 16, 3), np.uint8); bright = np.full((16, 16, 3), 180, np.uint8)
    engine.process_frame_observation(observe_frame(dark, 0))
    assert any(event.marker_type == "camera_dark" for event in engine.process_frame_observation(observe_frame(dark, 2, dark)))
    assert not any(event.marker_type == "camera_dark" for event in engine.process_frame_observation(observe_frame(dark, 8, dark)))
    engine.process_frame_observation(observe_frame(bright, 9, dark))
    engine.process_frame_observation(observe_frame(dark, 10, bright))
    assert any(event.marker_type == "camera_dark" for event in engine.process_frame_observation(observe_frame(dark, 12, dark)))

def test_darkness_needs_sustained_frames_and_records_transition():
    engine = MarkerEngine(CONFIG); bright = np.full((16, 16, 3), 180, np.uint8); dark = np.zeros((16, 16, 3), np.uint8)
    engine.process_frame_observation(observe_frame(bright, 0)); assert not engine.process_frame_observation(observe_frame(dark, 1, bright))
    events = engine.process_frame_observation(observe_frame(dark, 3, dark)); dark_event = next(event for event in events if event.marker_type == "camera_dark")
    assert dark_event.evidence["persist_seconds"] == 2

def test_frozen_feed_and_source_failure_are_review_candidates():
    engine = MarkerEngine(CONFIG); frame = np.full((16, 16, 3), 100, np.uint8)
    engine.process_frame_observation(observe_frame(frame, 0)); engine.process_frame_observation(observe_frame(frame, 1, frame))
    assert any(event.marker_type == "frozen_feed_candidate" for event in engine.process_frame_observation(observe_frame(frame, 3, frame)))
    assert engine.source_read_failed(4, "decoder EOF")[0].category == "other"

def test_obstruction_is_not_claimed_as_malicious():
    engine = MarkerEngine(CONFIG); flat = np.full((16, 16, 3), 100, np.uint8)
    engine.process_frame_observation(observe_frame(flat, 0)); events = engine.process_frame_observation(observe_frame(flat, 2, flat))
    obstruction = next(event for event in events if event.marker_type == "camera_obstruction_candidate")
    assert "caveat" in obstruction.evidence and obstruction.status == "needs_review"
