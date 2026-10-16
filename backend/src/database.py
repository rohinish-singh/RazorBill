import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional
from .schemas import ClassifiedIncident, Category, Source, Status

DEFAULT_DB_DIR = Path(__file__).resolve().parent.parent / "data"
DEFAULT_DB_PATH = DEFAULT_DB_DIR / "razorbill.db"


def get_db_path() -> Path:
    env_path = os.getenv("RAZORBILL_DB_PATH")
    if env_path:
        path = Path(env_path)
    else:
        path = DEFAULT_DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    target_path = db_path or get_db_path()
    conn = sqlite3.connect(str(target_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Optional[Path] = None) -> None:
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS incidents (
                event_id TEXT PRIMARY KEY,
                camera_id TEXT NOT NULL,
                timestamp_seconds REAL NOT NULL,
                category TEXT NOT NULL,
                summary TEXT NOT NULL,
                confidence REAL,
                confidence_type TEXT,
                frame_path TEXT NOT NULL,
                source TEXT NOT NULL,
                processing_ms INTEGER,
                status TEXT NOT NULL,
                evidence_notes TEXT,
                created_at TEXT NOT NULL
            );
            """
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_incidents_camera ON incidents(camera_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_incidents_category ON incidents(category);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_incidents_created_at ON incidents(created_at);")
        conn.commit()


def upsert_incident(incident: ClassifiedIncident, db_path: Optional[Path] = None) -> None:
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO incidents (
                event_id, camera_id, timestamp_seconds, category, summary,
                confidence, confidence_type, frame_path, source, processing_ms,
                status, evidence_notes, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(event_id) DO UPDATE SET
                camera_id = excluded.camera_id,
                timestamp_seconds = excluded.timestamp_seconds,
                category = excluded.category,
                summary = excluded.summary,
                confidence = excluded.confidence,
                confidence_type = excluded.confidence_type,
                frame_path = excluded.frame_path,
                source = excluded.source,
                processing_ms = excluded.processing_ms,
                status = excluded.status,
                evidence_notes = excluded.evidence_notes,
                created_at = excluded.created_at;
            """,
            (
                incident.event_id,
                incident.camera_id,
                incident.timestamp_seconds,
                incident.category.value if isinstance(incident.category, Category) else str(incident.category),
                incident.summary,
                incident.confidence,
                incident.confidence_type,
                incident.frame_path,
                incident.source.value if isinstance(incident.source, Source) else str(incident.source),
                incident.processing_ms,
                incident.status.value if isinstance(incident.status, Status) else str(incident.status),
                incident.evidence_notes,
                incident.created_at,
            ),
        )
        conn.commit()


def query_incidents(
    camera_id: Optional[str] = None,
    camera_ids: Optional[List[str]] = None,
    category: Optional[str] = None,
    exclude_category: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 50,
    offset: int = 0,
    db_path: Optional[Path] = None,
) -> List[ClassifiedIncident]:
    init_db(db_path)
    conditions = []
    params = []

    target_cams = []
    if camera_ids:
        target_cams.extend(camera_ids)
    elif camera_id:
        target_cams.append(camera_id)

    if target_cams:
        placeholders = ",".join(["?"] * len(target_cams))
        conditions.append(f"camera_id IN ({placeholders})")
        params.extend(target_cams)

    if category:
        conditions.append("category = ?")
        params.append(category)

    if exclude_category:
        conditions.append("category != ?")
        params.append(exclude_category)

    if start_time and end_time and start_time > end_time:
        start_time, end_time = end_time, start_time

    if start_time:
        start_iso = start_time.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        conditions.append("created_at >= ?")
        params.append(start_iso)

    if end_time:
        end_iso = end_time.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        conditions.append("created_at <= ?")
        params.append(end_iso)

    clamped_limit = max(1, min(limit, 100))
    clamped_offset = max(0, offset)

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    sql = f"SELECT * FROM incidents {where_clause} ORDER BY created_at DESC LIMIT ? OFFSET ?"
    params.extend([clamped_limit, clamped_offset])

    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        incidents = []
        for row in rows:
            incidents.append(
                ClassifiedIncident(
                    event_id=row["event_id"],
                    camera_id=row["camera_id"],
                    timestamp_seconds=row["timestamp_seconds"],
                    category=Category(row["category"]),
                    summary=row["summary"],
                    confidence=row["confidence"],
                    confidence_type=row["confidence_type"],
                    frame_path=row["frame_path"],
                    source=Source(row["source"]),
                    processing_ms=row["processing_ms"],
                    status=Status(row["status"]),
                    evidence_notes=row["evidence_notes"],
                    created_at=row["created_at"],
                )
            )
        return incidents


