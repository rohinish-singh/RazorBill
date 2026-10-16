import json
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
import httpx
from pydantic import BaseModel, Field, field_validator
from .schemas import ClassifiedIncident, Category
from .database import query_incidents

WORD_TO_DIGIT = {
    "zero": "00",
    "one": "01",
    "two": "02",
    "three": "03",
    "four": "04",
    "five": "05",
    "six": "06",
    "seven": "07",
    "eight": "08",
    "nine": "09",
    "ten": "10",
    "eleven": "11",
    "twelve": "12",
}

VALID_CATEGORIES = {c.value for c in Category}

# Ordered from multi-word specific phrases to single words
CATEGORY_SYNONYMS: List[Tuple[str, str]] = [
    # person_down
    ("medical emergency", "person_down"),
    ("lying on floor", "person_down"),
    ("lying on ground", "person_down"),
    ("fallen person", "person_down"),
    ("person down", "person_down"),
    ("man down", "person_down"),
    ("passed out", "person_down"),
    ("unconscious", "person_down"),
    ("collapsed", "person_down"),
    ("collapse", "person_down"),
    ("fainted", "person_down"),
    ("fallen", "person_down"),
    ("tripped", "person_down"),
    ("fall", "person_down"),
    ("slip", "person_down"),

    # fighting
    ("physical confrontation", "fighting"),
    ("physical violence", "fighting"),
    ("altercation", "fighting"),
    ("punching", "fighting"),
    ("grappling", "fighting"),
    ("assault", "fighting"),
    ("scuffle", "fighting"),
    ("brawl", "fighting"),
    ("fighting", "fighting"),
    ("fight", "fighting"),

    # tailgating
    ("followed through turnstile", "tailgating"),
    ("unauthorized entry", "tailgating"),
    ("gate jumping", "tailgating"),
    ("piggybacking", "tailgating"),
    ("piggyback", "tailgating"),
    ("turnstile bypass", "tailgating"),
    ("tailgating", "tailgating"),
    ("tailgate", "tailgating"),

    # suspicious_activity
    ("suspicious activity", "suspicious_activity"),
    ("unauthorized access", "suspicious_activity"),
    ("trespassing", "suspicious_activity"),
    ("trespass", "suspicious_activity"),
    ("loitering", "suspicious_activity"),
    ("tampering", "suspicious_activity"),
    ("prowling", "suspicious_activity"),
    ("lingering", "suspicious_activity"),
    ("intruder", "suspicious_activity"),
    ("suspicious", "suspicious_activity"),

    # crowd_incident
    ("crowd incident", "crowd_incident"),
    ("large group", "crowd_incident"),
    ("gathering", "crowd_incident"),
    ("stampede", "crowd_incident"),
    ("congestion", "crowd_incident"),
    ("surging", "crowd_incident"),
    ("crowd", "crowd_incident"),
    ("mob", "crowd_incident"),
]

NEGATION_REGEX = re.compile(
    r"\b(?:not|no|except|excluding|exclude|other\s+than|without|aside\s+from|apart\s+from)\b",
    re.IGNORECASE,
)

TEMPORAL_CUES_REGEX = re.compile(
    r"\b(?:today|yesterday|tomorrow|week|month|year|hour|hours|hr|hrs|min|mins|minute|minutes|second|seconds|sec|secs|latest|recent|recently|last|past|since|between|from|before|after|ago|now|am|pm|\d{1,2}:\d{2}|\d{4}-\d{2}-\d{2})\b",
    re.IGNORECASE,
)


class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)
    limit: Optional[int] = Field(default=50, ge=1, le=100)
    offset: Optional[int] = Field(default=0, ge=0)

    @field_validator("question")
    @classmethod
    def sanitize_question(cls, v: str) -> str:
        # Strip ASCII control characters and unicode zero-width / invisible formatting characters
        sanitized = re.sub(r"[\x00-\x1f\x7f-\x9f\u200b-\u200f\u2028-\u202f\ufeff]", " ", v)
        sanitized = re.sub(r"\s+", " ", sanitized).strip()
        if not sanitized:
            raise ValueError("Question cannot be empty or solely whitespace.")
        return sanitized


