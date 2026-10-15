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
