import mimetypes
import os
import re
import urllib.parse
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

try:
    from backend.src.database import (
        DEFAULT_DB_PATH,
        REPO_ROOT,
        get_incident_by_id,
        get_stats,
        init_db,
        list_incidents,
        upsert_incident,
    )
    from backend.src.query_parser import execute_query
    from backend.src.schemas import (
        Category,
        ClassifiedIncident,
        IncidentListResponse,
        QueryRequest,
        QueryResponse,
        StatsResponse,
        normalize_boundary,
    )
except ModuleNotFoundError:
    from src.database import (
        DEFAULT_DB_PATH,
        REPO_ROOT,
        get_incident_by_id,
        get_stats,
        init_db,
        list_incidents,
        upsert_incident,
    )
    from src.query_parser import execute_query
    from src.schemas import (
        Category,
        ClassifiedIncident,
        IncidentListResponse,
        QueryRequest,
        QueryResponse,
        StatsResponse,
        normalize_boundary,
    )


class HealthResponse(BaseModel):
    status: str


def get_db_path() -> str:
    return os.environ.get("RAZORBILL_DB_PATH", DEFAULT_DB_PATH)


def get_frames_dir() -> str:
    custom = os.environ.get("RAZORBILL_FRAMES_DIR")
    if custom:
        return os.path.abspath(custom)
    data_dir = os.environ.get("RAZORBILL_DATA_DIR", os.path.join(REPO_ROOT, "data"))
    return os.path.abspath(os.path.join(data_dir, "frames"))


ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def resolve_evidence_path(file_path: str, base_dir: Optional[str] = None) -> str:
    raw_frames_dir = base_dir or get_frames_dir()
    frames_dir = os.path.realpath(os.path.abspath(raw_frames_dir))

    if not file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence frame not found",
        )

    # URL-decode and convert backslashes to forward slashes
    decoded_path = urllib.parse.unquote(file_path).replace("\\", "/")

    # Reject drive-letter specifications (e.g., C:)
    drive, rest = os.path.splitdrive(decoded_path)
    if drive:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence frame not found",
        )

    # Collapse consecutive separators and strip leading/trailing slashes
    clean_path = re.sub(r"/+", "/", rest).strip("/")
    if not clean_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence frame not found",
        )

    # Strip documented prefixes if present
    if clean_path.startswith("data/frames/"):
        clean_path = clean_path[len("data/frames/"):]
    elif clean_path.startswith("frames/"):
        clean_path = clean_path[len("frames/"):]

    clean_path = clean_path.strip("/")
    if not clean_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence frame not found",
        )

    # Resolve candidate path and canonical realpath
    candidate_path = os.path.abspath(os.path.join(frames_dir, clean_path))
    real_target_path = os.path.realpath(candidate_path)

    # Verify both candidate and resolved paths remain strictly inside frames_dir
    try:
        common_cand = os.path.commonpath([frames_dir, candidate_path])
        common_real = os.path.commonpath([frames_dir, real_target_path])
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence frame not found",
        )

    if (
        common_cand != frames_dir
        or common_real != frames_dir
        or candidate_path == frames_dir
        or real_target_path == frames_dir
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence frame not found",
        )

    # Check extension on both candidate and real target
    cand_ext = os.path.splitext(candidate_path)[1].lower()
    target_ext = os.path.splitext(real_target_path)[1].lower()
    if cand_ext not in ALLOWED_IMAGE_EXTENSIONS or target_ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence frame not found",
        )

    # Ensure target is an actual regular file
    if not os.path.isfile(real_target_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence frame not found",
        )

    return real_target_path



@asynccontextmanager
async def lifespan(app: FastAPI):
    override = app.dependency_overrides.get(get_db_path)
    db_path = override() if override else get_db_path()
    init_db(db_path)
    yield


app = FastAPI(
    title="RazorBill Backend API",
    version="0.1.0",
    description="Live Video Event Summarization, Classification, and Conversational Querying",
    lifespan=lifespan,
)

