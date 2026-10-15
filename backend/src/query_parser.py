import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

try:
    from backend.src.database import DEFAULT_DB_PATH, list_incidents
    from backend.src.schemas import Category, ClassifiedIncident, QueryResponse
except ModuleNotFoundError:
    from src.database import DEFAULT_DB_PATH, list_incidents
    from src.schemas import Category, ClassifiedIncident, QueryResponse


CATEGORY_SYNONYMS: dict[Category, list[str]] = {
    Category.person_down: [
        r"\bperson[\s_-]?down\b",
        r"\bworker[\s_-]?down\b",
        r"\bman[\s_-]?down\b",
        r"\bfallen\s+person\b",
        r"\bperson\s+lying\b",
    ],
    Category.fighting: [
        r"\bfighting\b",
        r"\bfight(?:s)?\b",
        r"\baltercation(?:s)?\b",
        r"\bbrawl(?:s)?\b",
        r"\bviolence\b",
    ],
    Category.tailgating: [
        r"\btailgating\b",
        r"\btailgate(?:s)?\b",
        r"\btailgater(?:s)?\b",
        r"\bunauthorized\s+entry\b",
    ],
    Category.crowd_incident: [
        r"\bcrowd[\s_-]?incident(?:s)?\b",
        r"\bcrowd(?:s)?\b",
        r"\bgathering(?:s)?\b",
        r"\bcongestion\b",
    ],
    Category.suspicious_activity: [
        r"\bsuspicious[\s_-]?activity\b",
        r"\bsuspicious\b",
        r"\bloitering\b",
    ],
    Category.other: [
        r"\bother\b",
    ],
    Category.unknown: [
        r"\bunknown\b",
    ],
}

# Non-canonical category terms that users might ask for, which should be rejected with clarification
KNOWN_INVALID_CATEGORIES = [
    "fire", "smoke", "weapon", "weapons", "gun", "knife", "theft", "stealing",
    "burglary", "robbery", "intrusion", "trespassing", "speeding", "flying",
    "collision", "accident", "vandalism", "hazard", "spill", "leak",
]

DOMAIN_KEYWORDS = [
    r"\bincident(?:s)?\b",
    r"\bevent(?:s)?\b",
    r"\bshow\b",
    r"\blist\b",
    r"\bget\b",
    r"\bfind\b",
    r"\bhow\s+many\b",
    r"\bcount\b",
    r"\blatest\b",
    r"\blast\b",
    r"\brecent\b",
    r"\ball\b",
    r"\bcamera(?:s)?\b",
    r"\bcam[_-]?[a-z0-9]+\b",
    r"\btoday\b",
    r"\byesterday\b",
]


@dataclass
class ParsedQuery:
    is_supported: bool
    is_count: bool = False
    category: Optional[Category] = None
    camera_id: Optional[str] = None
    start: Optional[str] = None
    end: Optional[str] = None
    limit: int = 50
    offset: int = 0
    interpreted_filters: dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None


