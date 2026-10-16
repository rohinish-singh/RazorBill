from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from behavioral_markers.schemas import CameraConfig, IncidentConfig, Track
from datasets_incident_detection.contracts import validate_candidate_packet
from video_pipeline.action import ActionPrediction, SlidingWindowActionAdapter, bgr_frames_to_rgb, torch_device
from video_pipeline.evidence import EvidenceBuffer
from video_pipeline.pipeline import PipelineConfig, process_video
from video_pipeline.pose import PoseObservation, associate_pose_cues

cv2 = pytest.importorskip("cv2")


def _video(path: Path, frames: int = 4):
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"MJPG"), 10, (64, 48))
    for index in range(frames):
        writer.write(np.full((48, 64, 3), index * 20, np.uint8))
    writer.release()


class _Tracker:
    def tracks(self, frame):
        return [Track(3, (10, 5, 30, 40))]


class _PoseEstimator:
    def poses(self, frame):
        points = tuple((10.0 + index * 4, 10.0 + (index % 2) * 3, 0.9) for index in range(8))
        return [PoseObservation((10, 5, 30, 40), points)]


def test_pose_association_is_one_to_one_and_rejects_low_confidence():
    tracks = [Track(1, (0, 0, 20, 40)), Track(2, (30, 0, 50, 40))]
    good = PoseObservation((0, 0, 20, 40), tuple((float(index), 1.0, 0.9) for index in range(6)))
    weak = PoseObservation((30, 0, 50, 40), tuple((float(index), 1.0, 0.1) for index in range(6)))
    cues = associate_pose_cues(tracks, [good, weak])
    assert len(cues) == 1 and cues[0].track_id == 1 and cues[0].confident_keypoint_count == 6


def test_pose_cue_emits_separate_review_candidate(tmp_path):
    source = tmp_path / "pose.avi"; _video(source)
    camera = CameraConfig("POSE", "fixture", incident=IncidentConfig(enabled=True, person_down_aspect_ratio=99,
                          pose_enabled=True, pose_down_ratio=1.1, pose_down_persist_seconds=0))
    packets, metrics = process_video(source, PipelineConfig(camera, sample_every=1, output_root=tmp_path / "frames"),
                                      _Tracker(), pose_estimator=_PoseEstimator())
    assert packets[0]["trigger"] == "pose_person_down_candidate"
    assert metrics.pose_observations == 4 and metrics.pose_matched_tracks == 4
    assert metrics.max_pose_posture_ratio > 1.1 and metrics.frames_meeting_pose_down_geometry == 4


def test_action_window_adapter_uses_stride_and_preserves_window_times():
    class Model:
        def predict(self, frames):
            return "generic_action", 0.7
    adapter = SlidingWindowActionAdapter(Model(), window_frames=3, stride_frames=2)
    frames = [np.zeros((4, 4, 3), np.uint8) for _ in range(5)]
    assert adapter.observe(0.0, frames[0]) is None and adapter.observe(0.1, frames[1]) is None
    first = adapter.observe(0.2, frames[2]); assert first and first.label == "generic_action" and first.start_seconds == 0.0
    assert adapter.observe(0.3, frames[3]) is None
    second = adapter.observe(0.4, frames[4]); assert second and second.start_seconds == 0.2 and second.end_seconds == 0.4


def test_action_preprocessing_converts_bgr_to_rgb_without_mutating_source():
    frame = np.array([[[1, 2, 3]]], dtype=np.uint8)
    rgb = bgr_frames_to_rgb([frame])[0]
    assert rgb.tolist() == [[[3, 2, 1]]]
    rgb[0, 0, 0] = 99
    assert frame.tolist() == [[[1, 2, 3]]]


def test_torch_device_accepts_yolo_numeric_gpu_and_cpu_values():
    assert torch_device("0", True) == "cuda:0"
    assert torch_device("cpu", True) == "cpu"
    assert torch_device(None, False) == "cpu"


def test_temporal_fighting_candidate_is_contract_valid_and_deduplicated(tmp_path):
    class ViolentModel:
        def predict(self, frames):
            return ActionPrediction("violent", 0.9, {"non_violent": 0.1, "violent": 0.9}, "fixture-violence")
    source = tmp_path / "fight.avi"; _video(source, frames=6)
    camera = CameraConfig("FIGHT", "fixture", incident=IncidentConfig(enabled=True, temporal_fighting_enabled=True,
                          temporal_fighting_label="violent", temporal_fighting_score_threshold=0.8, cooldown_seconds=30))
    adapter = SlidingWindowActionAdapter(ViolentModel(), window_frames=2, stride_frames=1)
    packets, metrics = process_video(source, PipelineConfig(camera, sample_every=1, output_root=tmp_path / "frames",
                                      evidence_root=tmp_path / "evidence", relative_evidence_root=Path("evidence")),
                                      _Tracker(), action_adapter=adapter)
    assert len(packets) == 1 and packets[0]["trigger"] == "temporal_fighting_candidate"
    assert packets[0]["tracks"] and metrics.temporal_windows == 5 and metrics.temporal_fighting_windows == 5
    assert validate_candidate_packet(packets[0]) == [] and Path(packets[0]["frame_path"]).name in {item.name for item in (tmp_path / "frames" / "FIGHT").glob("*.jpg")}
    assert metrics.evidence_clips_written == 1
    evidence = next((tmp_path / "evidence").glob("*.mp4")); capture = cv2.VideoCapture(str(evidence)); ok, _ = capture.read(); capture.release()
    assert ok


def test_temporal_stride_gaps_do_not_reset_a_positive_episode(tmp_path):
    class AlternatingModel:
        def predict(self, frames):
            return ActionPrediction("violent", 0.9, {"violent": 0.9}, "fixture-violence")
    source = tmp_path / "stride.avi"; _video(source, frames=5)
    camera = CameraConfig("FIGHT", "fixture", incident=IncidentConfig(enabled=True, temporal_fighting_enabled=True,
                          temporal_fighting_label="violent", temporal_fighting_score_threshold=0.8, cooldown_seconds=30))
    adapter = SlidingWindowActionAdapter(AlternatingModel(), window_frames=2, stride_frames=3)
    packets, _ = process_video(source, PipelineConfig(camera, sample_every=1, output_root=tmp_path / "frames"), _Tracker(), action_adapter=adapter)
    assert len(packets) == 1


def test_evidence_buffer_writes_bounded_sidecar_clip(tmp_path):
    buffer = EvidenceBuffer(pre_seconds=0.2, post_seconds=0.2, fps=10)
    for timestamp in (0.0, 0.1, 0.2):
        buffer.add(timestamp, np.full((16, 16, 3), 100, np.uint8))
    buffer.register("evt_safe", 0.2)
    for timestamp in (0.3, 0.4, 0.5):
        buffer.add(timestamp, np.full((16, 16, 3), 120, np.uint8))
    index = buffer.write(tmp_path, Path("evidence"), cv2)
    assert index[0]["event_id"] == "evt_safe" and index[0]["frame_count"] == 5
    assert (tmp_path / "evt_safe.mp4").is_file() and (tmp_path / "index.jsonl").is_file()


def test_pipeline_rejects_invalid_pose_sampling_and_evidence_durations(tmp_path):
    source = tmp_path / "invalid.avi"; _video(source)
    camera = CameraConfig("cam", "source")
    with pytest.raises(ValueError, match="pose_every"):
        process_video(source, PipelineConfig(camera, pose_every=0), _Tracker())
    with pytest.raises(ValueError, match="evidence durations"):
        process_video(source, PipelineConfig(camera, evidence_pre_seconds=-0.1), _Tracker())
