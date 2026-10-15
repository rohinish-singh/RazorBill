"""Narrow compatibility validation for the authoritative Person 1 candidate packet."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any


def validate_candidate_packet(packet: dict[str, Any]) -> list[str]:
    """Return validation errors without changing the shared contract or packet."""
    errors: list[str] = []
    for key in ("event_id", "camera_id", "video_source_id", "frame_path", "frame_paths", "tracks", "trigger", "created_at"):
        if key not in packet or packet[key] in (None, ""):
            errors.append(f"missing {key}")
    timestamp = packet.get("timestamp_seconds")
    if not isinstance(timestamp, (int, float)) or timestamp < 0:
        errors.append("timestamp_seconds must be a non-negative relative source-video number")
    for path_key in ("frame_path",):
        if packet.get(path_key) and Path(packet[path_key]).is_absolute():
            errors.append(f"{path_key} must be relative/configurable, not absolute")
    if not isinstance(packet.get("frame_paths", []), list):
        errors.append("frame_paths must be a list")
    elif any(not isinstance(path, str) or Path(path).is_absolute() for path in packet.get("frame_paths", [])):
        errors.append("frame_paths entries must be relative strings")
    if not isinstance(packet.get("tracks", []), list):
        errors.append("tracks must be a list")
    else:
        for index, track in enumerate(packet.get("tracks", [])):
            box = track.get("bbox_xyxy") if isinstance(track, dict) else None
            if not isinstance(track, dict) or track.get("track_id") is None:
                errors.append(f"tracks[{index}] needs track_id")
            if not isinstance(box, list) or len(box) != 4 or not all(isinstance(value, (int, float)) for value in box):
                errors.append(f"tracks[{index}].bbox_xyxy must contain four numbers")
            elif box[2] <= box[0] or box[3] <= box[1] or box[0] < 0 or box[1] < 0:
                errors.append(f"tracks[{index}].bbox_xyxy must be non-negative xyxy with x2>x1 and y2>y1")
    created = packet.get("created_at")
    if isinstance(created, str):
        try:
            datetime.fromisoformat(created.replace("Z", "+00:00"))
        except ValueError:
            errors.append("created_at must be ISO-8601")
    return errors
