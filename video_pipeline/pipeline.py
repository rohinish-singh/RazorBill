from __future__ import annotations

import json
import queue
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Protocol

from behavioral_markers.camera_health import observe_frame
from behavioral_markers.engine import MarkerEngine
from behavioral_markers.event_adapter import to_candidate_packet
from behavioral_markers.schemas import CameraConfig, Track
from datasets_incident_detection.contracts import validate_candidate_packet


class DetectorTracker(Protocol):
    def tracks(self, frame) -> list[Track]: ...


@dataclass(frozen=True)
class PipelineConfig:
    camera: CameraConfig
    sample_every: int = 3
    output_root: Path = Path("data/frames")
    confidence: float = 0.30
    device: str | None = None
    max_candidates: int = 128


@dataclass
class PipelineMetrics:
    frames_read: int = 0
    frames_sampled: int = 0
    candidates_emitted: int = 0
    candidates_dropped: int = 0
    read_seconds: float = 0.0
    inference_seconds: float = 0.0
    marker_seconds: float = 0.0
    elapsed_seconds: float = 0.0

    def as_dict(self) -> dict:
        sampled_fps = self.frames_sampled / self.elapsed_seconds if self.elapsed_seconds else 0.0
        return self.__dict__ | {"sampled_fps": sampled_fps,
            "mean_inference_ms": 1000 * self.inference_seconds / self.frames_sampled if self.frames_sampled else None,
            "mean_marker_ms": 1000 * self.marker_seconds / self.frames_sampled if self.frames_sampled else None}


class UltralyticsByteTrack:
    """Lazy YOLO11n/ByteTrack adapter. Detection only includes COCO person class."""
    def __init__(self, model: str = "yolo11n.pt", confidence: float = 0.30, device: str | None = None):
        try:
            from ultralytics import YOLO
        except ImportError as error:
            raise RuntimeError("Install the optional Person 1 dependency: pip install -e '.[person1]'") from error
        self.model, self.confidence, self.device = YOLO(model), confidence, device

    def tracks(self, frame) -> list[Track]:
        result = self.model.track(frame, persist=True, tracker="bytetrack.yaml", classes=[0],
                                  conf=self.confidence, device=self.device, verbose=False)[0]
        if result.boxes is None or result.boxes.id is None:
            return []
        boxes = result.boxes.xyxy.cpu().tolist()
        ids = result.boxes.id.int().cpu().tolist()
        return [Track(track_id=track_id, bbox_xyxy=tuple(map(float, box))) for track_id, box in zip(ids, boxes)]


def process_video(source: str | Path, config: PipelineConfig, detector: DetectorTracker,
                  on_candidate: Callable[[dict], None] | None = None,
                  candidate_queue: queue.Queue | None = None) -> tuple[list[dict], PipelineMetrics]:
    """Stream a video. VLM work belongs to an external bounded queue/consumer."""
    try:
        import cv2
    except ImportError as error:
        raise RuntimeError("OpenCV is required for video ingestion") from error
    if config.sample_every < 1:
        raise ValueError("sample_every must be >= 1")
    capture = cv2.VideoCapture(str(source))
    if not capture.isOpened():
        raise FileNotFoundError(f"unable to open video source: {source}")
    fps = capture.get(cv2.CAP_PROP_FPS) or 30.0
    engine, metrics, packets, previous = MarkerEngine(config.camera), PipelineMetrics(), [], None
    started = time.perf_counter()
    try:
        while True:
            read_started = time.perf_counter(); ok, frame = capture.read(); metrics.read_seconds += time.perf_counter() - read_started
            if not ok:
                if metrics.frames_read == 0:
                    raise ValueError(f"video source produced no frames: {source}")
                break
            frame_index = metrics.frames_read; metrics.frames_read += 1
            if frame_index % config.sample_every:
                continue
            timestamp = frame_index / fps; metrics.frames_sampled += 1
            infer_started = time.perf_counter(); tracks = detector.tracks(frame); metrics.inference_seconds += time.perf_counter() - infer_started
            marker_started = time.perf_counter()
            events = engine.process_tracks(timestamp, tracks)
            events += engine.process_frame_observation(observe_frame(frame, timestamp, previous))
            previous = frame.copy()
            metrics.marker_seconds += time.perf_counter() - marker_started
            for event in events:
                packet = _save_and_packet(event, frame, config, cv2)
                _emit(packet, packets, metrics, config.max_candidates, on_candidate, candidate_queue)
    except Exception:
        # The source failure is an internal observation; do not hide original errors.
        raise
    finally:
        capture.release(); metrics.elapsed_seconds = time.perf_counter() - started
    return packets, metrics


def _save_and_packet(event, frame, config: PipelineConfig, cv2) -> dict:
    relative = Path("data") / "frames" / config.camera.camera_id / f"{event.event_id}.jpg"
    destination = config.output_root / config.camera.camera_id / f"{event.event_id}.jpg"
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(destination), frame):
        raise OSError(f"failed to write keyframe: {destination}")
    packet = to_candidate_packet(event, relative.as_posix())
    errors = validate_candidate_packet(packet)
    if errors:
        raise ValueError(f"internal candidate packet contract failure: {errors}")
    return packet


def _emit(packet: dict, packets: list[dict], metrics: PipelineMetrics, limit: int,
          callback: Callable[[dict], None] | None, candidate_queue: queue.Queue | None) -> None:
    if len(packets) >= limit:
        metrics.candidates_dropped += 1; return
    if candidate_queue is not None:
        try:
            candidate_queue.put_nowait(packet)
        except queue.Full:
            metrics.candidates_dropped += 1; return
    packets.append(packet); metrics.candidates_emitted += 1
    if callback is not None:
        callback(packet)


def write_jsonl(packets: list[dict], path: str | Path) -> None:
    target = Path(path); target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("".join(json.dumps(packet) + "\n" for packet in packets), encoding="utf-8")
