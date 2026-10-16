from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from behavioral_markers.schemas import CameraConfig, IncidentConfig, ObjectFlag, Track
from datasets_incident_detection.contracts import validate_candidate_packet
from video_pipeline.pipeline import PipelineConfig, process_video
from video_pipeline.weapons import UltralyticsGunKnifeDetector, WeaponTemporalFilter, validate_weapon_class_names

cv2 = pytest.importorskip("cv2")


def _video(path: Path, frames: int = 5) -> None:
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"MJPG"), 10, (64, 48))
    for index in range(frames):
        writer.write(np.full((48, 64, 3), index * 20, np.uint8))
    writer.release()


class _Tracker:
    def tracks(self, frame):
        return [Track(3, (10, 5, 30, 40))]


class _WeaponDetector:
    def __init__(self, label: str = "firearm", confidence: float = 0.9):
        self.label, self.confidence = label, confidence

    def flags(self, frame):
        return [ObjectFlag(self.label, self.confidence, (15, 10, 28, 20),
                           class_id=0 if self.label == "firearm" else 1,
                           class_name="gun" if self.label == "firearm" else "knife")]


def test_verified_gun_and_knife_class_mapping_and_invalid_mapping():
    assert UltralyticsGunKnifeDetector.LABEL_BY_CLASS == {0: "firearm", 1: "knife"}
    assert validate_weapon_class_names({0: "gun", 1: "knife"}) == {0: "gun", 1: "knife"}
    with pytest.raises(ValueError, match="class mapping"):
        validate_weapon_class_names({0: "knife", 1: "gun"})


def test_missing_weapon_weights_fail_before_inference(tmp_path):
    with pytest.raises(FileNotFoundError, match="weights not found"):
        UltralyticsGunKnifeDetector(str(tmp_path / "missing.pt"))


def test_weapon_filter_requires_spatially_consistent_observations_and_deduplicates():
    filter_ = WeaponTemporalFilter(min_observations=2, max_gap_seconds=0.5, min_iou=0.2)
    frame = np.zeros((8, 8, 3), np.uint8)
    gun = ObjectFlag("firearm", 0.7, (0, 0, 4, 4), class_id=0, class_name="gun")
    assert filter_.observe(0.0, [gun], frame) == []
    confirmed = filter_.observe(0.1, [ObjectFlag("firearm", 0.9, (0, 0, 4, 4), class_id=0, class_name="gun")], frame)
    assert len(confirmed) == 1 and confirmed[0].observation_count == 2
    assert confirmed[0].first_detection_timestamp_seconds == 0.0
    assert confirmed[0].strongest_detection_timestamp_seconds == 0.1
    assert len(filter_.observe(0.2, [gun], frame)) == 1
    assert filter_.observe(1.0, [], frame) == []


def test_weapon_filter_rejects_intermittent_or_spatially_unrelated_flags():
    filter_ = WeaponTemporalFilter(min_observations=2, max_gap_seconds=0.1, min_iou=0.5)
    frame = np.zeros((8, 8, 3), np.uint8)
    assert filter_.observe(0.0, [ObjectFlag("knife", 0.9, (0, 0, 2, 2))], frame) == []
    assert filter_.observe(0.2, [ObjectFlag("knife", 0.9, (0, 0, 2, 2))], frame) == []
    assert filter_.observe(0.21, [ObjectFlag("knife", 0.9, (5, 5, 7, 7))], frame) == []


def test_temporally_confirmed_weapon_emits_packet_keyframe_and_evidence(tmp_path):
    source = tmp_path / "weapon.avi"; _video(source)
    camera = CameraConfig("WEAPON", "fixture", incident=IncidentConfig(enabled=True, object_confidence_threshold=0.5,
                          cooldown_seconds=30))
    packets, metrics = process_video(source, PipelineConfig(camera, sample_every=1, output_root=tmp_path / "frames",
                                      evidence_root=tmp_path / "evidence", relative_evidence_root=Path("evidence")),
                                      _Tracker(), object_detector=_WeaponDetector(), weapon_filter=WeaponTemporalFilter(2, 0.5))
    assert len(packets) == 1 and packets[0]["trigger"] == "weapon_firearm_candidate"
    assert validate_candidate_packet(packets[0]) == []
    assert metrics.object_detections == 5 and metrics.weapon_confirmed_observations >= 4 and metrics.evidence_clips_written == 1
    assert next((tmp_path / "frames" / "WEAPON").glob("*.jpg")).is_file()
    clip = next((tmp_path / "evidence").glob("*.mp4")); capture = cv2.VideoCapture(str(clip)); ok, _ = capture.read(); capture.release()
    assert ok


def test_weapon_detector_disabled_preserves_no_weapon_events(tmp_path):
    source = tmp_path / "normal.avi"; _video(source)
    packets, _ = process_video(source, PipelineConfig(CameraConfig("OFF", "fixture"), output_root=tmp_path / "frames"), _Tracker())
    assert packets == []