DEFAULT_CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]


def get_cors_origins() -> list[str]:
    custom = os.environ.get("RAZORBILL_CORS_ORIGINS")
    if custom:
        return [o.strip() for o in custom.split(",") if o.strip()]
    return DEFAULT_CORS_ORIGINS


app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def get_health() -> HealthResponse:
    return HealthResponse(status="healthy")


@app.post(
    "/api/incidents",
    response_model=ClassifiedIncident,
    status_code=status.HTTP_200_OK,
)
def create_or_update_incident(
    incident: ClassifiedIncident,
    db_path: str = Depends(get_db_path),
) -> ClassifiedIncident:
    return upsert_incident(incident, db_path=db_path)


@app.get(
    "/api/incidents",
    response_model=IncidentListResponse,
)
def get_incidents(
    camera_id: Optional[str] = Query(None, description="Optional camera ID filter"),
    category: Optional[Category] = Query(None, description="Optional canonical Category filter"),
    start: Optional[str] = Query(None, description="Optional lower UTC timestamp boundary (ISO datetime or YYYY-MM-DD)"),
    end: Optional[str] = Query(None, description="Optional upper UTC timestamp boundary (ISO datetime or YYYY-MM-DD)"),
    limit: int = Query(50, ge=1, le=100, description="Page limit (1-100, default 50)"),
    offset: int = Query(0, ge=0, description="Page offset (>= 0, default 0)"),
    db_path: str = Depends(get_db_path),
) -> IncidentListResponse:
    start_norm = None
    if start is not None:
        try:
            start_norm = normalize_boundary(start, is_end=False)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid 'start' timestamp: {e}",
            )

    end_norm = None
    if end is not None:
        try:
            end_norm = normalize_boundary(end, is_end=True)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid 'end' timestamp: {e}",
            )

    if start_norm is not None and end_norm is not None:
        if start_norm > end_norm:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="'start' boundary cannot be later than 'end' boundary",
            )

    items, total = list_incidents(
        camera_id=camera_id,
        category=category,
        start=start_norm,
        end=end_norm,
        limit=limit,
        offset=offset,
        db_path=db_path,
    )
    return IncidentListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@app.get(
    "/api/incidents/{event_id}",
    response_model=ClassifiedIncident,
)
def get_incident(
    event_id: str,
    db_path: str = Depends(get_db_path),
) -> ClassifiedIncident:
    incident = get_incident_by_id(event_id, db_path=db_path)
    if not incident:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Incident '{event_id}' not found",
        )
    return incident


@app.get(
    "/api/stats",
    response_model=StatsResponse,
)
def get_incident_stats(
    db_path: str = Depends(get_db_path),
) -> StatsResponse:
    return get_stats(db_path=db_path)


@app.post(
    "/api/query",
    response_model=QueryResponse,
    status_code=status.HTTP_200_OK,
)
def post_query(
    body: QueryRequest,
    db_path: str = Depends(get_db_path),
) -> QueryResponse:
    return execute_query(question=body.question, db_path=db_path)


@app.get(
    "/data/frames/{file_path:path}",
    response_class=FileResponse,
)
def get_frame_file(
    file_path: str,
    frames_dir: str = Depends(get_frames_dir),
) -> FileResponse:
    target_path = resolve_evidence_path(file_path, base_dir=frames_dir)
    media_type, _ = mimetypes.guess_type(target_path)
    return FileResponse(target_path, media_type=media_type or "image/jpeg")


@app.get(
    "/api/evidence/{file_path:path}",
    response_class=FileResponse,
)
def get_evidence_file(
    file_path: str,
    frames_dir: str = Depends(get_frames_dir),
) -> FileResponse:
    target_path = resolve_evidence_path(file_path, base_dir=frames_dir)
    media_type, _ = mimetypes.guess_type(target_path)
    return FileResponse(target_path, media_type=media_type or "image/jpeg")