class InterpretedFilters(BaseModel):
    camera_id: Optional[str] = None
    camera_ids: Optional[List[str]] = None
    category: Optional[str] = None
    exclude_category: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None


class QueryResponse(BaseModel):
    question: str
    interpreted_filters: Dict[str, Any]
    answer: str
    incidents: List[ClassifiedIncident] = []


def normalize_camera_ids(text: str) -> List[str]:
    """Deterministically extracts and normalizes camera IDs from query text.
    Handles 'camera 2', 'cam 2', 'CAM-02', 'camera two', 'cameras 1 and 2',
    ranges like 'cameras 1 to 3', 'cams 2-4', and suppresses generic camera terms.
    """
    found: set[str] = set()
    lower_text = text.lower()

    # 1. Camera ranges: "cameras 1 to 3", "cameras 1 through 4", "cams 2-4", "camera 1 - 3"
    range_matches = re.findall(
        r"\b(?:cameras?|cams?)\s+(\d+)\s*(?:to|through|-)\s*(\d+)\b",
        lower_text,
    )
    for start_s, end_s in range_matches:
        start_d, end_d = int(start_s), int(end_s)
        if 1 <= start_d <= end_d and (end_d - start_d) <= 20:
            for d in range(start_d, end_d + 1):
                found.add(f"CAM_{d:02d}")

    # 2. Multi-camera patterns: e.g. "cameras 1 and 2", "cams 1, 2 and 3"
    multi_cam_matches = re.findall(r"\b(?:cameras?|cams?)\s+([0-9\s,and&]+)\b", lower_text)
    for group in multi_cam_matches:
        digits = re.findall(r"\b\d+\b", group)
        for d in digits:
            d_int = int(d)
            if 1 <= d_int <= 99:
                found.add(f"CAM_{d_int:02d}")

    # 3. Numbered camera: "camera 2", "camera 02", "cam-02", "cam_2", "cam2", "CAM01"
    single_matches = re.findall(r"\b(?:camera|cam)[-_ ]*(\d+)\b", lower_text)
    for num in single_matches:
        num_int = int(num)
        if 1 <= num_int <= 99:
            found.add(f"CAM_{num_int:02d}")

    # 4. Word-based camera: "camera two", "cam one"
    for word, digit in WORD_TO_DIGIT.items():
        if re.search(rf"\b(?:camera|cam)[-_ ]+{word}\b", lower_text):
            found.add(f"CAM_{digit}")

    return sorted(list(found))


