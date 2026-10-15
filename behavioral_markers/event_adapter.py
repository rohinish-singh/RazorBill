from __future__ import annotations

from datetime import datetime, timezone

from .schemas import MarkerEvent

def to_candidate_packet(event: MarkerEvent, frame_path: str = "") -> dict:
    """Map internal markers to the unchanged Person 1 → Person 2 packet shape."""
    tracks = [{"track_id": item.track_id, "class_name": item.class_name, "bbox_xyxy": list(item.bbox_xyxy)} for item in event.tracks]
    return {"event_id": event.event_id, "camera_id": event.camera_id, "video_source_id": event.video_source_id,
            "timestamp_seconds": event.timestamp_seconds, "frame_path": frame_path, "frame_paths": [], "tracks": tracks,
            "trigger": event.trigger, "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")}