def parse_query(question: str, reference_time: Optional[datetime] = None) -> ParsedQuery:
    """Parse a natural language question into structured incident filters deterministically."""
    if not isinstance(question, str) or not question.strip():
        return ParsedQuery(
            is_supported=False,
            error_message="Question cannot be empty. Please ask about incidents by category, camera, date, or count.",
        )

    q = question.strip()
    q_lower = q.lower()

    # 1. Check for explicit invalid date formats: YYYY-MM-DD that fails calendar validation
    date_candidates = re.findall(r"\b(\d{4}-\d{2}-\d{2})\b", q)
    for date_str in date_candidates:
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return ParsedQuery(
                is_supported=False,
                error_message=f"Invalid date '{date_str}' in question. Please use valid calendar dates in YYYY-MM-DD format or 'today'/'yesterday'.",
            )

    # 2. Check for explicit request for an invalid / non-canonical category
    # Pattern: "category <word>", "type of <word>", "<word> incidents"
    explicit_cat_match = re.search(r"\b(?:category|type)(?:\s+of)?\s+([a-zA-Z0-9_-]+)\b", q_lower)
    if explicit_cat_match:
        cat_word = explicit_cat_match.group(1).lower()
        canonical_values = {c.value for c in Category}
        if cat_word not in canonical_values and not any(cat_word in s for s in ["any", "all", "each"]):
            return ParsedQuery(
                is_supported=False,
                error_message=f"Category '{cat_word}' is not recognized. Canonical categories are: {', '.join(sorted(canonical_values))}.",
            )

    for invalid_cat in KNOWN_INVALID_CATEGORIES:
        pattern = rf"\b{invalid_cat}\b"
        if re.search(pattern, q_lower):
            canonical_values = {c.value for c in Category}
            return ParsedQuery(
                is_supported=False,
                error_message=f"Category '{invalid_cat}' is not recognized. Canonical categories are: {', '.join(sorted(canonical_values))}.",
            )

    # 3. Match canonical categories
    matched_categories: list[Category] = []
    for cat, patterns in CATEGORY_SYNONYMS.items():
        for pat in patterns:
            if re.search(pat, q_lower):
                if cat not in matched_categories:
                    matched_categories.append(cat)
                break

    # If multiple distinct canonical categories matched -> ambiguous query
    if len(matched_categories) > 1:
        cat_names = sorted([c.value for c in matched_categories])
        return ParsedQuery(
            is_supported=False,
            error_message=f"Ambiguous query: multiple categories detected ({', '.join(cat_names)}). Please filter by one category at a time.",
        )

    selected_category: Optional[Category] = matched_categories[0] if matched_categories else None

    # 4. Camera ID extraction
    camera_id: Optional[str] = None
    # 4a. Check for "camera 2" -> "CAM_02", "camera 01" -> "CAM_01", "camera 12" -> "CAM_12"
    cam_num_match = re.search(r"\bcamera\s*(\d+)\b", q_lower)
    if cam_num_match:
        num = int(cam_num_match.group(1))
        camera_id = f"CAM_{num:02d}"
    else:
        # 4b. Check for explicit "CAM_01", "CAM-02", "CAM_NORTH", "CAM1"
        cam_code_match = re.search(r"\bcam(?:[-_]([a-z0-9]+)|(\d+))\b", q_lower)
        if cam_code_match:
            if cam_code_match.group(2):
                num = int(cam_code_match.group(2))
                camera_id = f"CAM_{num:02d}"
            else:
                code = cam_code_match.group(1).upper()
                camera_id = f"CAM_{code}"
        else:
            # 4c. Check for "camera <name>" (e.g. "camera north" -> "CAM_NORTH", "camera CAM_A" -> "CAM_A")
            cam_name_match = re.search(r"\bcamera\s+([a-z0-9_-]+)\b", q_lower)
            cam_stop_words = {
                "id", "feed", "view", "today", "yesterday", "incidents",
                "events", "footage", "stream", "status", "data", "records",
                "detected", "active", "offline", "online",
            }
            if cam_name_match and cam_name_match.group(1) not in cam_stop_words:
                raw_name = cam_name_match.group(1).upper()
                camera_id = raw_name if raw_name.startswith("CAM_") else f"CAM_{raw_name}"

    # 5. Date / Date Range extraction
    ref_dt = reference_time or datetime.now(timezone.utc)
    today_str = ref_dt.strftime("%Y-%m-%d")
    start: Optional[str] = None
    end: Optional[str] = None

    if len(date_candidates) >= 2:
        # Range between two explicit dates
        d1, d2 = date_candidates[0], date_candidates[1]
        if d1 > d2:
            return ParsedQuery(
                is_supported=False,
                error_message=f"Invalid date range: start date '{d1}' cannot be later than end date '{d2}'.",
            )
        start = f"{d1}T00:00:00Z"
        end = f"{d2}T23:59:59.999999Z"
    elif len(date_candidates) == 1 and "today" in q_lower:
        d1 = date_candidates[0]
        if d1 > today_str:
            return ParsedQuery(
                is_supported=False,
                error_message=f"Invalid date range: start date '{d1}' cannot be later than today ('{today_str}').",
            )
        start = f"{d1}T00:00:00Z"
        end = ref_dt.strftime("%Y-%m-%dT23:59:59.999999Z")
    elif len(date_candidates) == 1:
        d = date_candidates[0]
        start = f"{d}T00:00:00Z"
        end = f"{d}T23:59:59.999999Z"
    elif "today" in q_lower:
        start = ref_dt.strftime("%Y-%m-%dT00:00:00Z")
        end = ref_dt.strftime("%Y-%m-%dT23:59:59.999999Z")
    elif "yesterday" in q_lower:
        y_dt = ref_dt - timedelta(days=1)
        start = y_dt.strftime("%Y-%m-%dT00:00:00Z")
        end = y_dt.strftime("%Y-%m-%dT23:59:59.999999Z")

    # 6. Limit extraction
    limit = 50
    limit_match = re.search(r"\b(?:latest|last|newest|top|show|get|list|display)\s+(\d+)\b", q_lower)
    if limit_match:
        limit = min(max(1, int(limit_match.group(1))), 100)
    elif re.search(r"\b(?:latest|newest)\b", q_lower):
        limit = 10

    # 7. Count query detection
    is_count = bool(
        re.search(r"\bhow\s+many\b", q_lower)
        or re.search(r"\bcount\b", q_lower)
        or re.search(r"\btotal\s+(?:number\s+of\s+)?incidents\b", q_lower)
        or re.search(r"\bnumber\s+of\s+(?:matching\s+)?incidents\b", q_lower)
    )

    # 8. Check general relevance / supported intent
    is_domain_relevant = (
        selected_category is not None
        or camera_id is not None
        or start is not None
        or is_count
        or any(re.search(kw, q_lower) for kw in DOMAIN_KEYWORDS)
    )

    if not is_domain_relevant:
        return ParsedQuery(
            is_supported=False,
            error_message="Unsupported query. Please ask about incidents by category (e.g. fighting, person_down), camera (e.g. CAM_01), date (e.g. today), or count.",
        )

    # Build interpreted_filters dictionary matching SHARED_CONTRACTS.md
    interpreted_filters: dict[str, Any] = {}
    if camera_id is not None:
        interpreted_filters["camera_id"] = camera_id
    if selected_category is not None:
        interpreted_filters["category"] = selected_category.value
    if start is not None:
        interpreted_filters["start"] = start
    if end is not None:
        interpreted_filters["end"] = end
    if limit != 50 or limit_match is not None:
        interpreted_filters["limit"] = limit

    return ParsedQuery(
        is_supported=True,
        is_count=is_count,
        category=selected_category,
        camera_id=camera_id,
        start=start,
        end=end,
        limit=limit,
        offset=0,
        interpreted_filters=interpreted_filters,
    )


