from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

@dataclass(frozen=True)
class Track:
    track_id: str | int
    bbox_xyxy: tuple[float, float, float, float]
    class_name: str = "person"

    @property
    def footpoint(self) -> tuple[float, float]:
        x1, _, x2, y2 = self.bbox_xyxy
        return ((x1 + x2) / 2, y2)

    @property
    def centre(self) -> tuple[float, float]:
        x1, y1, x2, y2 = self.bbox_xyxy
        return ((x1 + x2) / 2, (y1 + y2) / 2)


@dataclass(frozen=True)
class ObjectFlag:
    """A specialized detector observation; not a shared candidate-packet field."""
    label: str
    confidence: float
    bbox_xyxy: tuple[float, float, float, float]

@dataclass(frozen=True)
class PoseCue:
    """Internal, uncalibrated pose geometry associated to a Person 1 track."""
    track_id: str | int
    posture_ratio: float
    confident_keypoint_count: int

@dataclass(frozen=True)
class ZoneConfig:
    zone_id: str
    polygon: tuple[tuple[float, float], ...]
    restricted: bool = False
    loiter_seconds: float = 30.0
    min_observations: int = 3
    crowd_threshold: int = 5
    crowd_persist_seconds: float = 5.0
    cooldown_seconds: float = 30.0


@dataclass(frozen=True)
class IncidentConfig:
    """Conservative Person 1 candidate cues, disabled unless explicitly configured."""
    enabled: bool = False
    cooldown_seconds: float = 30.0
    person_down_aspect_ratio: float = 1.25
    person_down_persist_seconds: float = 1.0
    person_down_gap_tolerance_seconds: float = 0.0
    pose_enabled: bool = False
    pose_down_ratio: float = 1.10
    pose_down_persist_seconds: float = 0.25
    fighting_pair_distance: float = 160.0
    fighting_motion_pixels_per_second: float = 250.0
    fighting_persist_seconds: float = 1.0
    object_confidence_threshold: float = 0.50

@dataclass(frozen=True)
class CameraConfig:
    camera_id: str
    video_source_id: str
    zones: tuple[ZoneConfig, ...] = ()
    darkness_mean_threshold: float = 25.0
    darkness_drop: float = 40.0
    health_persist_seconds: float = 2.0
    freeze_mad_threshold: float = 1.0
    freeze_persist_seconds: float = 3.0
    obstruction_sharpness_threshold: float = 5.0
    obstruction_texture_threshold: float = 3.0
    incident: IncidentConfig = IncidentConfig()

@dataclass(frozen=True)
class MarkerEvent:
    event_id: str
    camera_id: str
    video_source_id: str
    timestamp_seconds: float
    marker_type: str
    category: str
    status: str
    trigger: str
    evidence: dict[str, Any]
    tracks: tuple[Track, ...] = ()
