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


def normalize_boundary(val: str, is_end: bool = False) -> str:
    """Normalize and validate a date/time boundary string to ISO 8601 UTC format.

    - Date-only input ('YYYY-MM-DD'):
        - start (is_end=False) -> 'YYYY-MM-DDT00:00:00Z'
        - end (is_end=True) -> 'YYYY-MM-DDT23:59:59.999999Z' (inclusive of entire day)
    - ISO datetime input ('YYYY-MM-DDTHH:MM:SSZ'):
        - Validated as strict UTC ISO timestamp using _validate_iso_timestamp.
    """
    if not isinstance(val, str) or not val.strip():
        raise ValueError("Timestamp boundary must be a non-empty string")
    clean_val = val.strip()

    # Check for date-only format (YYYY-MM-DD)
    if len(clean_val) == 10 and clean_val.count("-") == 2:
        try:
            datetime.strptime(clean_val, "%Y-%m-%d")
        except ValueError as e:
            raise ValueError(f"Invalid date format: {e}")
        return f"{clean_val}T23:59:59.999999Z" if is_end else f"{clean_val}T00:00:00Z"

    # Full ISO datetime string: enforce strict UTC format
    return _validate_iso_timestamp(clean_val)


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


class IncidentListResponse(BaseModel):
    items: list[ClassifiedIncident]
    total: int = Field(..., ge=0)
    limit: int = Field(..., ge=1, le=100)
    offset: int = Field(..., ge=0)


class StatsResponse(BaseModel):
    total: int = Field(..., ge=0, description="Total incident count")
    by_category: dict[str, int] = Field(..., description="Incident counts grouped by canonical category")
    by_status: dict[str, int] = Field(..., description="Incident counts grouped by canonical status")
    by_camera: dict[str, int] = Field(..., description="Incident counts grouped by camera ID")
    recent_activity_count: int = Field(..., ge=0, description="Number of incidents in the last 24 hours")


class QueryRequest(BaseModel):
    question: str = Field(..., description="Natural language question about stored incidents")


class QueryResponse(BaseModel):
    question: str = Field(..., description="Original user question")
    interpreted_filters: dict[str, Any] = Field(default_factory=dict, description="Parsed structured query filters")
    answer: str = Field(..., description="Evidence-backed natural-language summary answer")
    incidents: list[ClassifiedIncident] = Field(default_factory=list, description="Matching incident records")
    status: str = Field(default="success", description="Query resolution status: success or unsupported_query")