def parse_temporal_filters(text: str, now: Optional[datetime] = None) -> tuple[Optional[datetime], Optional[datetime]]:
    """Resolves relative date/time expressions to explicit UTC datetime intervals.
    Supports minute, hourly, daily, calendar lookbacks, and explicit date/ISO strings.
    Prevents future queries and inverted time bounds.
    """
    current_utc = now or datetime.now(timezone.utc)
    lower = text.lower()

    # 1. Guard against purely future queries
    if re.search(r"\b(?:tomorrow|next\s+hour|next\s+day|next\s+week|next\s+month|in\s+the\s+next|in\s+future|upcoming)\b", lower):
        return None, None

    # 2. Explicit date ranges: "from 2026-10-13 to 2026-10-15", "2026-10-13 - 2026-10-15"
    date_range_match = re.search(r"\b(\d{4}-\d{2}-\d{2})\s*(?:to|through|until|--|-)\s*(\d{4}-\d{2}-\d{2})\b", lower)
    if date_range_match:
        try:
            d1 = datetime.strptime(date_range_match.group(1), "%Y-%m-%d").replace(tzinfo=timezone.utc)
            d2 = datetime.strptime(date_range_match.group(2), "%Y-%m-%d").replace(
                hour=23, minute=59, second=59, microsecond=999999, tzinfo=timezone.utc
            )
            if d1 <= d2:
                return d1, d2
            else:
                return d2, d1
        except ValueError:
            pass

    # 3. Explicit single date: "on 2026-10-15", "for 2026-10-15", "2026-10-15"
    single_date_match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", lower)
    if single_date_match:
        try:
            d = datetime.strptime(single_date_match.group(1), "%Y-%m-%d").replace(tzinfo=timezone.utc)
            end_d = d.replace(hour=23, minute=59, second=59, microsecond=999999)
            return d, end_d
        except ValueError:
            pass

    # 4. Minute granularity: "last 15 minutes", "last 45 mins", "past 10 min"
    mins_match = re.search(r"\b(?:last|past|in the last|in the past)\s+(\d+)\s*(?:mins?|minutes?)\b", lower)
    if mins_match:
        mins = int(mins_match.group(1))
        return current_utc - timedelta(minutes=mins), current_utc

    # 5. Hourly lookbacks: "last 3 hours", "past 1 hour", "last 24 hours"
    hours_match = re.search(r"\b(?:last|past|in the last|in the past)\s+(\d+)\s*hours?\b", lower)
    if hours_match:
        hrs = int(hours_match.group(1))
        return current_utc - timedelta(hours=hrs), current_utc

    # 6. Multi-day lookbacks: "last 2 days", "past 3 days"
    days_match = re.search(r"\b(?:last|past|in the last|in the past)\s+(\d+)\s*days?\b", lower)
    if days_match:
        days = int(days_match.group(1))
        return current_utc - timedelta(days=days), current_utc

    # 7. "this week" -> Monday 00:00:00 UTC of current week to now
    if re.search(r"\b(?:this\s+week|past\s+week)\b", lower):
        start_of_week = datetime(
            current_utc.year, current_utc.month, current_utc.day, 0, 0, 0, tzinfo=timezone.utc
        ) - timedelta(days=current_utc.weekday())
        return start_of_week, current_utc

    # 8. "today" -> start of today 00:00:00 UTC
    if "today" in lower:
        start_of_day = datetime(current_utc.year, current_utc.month, current_utc.day, 0, 0, 0, tzinfo=timezone.utc)
        return start_of_day, None

    # 9. "yesterday" -> yesterday 00:00:00 to 23:59:59.999999 UTC
    if "yesterday" in lower:
        start_yesterday = datetime(
            current_utc.year, current_utc.month, current_utc.day, 0, 0, 0, tzinfo=timezone.utc
        ) - timedelta(days=1)
        end_yesterday = start_yesterday + timedelta(days=1, microseconds=-1)
        return start_yesterday, end_yesterday

    return None, None


def extract_category_and_negation(text: str) -> tuple[Optional[str], Optional[str]]:
    """Extracts target category and checks whether it appears in a negated/exclusion context.
    Normalizes punctuation and hyphens so 'Person-Down', 'crowd-incident', etc. match cleanly.
    Returns: (positive_category, excluded_category)
    """
    lower = text.lower()
    clean_text = re.sub(r"[-_]+", " ", lower)

    for phrase, cat in CATEGORY_SYNONYMS:
        match = re.search(rf"\b{re.escape(phrase)}\b", clean_text)
        if match:
            start_pos = match.start()
            # Inspect preceding text window (up to 40 characters before match)
            window_start = max(0, start_pos - 40)
            preceding_context = clean_text[window_start:start_pos]

            if NEGATION_REGEX.search(preceding_context):
                return None, cat
            else:
                return cat, None

    return None, None


def extract_category_regex(text: str) -> Optional[str]:
    """Backwards-compatible helper returning positive category match or None."""
    cat, _ = extract_category_and_negation(text)
    return cat


SYSTEM_PROMPT = """You are a specialized security video surveillance assistant.
Extract search filters from the user question into strict JSON.
Available Categories: person_down, fighting, tailgating, crowd_incident, suspicious_activity, other, unknown.
Current UTC time: {current_time}

Rules:
1. "camera_id": Canonical camera ID (e.g., "CAM_01", "CAM_02") or null.
2. "category": Exact match from Available Categories if a specific incident type is requested, otherwise null. Do NOT output "other" or "unknown" unless the user explicitly asks for other or unknown incidents.
3. "exclude_category": If user asks to exclude or negate a category (e.g. "not fighting"), set this and set category to null.
4. "start_time": ISO 8601 UTC timestamp or null. Only set if the user explicitly specifies a temporal window; otherwise set to null. Do NOT default to current time.
5. "end_time": ISO 8601 UTC timestamp or null. Only set if user specifies an ending time constraint; otherwise set to null.

Respond ONLY with valid JSON in this schema:
{{
  "camera_id": string or null,
  "category": string or null,
  "exclude_category": string or null,
  "start_time": string or null,
  "end_time": string or null
}}"""


