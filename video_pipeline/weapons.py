"""Optional verified gun/knife detector and bounded temporal confirmation."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from behavioral_markers.schemas import ObjectFlag


def validate_weapon_class_names(names: dict[int, str]) -> dict[int, str]:
    normalized = {int(index): str(name).strip().lower() for index, name in names.items()}
    expected = UltralyticsGunKnifeDetector.EXPECTED_CLASS_NAMES
    if normalized != expected:
        raise ValueError(f"weapon model class mapping must be {expected}, got {normalized}")
    return normalized


class WeaponDetector(Protocol):
    def flags(self, frame) -> list[ObjectFlag]: ...


class UltralyticsGunKnifeDetector:
    """Adapter for the audited cosgun99 YOLO11n checkpoint only.

    Checkpoint classes are verified at load time rather than accepted from CLI
    strings. Ultralytics/framework licensing remains separate from checkpoint
    metadata and must be resolved before deployment.
    """
    EXPECTED_CLASS_NAMES = {0: "gun", 1: "knife"}
    LABEL_BY_CLASS = {0: "firearm", 1: "knife"}

    def __init__(self, model: str, confidence: float = 0.50, imgsz: int = 640, device: str | None = None):
        if not model:
            raise ValueError("weapon model path is required")
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("weapon confidence must be between 0 and 1")
        if imgsz < 32:
            raise ValueError("weapon imgsz must be at least 32")
        try:
            from pathlib import Path
            from ultralytics import YOLO
        except ImportError as error:
            raise RuntimeError("Install the optional Person 1 dependency: pip install -e '.[person1]'") from error
        path = Path(model)
        if not path.is_file():
            raise FileNotFoundError(f"weapon model weights not found: {path}")
        self.model, self.confidence, self.imgsz, self.device = YOLO(str(path)), confidence, imgsz, device
        validate_weapon_class_names(self.model.names)

    def flags(self, frame) -> list[ObjectFlag]:
        result = self.model.predict(frame, conf=self.confidence, imgsz=self.imgsz, device=self.device, verbose=False)[0]
        if result.boxes is None:
            return []
        return [ObjectFlag(self.LABEL_BY_CLASS[int(class_id)], float(score), tuple(map(float, box)),
                           class_id=int(class_id), class_name=self.EXPECTED_CLASS_NAMES[int(class_id)])
                for box, class_id, score in zip(result.boxes.xyxy.cpu().tolist(), result.boxes.cls.int().cpu().tolist(),
                                                result.boxes.conf.cpu().tolist())
                if int(class_id) in self.LABEL_BY_CLASS]


@dataclass
class _Episode:
    flag: ObjectFlag
    first_timestamp: float
    last_timestamp: float
    strongest_timestamp: float
    observations: int = 1
    strongest_frame: object | None = None


class WeaponTemporalFilter:
    """Confirm repeated spatially associated observations without unbounded state."""

    def __init__(self, min_observations: int = 2, max_gap_seconds: float = 0.5, min_iou: float = 0.10):
        if min_observations < 1:
            raise ValueError("weapon minimum observations must be at least 1")
        if max_gap_seconds < 0:
            raise ValueError("weapon maximum gap must be non-negative")
        if not 0 <= min_iou <= 1:
            raise ValueError("weapon IoU must be between 0 and 1")
        self.min_observations, self.max_gap_seconds, self.min_iou = min_observations, max_gap_seconds, min_iou
        self._episodes: list[_Episode] = []

    def observe(self, timestamp_seconds: float, flags: list[ObjectFlag], frame) -> list[ObjectFlag]:
        self._episodes = [episode for episode in self._episodes if timestamp_seconds - episode.last_timestamp <= self.max_gap_seconds]
        matched = set()
        for flag in flags:
            candidates = [(index, episode) for index, episode in enumerate(self._episodes)
                          if index not in matched and episode.flag.label == flag.label
                          and _iou(episode.flag.bbox_xyxy, flag.bbox_xyxy) >= self.min_iou]
            if candidates:
                index, episode = max(candidates, key=lambda item: _iou(item[1].flag.bbox_xyxy, flag.bbox_xyxy))
                matched.add(index); episode.last_timestamp = timestamp_seconds; episode.observations += 1
                if flag.confidence >= episode.flag.confidence:
                    episode.flag = flag; episode.strongest_timestamp = timestamp_seconds; episode.strongest_frame = frame.copy()
            else:
                self._episodes.append(_Episode(flag, timestamp_seconds, timestamp_seconds, timestamp_seconds,
                                                strongest_frame=frame.copy()))
        return self.confirmed(timestamp_seconds)

    def confirmed(self, timestamp_seconds: float) -> list[ObjectFlag]:
        self._episodes = [episode for episode in self._episodes if timestamp_seconds - episode.last_timestamp <= self.max_gap_seconds]
        return [ObjectFlag(episode.flag.label, episode.flag.confidence, episode.flag.bbox_xyxy, episode.flag.class_id,
                           episode.flag.class_name, episode.first_timestamp, episode.strongest_timestamp,
                           episode.observations, episode.strongest_frame)
                for episode in self._episodes if episode.observations >= self.min_observations
                and timestamp_seconds - episode.last_timestamp <= self.max_gap_seconds]


def _iou(first: tuple[float, float, float, float], second: tuple[float, float, float, float]) -> float:
    left, top = max(first[0], second[0]), max(first[1], second[1])
    right, bottom = min(first[2], second[2]), min(first[3], second[3])
    intersection = max(0.0, right - left) * max(0.0, bottom - top)
    if not intersection:
        return 0.0
    first_area = max(0.0, first[2] - first[0]) * max(0.0, first[3] - first[1])
    second_area = max(0.0, second[2] - second[0]) * max(0.0, second[3] - second[1])
    return intersection / max(first_area + second_area - intersection, 1e-6)
