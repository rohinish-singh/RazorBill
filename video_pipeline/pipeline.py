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
from behavioral_markers.schemas import CameraConfig, ObjectFlag, TemporalActionCue, Track
from .pose import PoseEstimator, associate_pose_cues
from .evidence import EvidenceBuffer
from .action import SlidingWindowActionAdapter
from .weapons import WeaponTemporalFilter
from datasets_incident_detection.contracts import validate_candidate_packet


class DetectorTracker(Protocol):
    def tracks(self, frame) -> list[Track]: ...


class ObjectFlagDetector(Protocol):
    def flags(self, frame) -> list[ObjectFlag]: ...


@dataclass(frozen=True)
class PipelineConfig:
    camera: CameraConfig
    sample_every: int = 3
    output_root: Path = Path("data/frames")
    relative_frame_root: Path = Path("data/frames")
    confidence: float = 0.30
    device: str | None = None
    max_candidates: int = 128
    pose_every: int = 1
    evidence_pre_seconds: float = 0.0
    evidence_post_seconds: float = 0.0
    evidence_root: Path | None = None
    relative_evidence_root: Path | None = None
    object_every: int = 1


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
    frames_with_people: int = 0
    person_detections: int = 0
    track_continuity_hits: int = 0
    gpu_peak_allocated_mib: float | None = None
    gpu_peak_reserved_mib: float | None = None
    max_person_bbox_aspect_ratio: float = 0.0
    frames_meeting_person_down_geometry: int = 0
    track_id_appearances: int = 0
    track_id_disappearances: int = 0
    person_down_diagnostics: dict = field(default_factory=dict)
    pose_observations: int = 0
    pose_matched_tracks: int = 0
    pose_inference_seconds: float = 0.0
    max_pose_posture_ratio: float = 0.0
    frames_meeting_pose_down_geometry: int = 0
    evidence_clips_written: int = 0
    temporal_windows: int = 0
    temporal_inference_seconds: float = 0.0
    temporal_fighting_windows: int = 0
    object_detections: int = 0
    object_inference_seconds: float = 0.0
    weapon_confirmed_observations: int = 0
    _track_ids: set[str] = field(default_factory=set, repr=False)

    def as_dict(self) -> dict:
        sampled_fps = self.frames_sampled / self.elapsed_seconds if self.elapsed_seconds else 0.0
        return {key: value for key, value in self.__dict__.items() if key != "_track_ids"} | {"sampled_fps": sampled_fps,
            "frames_skipped_by_sampling": self.frames_read - self.frames_sampled,
            "distinct_track_ids": len(self._track_ids),
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


class UltralyticsObjectFlagDetector:
    """Optional adapter for an explicitly supplied knife/firearm-trained model.

    COCO weights must not be passed here: class-to-label mapping is explicit so a
    generic detector cannot silently be treated as a weapon detector.
    """
    def __init__(self, model: str, labels_by_class: dict[int, str], confidence: float = 0.50, device: str | None = None):
        if not labels_by_class or not set(labels_by_class.values()) <= {"knife", "firearm"}:
            raise ValueError("weapon labels must explicitly map class IDs to knife or firearm")
        try:
            from ultralytics import YOLO
        except ImportError as error:
            raise RuntimeError("Install the optional Person 1 dependency: pip install -e '.[person1]'") from error
        self.model, self.labels_by_class, self.confidence, self.device = YOLO(model), labels_by_class, confidence, device

    def flags(self, frame) -> list[ObjectFlag]:
        result = self.model.predict(frame, conf=self.confidence, device=self.device, verbose=False)[0]
        if result.boxes is None:
            return []
        boxes = result.boxes.xyxy.cpu().tolist(); classes = result.boxes.cls.int().cpu().tolist(); confidences = result.boxes.conf.cpu().tolist()
        return [ObjectFlag(self.labels_by_class[class_id], float(confidence), tuple(map(float, box)))
                for box, class_id, confidence in zip(boxes, classes, confidences) if class_id in self.labels_by_class]


def process_video(source: str | Path, config: PipelineConfig, detector: DetectorTracker,
                  on_candidate: Callable[[dict], None] | None = None,
                  candidate_queue: queue.Queue | None = None,
                  object_detector: ObjectFlagDetector | None = None,
                  pose_estimator: PoseEstimator | None = None,
                  action_adapter: SlidingWindowActionAdapter | None = None,
                  weapon_filter: WeaponTemporalFilter | None = None) -> tuple[list[dict], PipelineMetrics]:
    """Stream a video. VLM work belongs to an external bounded queue/consumer."""
    try:
        import cv2
    except ImportError as error:
        raise RuntimeError("OpenCV is required for video ingestion") from error
    if config.sample_every < 1:
        raise ValueError("sample_every must be >= 1")
    if config.pose_every < 1:
        raise ValueError("pose_every must be >= 1")
    if config.object_every < 1:
        raise ValueError("object_every must be >= 1")
    if config.evidence_pre_seconds < 0 or config.evidence_post_seconds < 0:
        raise ValueError("evidence durations must be non-negative")
    capture = cv2.VideoCapture(str(source))
    if not capture.isOpened():
        raise FileNotFoundError(f"unable to open video source: {source}")
    fps = capture.get(cv2.CAP_PROP_FPS) or 30.0
    engine, metrics, packets, previous, previous_track_ids = MarkerEngine(config.camera), PipelineMetrics(), [], None, set()
    evidence = EvidenceBuffer(config.evidence_pre_seconds, config.evidence_post_seconds, fps / config.sample_every) if config.evidence_root else None
    _reset_cuda_peak_memory(config.device)
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
            if evidence is not None:
                evidence.add(timestamp, frame)
            _synchronize_cuda(config.device)
            infer_started = time.perf_counter(); tracks = detector.tracks(frame); _synchronize_cuda(config.device)
            metrics.inference_seconds += time.perf_counter() - infer_started
            current_track_ids = {str(track.track_id) for track in tracks}
            metrics.track_id_appearances += len(current_track_ids - previous_track_ids)
            metrics.track_id_disappearances += len(previous_track_ids - current_track_ids)
            metrics.person_detections += len(tracks)
            metrics.frames_with_people += int(bool(tracks))
            aspects = [(track.bbox_xyxy[2] - track.bbox_xyxy[0]) / max(track.bbox_xyxy[3] - track.bbox_xyxy[1], 1e-6) for track in tracks]
            if aspects:
                metrics.max_person_bbox_aspect_ratio = max(metrics.max_person_bbox_aspect_ratio, max(aspects))
            metrics.frames_meeting_person_down_geometry += int(any(aspect >= config.camera.incident.person_down_aspect_ratio for aspect in aspects))
            metrics.track_continuity_hits += len(previous_track_ids & current_track_ids)
            metrics._track_ids.update(current_track_ids); previous_track_ids = current_track_ids
            marker_started = time.perf_counter()
            events = engine.process_tracks(timestamp, tracks)
            object_flags = []
            if object_detector is not None:
                if frame_index % (config.sample_every * config.object_every) == 0:
                    _synchronize_cuda(config.device)
                    object_started = time.perf_counter(); raw_flags = object_detector.flags(frame); _synchronize_cuda(config.device)
                    metrics.object_inference_seconds += time.perf_counter() - object_started; metrics.object_detections += len(raw_flags)
                    object_flags = weapon_filter.observe(timestamp, raw_flags, frame) if weapon_filter is not None else raw_flags
                elif weapon_filter is not None:
                    object_flags = weapon_filter.confirmed(timestamp)
                metrics.weapon_confirmed_observations += len(object_flags)
            pose_cues = []
            if pose_estimator is not None and frame_index % (config.sample_every * config.pose_every) == 0:
                pose_started = time.perf_counter(); poses = pose_estimator.poses(frame); metrics.pose_inference_seconds += time.perf_counter() - pose_started
                pose_cues = associate_pose_cues(tracks, poses); metrics.pose_observations += len(poses); metrics.pose_matched_tracks += len(pose_cues)
                if pose_cues:
                    metrics.max_pose_posture_ratio = max(metrics.max_pose_posture_ratio, max(cue.posture_ratio for cue in pose_cues))
                metrics.frames_meeting_pose_down_geometry += int(any(cue.posture_ratio >= config.camera.incident.pose_down_ratio for cue in pose_cues))
            action_cues = None
            if action_adapter is not None:
                _synchronize_cuda(config.device)
                action_started = time.perf_counter(); observation = action_adapter.observe(timestamp, frame); _synchronize_cuda(config.device)
                metrics.temporal_inference_seconds += time.perf_counter() - action_started
                if observation is not None:
                    metrics.temporal_windows += 1
                    action_cues = [TemporalActionCue(observation.label, observation.score, observation.start_seconds,
                                                     observation.end_seconds, observation.class_scores, observation.model_id)]
                    metrics.temporal_fighting_windows += int(observation.label == config.camera.incident.temporal_fighting_label)
            events += engine.process_incidents(timestamp, tracks, object_flags, pose_cues, action_cues)
            events += engine.process_frame_observation(observe_frame(frame, timestamp, previous))
            previous = frame.copy()
            metrics.marker_seconds += time.perf_counter() - marker_started
            for event in events:
                event_frame = frame
                if event.marker_type in {"weapon_knife_candidate", "weapon_firearm_candidate"}:
                    matching = next((flag for flag in object_flags if flag.label == event.evidence.get("object_label") and flag.support_frame is not None), None)
                    if matching is not None:
                        event_frame = matching.support_frame
                packet = _save_and_packet(event, event_frame, config, cv2)
                if evidence is not None:
                    evidence.register(event.event_id, timestamp)
                _emit(packet, packets, metrics, config.max_candidates, on_candidate, candidate_queue)
    except Exception:
        # The source failure is an internal observation; do not hide original errors.
        raise
    finally:
        capture.release(); metrics.elapsed_seconds = time.perf_counter() - started
        metrics.person_down_diagnostics = engine.person_down_diagnostics()
        if evidence is not None and config.evidence_root is not None:
            index = evidence.write(config.evidence_root, config.relative_evidence_root or config.evidence_root, cv2)
            metrics.evidence_clips_written = len(index)
        _record_cuda_peak_memory(metrics, config.device)
    return packets, metrics


def _save_and_packet(event, frame, config: PipelineConfig, cv2) -> dict:
    relative = config.relative_frame_root / config.camera.camera_id / f"{event.event_id}.jpg"
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


def _cuda_available_for(device: str | None) -> bool:
    if device is None or str(device).lower() == "cpu":
        return False
    try:
        import torch
        return bool(torch.cuda.is_available())
    except ImportError:
        return False


def _synchronize_cuda(device: str | None) -> None:
    if _cuda_available_for(device):
        import torch
        torch.cuda.synchronize()


def _reset_cuda_peak_memory(device: str | None) -> None:
    if _cuda_available_for(device):
        import torch
        torch.cuda.reset_peak_memory_stats()


def _record_cuda_peak_memory(metrics: PipelineMetrics, device: str | None) -> None:
    if _cuda_available_for(device):
        import torch
        metrics.gpu_peak_allocated_mib = round(torch.cuda.max_memory_allocated() / 1024 / 1024, 2)
        metrics.gpu_peak_reserved_mib = round(torch.cuda.max_memory_reserved() / 1024 / 1024, 2)
