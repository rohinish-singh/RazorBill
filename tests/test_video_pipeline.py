from __future__ import annotations

from pathlib import Path
import numpy as np
import pytest

from behavioral_markers.schemas import CameraConfig, Track, ZoneConfig
from datasets_incident_detection.contracts import validate_candidate_packet
from video_pipeline.pipeline import PipelineConfig, process_video

cv2 = pytest.importorskip("cv2")

class FakeTracker:
    def __init__(self, tracks): self.value = tracks
    def tracks(self, frame): return self.value

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

def test_track_continuity_marker_packet_and_keyframe(tmp_path):
    source = tmp_path / "tracks.avi"; video(source)
    packets, metrics = process_video(source, config(tmp_path), FakeTracker([Track(7, (10, 5, 30, 40))]))
    assert len(packets) == 1 and packets[0]["tracks"][0]["track_id"] == 7
    assert validate_candidate_packet(packets[0]) == []
    assert (tmp_path / "frames" / "CAM_TEST" / f"{packets[0]['event_id']}.jpg").is_file()
    assert metrics.candidates_emitted == 1
