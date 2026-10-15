from __future__ import annotations

from behavioral_markers.engine import MarkerEngine
from behavioral_markers.config import camera_config_from_dict
from behavioral_markers.schemas import CameraConfig, IncidentConfig, ObjectFlag, Track


def engine(**settings) -> MarkerEngine:
    return MarkerEngine(CameraConfig("CAM_INCIDENT", "fixture", incident=IncidentConfig(enabled=True, cooldown_seconds=1, **settings)))


def test_person_down_requires_persistence_and_is_review_candidate():
    marker = engine(person_down_persist_seconds=1.0)
    down = Track(4, (10, 10, 110, 50))
    assert marker.process_incidents(0.0, [down]) == []
    events = marker.process_incidents(1.0, [down])
    assert [event.marker_type for event in events] == ["person_down_candidate"]
    assert events[0].category == "person_down" and events[0].status == "needs_review"
    assert marker.process_incidents(2.0, [down]) == []


def test_fighting_is_proximity_motion_cue_not_an_assertion():
    marker = engine(person_down_persist_seconds=99, fighting_pair_distance=100, fighting_motion_pixels_per_second=100, fighting_persist_seconds=0)
    marker.process_incidents(0.0, [Track(1, (0, 0, 20, 80)), Track(2, (40, 0, 60, 80))])
    events = marker.process_incidents(0.1, [Track(1, (30, 0, 50, 80)), Track(2, (50, 0, 70, 80))])
    fight = next(event for event in events if event.marker_type == "fighting_candidate")
    assert fight.category == "fighting" and "not proof" in fight.evidence["caveat"]


def test_weapon_flags_require_specialized_detector_input_and_reset():
    marker = engine(person_down_persist_seconds=99)
    knife = ObjectFlag("knife", 0.9, (1, 1, 5, 5))
    events = marker.process_incidents(0.0, [], [knife])
    assert [event.marker_type for event in events] == ["weapon_knife_candidate"]
    assert marker.process_incidents(1.0, [], [knife]) == []
    marker.process_incidents(2.0, [], [])
    assert [event.marker_type for event in marker.process_incidents(3.0, [], [knife])] == ["weapon_knife_candidate"]


def test_incident_configuration_is_opt_in():
    config = camera_config_from_dict({"camera_id": "CAM", "video_source_id": "fixture", "incident": {"enabled": True, "fighting_persist_seconds": 0.25}})
    assert config.incident.enabled and config.incident.fighting_persist_seconds == 0.25
