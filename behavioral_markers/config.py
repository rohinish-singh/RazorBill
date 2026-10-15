from __future__ import annotations

from .schemas import CameraConfig, ZoneConfig

def camera_config_from_dict(value: dict) -> CameraConfig:
    zones = tuple(ZoneConfig(zone_id=item["zone_id"], polygon=tuple(tuple(point) for point in item["polygon"]), **{key: item[key] for key in ("restricted", "loiter_seconds", "min_observations", "crowd_threshold", "crowd_persist_seconds", "cooldown_seconds") if key in item}) for item in value.get("zones", []))
    fields = {key: value[key] for key in CameraConfig.__dataclass_fields__ if key in value and key != "zones"}
    return CameraConfig(zones=zones, **fields)