async def extract_filters_with_ollama(question: str) -> InterpretedFilters:
    """Interprets user question into structured filters using Ollama with deterministic fallback."""
    now_utc = datetime.now(timezone.utc)
    current_time_str = now_utc.isoformat().replace("+00:00", "Z")

    # 1. Deterministic baseline extractions
    det_cams = normalize_camera_ids(question)
    det_cat, det_exclude = extract_category_and_negation(question)
    det_start, det_end = parse_temporal_filters(question, now=now_utc)

    extracted_cam = det_cams[0] if len(det_cams) == 1 else None
    extracted_cams = det_cams if len(det_cams) > 1 else None
    extracted_cat = det_cat
    extracted_exclude = det_exclude
    start_iso = det_start.isoformat().replace("+00:00", "Z") if det_start else None
    end_iso = det_end.isoformat().replace("+00:00", "Z") if det_end else None

    # 2. Prompt Ollama with strict JSON mode & 30.0s timeout
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "llama3.2:1b",
                    "prompt": f"{SYSTEM_PROMPT.format(current_time=current_time_str)}\nUser Question: {question}\nJSON:",
                    "format": "json",
                    "stream": False,
                },
            )
            if resp.status_code == 200:
                raw_text = resp.json().get("response", "").strip()
                parsed = json.loads(raw_text)

                # Camera ID fallback
                if not extracted_cam and not extracted_cams:
                    model_cam = parsed.get("camera_id")
                    if model_cam and isinstance(model_cam, str):
                        normalized = normalize_camera_ids(model_cam)
                        if len(normalized) == 1:
                            extracted_cam = normalized[0]
                        elif len(normalized) > 1:
                            extracted_cams = normalized

                # Category fallback (only if not deterministically excluded)
                if not extracted_cat and not extracted_exclude:
                    model_cat = parsed.get("category")
                    if model_cat and model_cat in VALID_CATEGORIES:
                        if model_cat in ("other", "unknown"):
                            if model_cat in question.lower():
                                extracted_cat = model_cat
                        else:
                            extracted_cat = model_cat

                if not extracted_exclude:
                    model_exclude = parsed.get("exclude_category")
                    if model_exclude and model_exclude in VALID_CATEGORIES:
                        extracted_exclude = model_exclude
                        extracted_cat = None

                # Timestamps fallback (only if query contains explicit temporal cues and not future-oriented)
                is_future = bool(re.search(r"\b(?:tomorrow|next\s+hour|next\s+day|next\s+week|next\s+month|in\s+the\s+next|in\s+future|upcoming)\b", question.lower()))
                if TEMPORAL_CUES_REGEX.search(question) and not is_future:
                    if not start_iso and parsed.get("start_time"):
                        try:
                            dt_s = datetime.fromisoformat(str(parsed["start_time"]).replace("Z", "+00:00"))
                            if dt_s <= now_utc:
                                start_iso = str(parsed["start_time"])
                        except Exception:
                            pass

                    if not end_iso and parsed.get("end_time"):
                        try:
                            dt_e = datetime.fromisoformat(str(parsed["end_time"]).replace("Z", "+00:00"))
                            if dt_e <= now_utc:
                                end_iso = str(parsed["end_time"])
                            else:
                                end_iso = now_utc.isoformat().replace("+00:00", "Z")
                        except Exception:
                            pass
    except Exception:
        # Graceful fallback: return deterministic filters if Ollama is offline/slow
        pass

    # Safety override: if deterministic layer found an excluded category, ensure category is never assigned
    if extracted_exclude and extracted_cat == extracted_exclude:
        extracted_cat = None

    # Safety override: prevent future timestamps and inverted bounds
    if start_iso:
        try:
            dt_s = datetime.fromisoformat(start_iso.replace("Z", "+00:00"))
            if dt_s > now_utc:
                start_iso = None
        except Exception:
            pass

    if end_iso:
        try:
            dt_e = datetime.fromisoformat(end_iso.replace("Z", "+00:00"))
            if dt_e > now_utc:
                end_iso = now_utc.isoformat().replace("+00:00", "Z")
        except Exception:
            pass

    if start_iso and end_iso:
        try:
            dt_s = datetime.fromisoformat(start_iso.replace("Z", "+00:00"))
            dt_e = datetime.fromisoformat(end_iso.replace("Z", "+00:00"))
            if dt_s > dt_e:
                start_iso, end_iso = end_iso, start_iso
        except Exception:
            pass

    return InterpretedFilters(
        camera_id=extracted_cam,
        camera_ids=extracted_cams,
        category=extracted_cat,
        exclude_category=extracted_exclude,
        start_time=start_iso,
        end_time=end_iso,
    )


