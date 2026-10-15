from __future__ import annotations

from pathlib import Path
import json
import numpy as np
import pytest

from behavioral_markers.schemas import CameraConfig, IncidentConfig, ObjectFlag, Track, ZoneConfig
from datasets_incident_detection.contracts import validate_candidate_packet
from video_pipeline.pipeline import PipelineConfig, process_video
from video_pipeline.__main__ import _weapon_labels
from video_pipeline.annotate import export_annotated_video

cv2 = pytest.importorskip("cv2")

class FakeTracker:
    def __init__(self, tracks): self.value = tracks
    def tracks(self, frame): return self.value

class FakeObjectDetector:
    def flags(self, frame): return [ObjectFlag("firearm", 0.9, (5, 5, 15, 15))]

def video(path: Path, frames=4):
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"MJPG"), 10, (64, 48))
    for _ in range(frames): writer.write(np.full((48, 64, 3), 160, np.uint8))
    writer.release()

def config(tmp_path):
    zone = ZoneConfig("restricted", ((0, 0), (64, 0), (64, 48), (0, 48)), restricted=True, cooldown_seconds=10)
    return PipelineConfig(CameraConfig("CAM_TEST", "fixture", (zone,)), sample_every=1, output_root=tmp_path / "frames")

def test_invalid_video(tmp_path):
    with pytest.raises(FileNotFoundError): process_video(tmp_path / "absent.avi", config(tmp_path), FakeTracker([]))

def test_empty_detections_process_without_packets(tmp_path):
    source = tmp_path / "empty.avi"; video(source)
    packets, metrics = process_video(source, config(tmp_path), FakeTracker([]))
    assert packets == [] and metrics.frames_sampled == 4
    assert metrics.max_person_bbox_aspect_ratio == 0.0 and metrics.frames_meeting_person_down_geometry == 0

def test_track_continuity_marker_packet_and_keyframe(tmp_path):
    source = tmp_path / "tracks.avi"; video(source)
    packets, metrics = process_video(source, config(tmp_path), FakeTracker([Track(7, (10, 5, 30, 40))]))
    assert len(packets) == 1 and packets[0]["tracks"][0]["track_id"] == 7
    assert validate_candidate_packet(packets[0]) == []
    assert (tmp_path / "frames" / "CAM_TEST" / f"{packets[0]['event_id']}.jpg").is_file()
    assert metrics.candidates_emitted == 1
    assert metrics.frames_with_people == 4 and metrics.person_detections == 4
    assert metrics.track_continuity_hits == 3 and metrics.as_dict()["distinct_track_ids"] == 1
    assert metrics.max_person_bbox_aspect_ratio == pytest.approx(20 / 35)

def test_configurable_relative_keyframe_path(tmp_path):
    source = tmp_path / "relative.avi"; video(source)
    current = config(tmp_path)
    custom = PipelineConfig(current.camera, sample_every=1, output_root=tmp_path / "frames", relative_frame_root=Path("relative/frames"))
    packets, _ = process_video(source, custom, FakeTracker([Track(3, (10, 5, 30, 40))]))
    assert packets[0]["frame_path"].startswith("relative/frames/CAM_TEST/")

def test_annotation_export_contains_source_relative_track_observations(tmp_path):
    source = tmp_path / "annotate.avi"; video(source, frames=3)
    report = export_annotated_video(source, tmp_path / "annotated.mp4", FakeTracker([Track(2, (10, 5, 30, 40))]))
    assert report["frames"] == 3 and report["observations"][1]["timestamp_seconds"] == pytest.approx(0.1)
    assert report["observations"][0]["tracks"][0]["track_id"] == 2
    assert (tmp_path / "annotated.mp4").is_file()

def test_specialized_object_flags_emit_contract_candidate_and_keyframe(tmp_path):
    source = tmp_path / "weapon.avi"; video(source)
    current = config(tmp_path)
    camera = CameraConfig(current.camera.camera_id, current.camera.video_source_id, current.camera.zones, incident=IncidentConfig(enabled=True))
    packets, _ = process_video(source, PipelineConfig(camera, sample_every=1, output_root=tmp_path / "frames"), FakeTracker([]), object_detector=FakeObjectDetector())
    assert packets[0]["trigger"] == "weapon_firearm_candidate"
    assert validate_candidate_packet(packets[0]) == []
    assert (tmp_path / "frames" / "CAM_TEST" / f"{packets[0]['event_id']}.jpg").is_file()

def test_weapon_model_class_mapping_is_explicit():
    assert _weapon_labels(["0=knife", "2=firearm"]) == {0: "knife", 2: "firearm"}

def test_portable_person2_fixture_is_contract_valid_and_openable():
    repo_root = Path(__file__).resolve().parents[1]
    packet = json.loads((repo_root / "demo_assets/person1/sample_candidate.jsonl").read_text(encoding="utf-8").splitlines()[0])
    keyframe = repo_root / packet["frame_path"]
    assert validate_candidate_packet(packet) == [] and keyframe.is_file()
    assert cv2.imread(str(keyframe)) is not None