def execute_query(
    question: str,
    db_path: Optional[str] = None,
    reference_time: Optional[datetime] = None,
) -> QueryResponse:
    """Execute a natural-language query safely against the SQLite database."""
    parsed = parse_query(question, reference_time=reference_time)

    if not parsed.is_supported:
        return QueryResponse(
            question=question,
            interpreted_filters={},
            answer=parsed.error_message or "Unsupported query.",
            incidents=[],
            status="unsupported_query",
        )

    # Execute parameterized query through standard database helper
    items, total = list_incidents(
        camera_id=parsed.camera_id,
        category=parsed.category,
        start=parsed.start,
        end=parsed.end,
        limit=parsed.limit,
        offset=parsed.offset,
        db_path=db_path,
    )

    # Construct concise, evidence-backed answer
    if parsed.is_count:
        if parsed.category and parsed.camera_id:
            answer = f"Found {total} {parsed.category.value} incident{'s' if total != 1 else ''} from camera {parsed.camera_id}."
        elif parsed.category:
            answer = f"Found {total} {parsed.category.value} incident{'s' if total != 1 else ''}."
        elif parsed.camera_id:
            answer = f"Found {total} incident{'s' if total != 1 else ''} from camera {parsed.camera_id}."
        else:
            answer = f"Found {total} total incident{'s' if total != 1 else ''}."
    else:
        if total == 0:
            answer = "Found 0 matching incidents."
        else:
            answer = f"Found {total} matching incident{'s' if total != 1 else ''}."

    return QueryResponse(
        question=question,
        interpreted_filters=parsed.interpreted_filters,
        answer=answer,
        incidents=items,
        status="success",
    )