def generate_grounded_answer(
    question: str,
    filters: InterpretedFilters,
    incidents: List[ClassifiedIncident],
) -> str:
    """Generates a truthful, dynamic textual summary grounded strictly in query results."""
    count = len(incidents)

    # Format camera label
    if filters.camera_ids:
        cam_desc = f"on cameras {', '.join(filters.camera_ids)}"
    elif filters.camera_id:
        cam_desc = f"on {filters.camera_id}"
    else:
        cam_desc = "across all cameras"

    # Format time context
    time_desc = ""
    if filters.start_time and not filters.end_time:
        time_desc = " for the requested time window"
    elif filters.start_time and filters.end_time:
        time_desc = " during the specified interval"

    plural = "s" if count != 1 else ""

    if filters.exclude_category:
        exc_str = filters.exclude_category.replace("_", " ")
        if count > 0:
            return f"Found {count} event{plural} (excluding {exc_str}) {cam_desc}{time_desc}."
        else:
            return f"No events (excluding {exc_str}) detected {cam_desc}{time_desc}."

    if filters.category:
        cat_str = filters.category.replace("_", " ")
        if count > 0:
            return f"Found {count} {cat_str} event{plural} {cam_desc}{time_desc}."
        else:
            return f"No {cat_str} events detected {cam_desc}{time_desc}."

    if count > 0:
        return f"Found {count} event{plural} {cam_desc}{time_desc}."
    else:
        return f"No events detected {cam_desc}{time_desc}."


async def process_incident_query(
    question: str,
    limit: int = 50,
    offset: int = 0,
) -> QueryResponse:
    """End-to-end handler for POST /api/query: parses filters, executes SQL, produces grounded answer."""
    filters = await extract_filters_with_ollama(question)

    start_dt = (
        datetime.fromisoformat(filters.start_time.replace("Z", "+00:00"))
        if filters.start_time
        else None
    )
    end_dt = (
        datetime.fromisoformat(filters.end_time.replace("Z", "+00:00"))
        if filters.end_time
        else None
    )

    # Inverted bounds protection
    if start_dt and end_dt and start_dt > end_dt:
        start_dt, end_dt = end_dt, start_dt

    incidents = query_incidents(
        camera_id=filters.camera_id,
        camera_ids=filters.camera_ids,
        category=filters.category,
        exclude_category=filters.exclude_category,
        start_time=start_dt,
        end_time=end_dt,
        limit=limit,
        offset=offset,
    )

    answer = generate_grounded_answer(question, filters, incidents)

    # Build clean filter dict conforming to SHARED_CONTRACTS.md
    filters_dict: Dict[str, Any] = {}
    if filters.camera_id:
        filters_dict["camera_id"] = filters.camera_id
    if filters.camera_ids:
        filters_dict["camera_ids"] = filters.camera_ids
    if filters.category:
        filters_dict["category"] = filters.category
    if filters.exclude_category:
        filters_dict["exclude_category"] = filters.exclude_category
    if filters.start_time:
        filters_dict["start_time"] = filters.start_time
    if filters.end_time:
        filters_dict["end_time"] = filters.end_time

    return QueryResponse(
        question=question,
        interpreted_filters=filters_dict,
        answer=answer,
        incidents=incidents,
    )