def seed_default_incidents(db_path: Optional[Path] = None) -> None:
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as cnt FROM incidents;")
        count = cursor.fetchone()["cnt"]
        if count > 0:
            return

    now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    sample_incidents = [
        ClassifiedIncident(
            event_id="evt_tailgating_01",
            camera_id="CAM_02",
            timestamp_seconds=142.0,
            category=Category.tailgating,
            summary="Two individuals entered through the turnstile on a single badge scan.",
            confidence=0.92,
            confidence_type="vlm_calibrated",
            frame_path="data/frames/CAM_02/evt_tailgating_01.jpg",
            source=Source.vlm,
            processing_ms=480,
            status=Status.classified,
            evidence_notes="Second individual followed immediately without badge interaction.",
            created_at=now_iso,
        ),
        ClassifiedIncident(
            event_id="evt_tailgating_02",
            camera_id="CAM_02",
            timestamp_seconds=210.5,
            category=Category.tailgating,
            summary="Access gate held open allowing an unverified visitor to bypass entry scan.",
            confidence=0.88,
            confidence_type="vlm_calibrated",
            frame_path="data/frames/CAM_02/evt_tailgating_02.jpg",
            source=Source.vlm,
            processing_ms=520,
            status=Status.classified,
            evidence_notes="Individual in dark jacket proceeded into secure corridor without badge verification.",
            created_at=now_iso,
        ),
        ClassifiedIncident(
            event_id="evt_person_down_01",
            camera_id="CAM_01",
            timestamp_seconds=88.2,
            category=Category.person_down,
            summary="A person appears to be lying motionless on the walkway near lobby entrance.",
            confidence=0.96,
            confidence_type="vlm_calibrated",
            frame_path="data/frames/CAM_01/evt_person_down_01.jpg",
            source=Source.vlm,
            processing_ms=610,
            status=Status.classified,
            evidence_notes="Subject prone on tile floor; no immediate movement detected for >15 seconds.",
            created_at=now_iso,
        ),
        ClassifiedIncident(
            event_id="evt_fighting_01",
            camera_id="CAM_03",
            timestamp_seconds=305.0,
            category=Category.fighting,
            summary="Aggressive physical confrontation between two individuals in the parking courtyard.",
            confidence=0.85,
            confidence_type="vlm_calibrated",
            frame_path="data/frames/CAM_03/evt_fighting_01.jpg",
            source=Source.vlm,
            processing_ms=590,
            status=Status.classified,
            evidence_notes="Rapid striking gestures and grapple postures observed.",
            created_at=now_iso,
        ),
        ClassifiedIncident(
            event_id="evt_suspicious_01",
            camera_id="CAM_01",
            timestamp_seconds=420.0,
            category=Category.suspicious_activity,
            summary="Individual lingering near high-voltage utility enclosure after hours.",
            confidence=0.78,
            confidence_type="vlm_calibrated",
            frame_path="data/frames/CAM_01/evt_suspicious_01.jpg",
            source=Source.vlm,
            processing_ms=450,
            status=Status.needs_review,
            evidence_notes="Subject repeatedly inspecting perimeter padlock without authorized maintenance vest.",
            created_at=now_iso,
        ),
    ]

    for inc in sample_incidents:
        upsert_incident(inc, db_path)

