from datetime import datetime
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field, field_validator


class Category(str, Enum):
    person_down = "person_down"
    fighting = "fighting"
    tailgating = "tailgating"
    crowd_incident = "crowd_incident"
    suspicious_activity = "suspicious_activity"
    other = "other"
    unknown = "unknown"


class Source(str, Enum):
    rule = "rule"
    vlm = "vlm"
    manual = "manual"


class Status(str, Enum):
    candidate = "candidate"
    classified = "classified"
    needs_review = "needs_review"
    failed = "failed"


class Track(BaseModel):
    track_id: int
    class_name: str
    bbox_xyxy: list[float] = Field(..., min_length=4, max_length=4)


def _validate_iso_timestamp(v: Any) -> str:
    if isinstance(v, datetime):
        if v.tzinfo is None:
            raise ValueError("created_at must include timezone information and be in UTC")
        if v.utcoffset() is None or v.utcoffset().total_seconds() != 0:
            raise ValueError("created_at must be in UTC (offset +00:00 or Z)")
        iso_str = v.isoformat()
        if iso_str.endswith("+00:00"):
            iso_str = iso_str[:-6] + "Z"
        return iso_str

    if not isinstance(v, str):
        raise ValueError("created_at must be an ISO 8601 UTC string or datetime")

    try:
        dt = datetime.fromisoformat(v.replace("Z", "+00:00"))
    except Exception as e:
        raise ValueError(f"created_at must be a valid ISO 8601 timestamp string: {e}")

    if dt.tzinfo is None:
        raise ValueError("created_at must include timezone information and be in UTC (e.g. ending in 'Z' or '+00:00')")

    if dt.utcoffset() is None or dt.utcoffset().total_seconds() != 0:
        raise ValueError("created_at must have a UTC offset (+00:00 or Z), non-UTC offsets are not permitted")

    return v


class CandidateEventPacket(BaseModel):
    event_id: str
    camera_id: str
    video_source_id: str
    timestamp_seconds: float = Field(..., ge=0.0)
    frame_path: str
    frame_paths: list[str] = Field(default_factory=list)
    tracks: list[Track] = Field(default_factory=list)
    trigger: str
    created_at: str

    @field_validator("created_at", mode="before")
    @classmethod
    def validate_created_at(cls, v: Any) -> str:
        return _validate_iso_timestamp(v)


class ClassifiedIncident(BaseModel):
    event_id: str
    camera_id: str
    timestamp_seconds: float = Field(..., ge=0.0)
    category: Category
    summary: str
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    confidence_type: Optional[str] = None
    frame_path: str
    source: Source
    processing_ms: Optional[int] = Field(default=None, ge=0)
    status: Status
    evidence_notes: Optional[str] = None
    created_at: str

    @field_validator("created_at", mode="before")
    @classmethod
    def validate_created_at(cls, v: Any) -> str:
        return _validate_iso_timestamp(v)

