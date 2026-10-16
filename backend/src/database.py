import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from typing import Generator, Optional

try:
    from backend.src.schemas import (
        Category,
        ClassifiedIncident,
        Source,
        StatsResponse,
        Status,
    )
except ModuleNotFoundError:
    from src.schemas import (
        Category,
        ClassifiedIncident,
        Source,
        StatsResponse,
        Status,
    )

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def get_default_db_path() -> str:
    """Return the configured database path, honoring RAZORBILL_DB_PATH at runtime."""
    return os.environ.get(
        "RAZORBILL_DB_PATH",
        os.path.join(REPO_ROOT, "data", "razorbill.db"),
    )


DEFAULT_DB_PATH = get_default_db_path()


@contextmanager
def get_connection(db_path: Optional[str] = None) -> Generator[sqlite3.Connection, None, None]:
    """Provide a transactional database connection with row factory enabled."""
    effective_path = db_path if db_path is not None else get_default_db_path()
    db_dir = os.path.dirname(effective_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(effective_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: Optional[str] = None) -> None:
    """Initialize SQLite schema and indexes for incidents."""
    with get_connection(db_path) as conn:
        conn.execute("""
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
        """)
        conn.execute("CREATE INDEX IF NOT EXISTS idx_incidents_camera_id ON incidents(camera_id);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_incidents_category ON incidents(category);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_incidents_created_at ON incidents(created_at);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_incidents_timestamp_seconds ON incidents(timestamp_seconds);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_incidents_status ON incidents(status);")


def upsert_incident(incident: ClassifiedIncident, db_path: Optional[str] = None) -> ClassifiedIncident:
    """Upsert an incident by stable event_id using parameterized SQL."""
    with get_connection(db_path) as conn:
        conn.execute("""
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
        """, (
            incident.event_id,
            incident.camera_id,
            incident.timestamp_seconds,
            incident.category.value,
            incident.summary,
            incident.confidence,
            incident.confidence_type,
            incident.frame_path,
            incident.source.value,
            incident.processing_ms,
            incident.status.value,
            incident.evidence_notes,
            incident.created_at,
        ))
    return incident


def get_incident_by_id(event_id: str, db_path: Optional[str] = None) -> Optional[ClassifiedIncident]:
    """Retrieve an incident by event_id."""
    with get_connection(db_path) as conn:
        cursor = conn.execute("SELECT * FROM incidents WHERE event_id = ?;", (event_id,))
        row = cursor.fetchone()
        if not row:
            return None
        return ClassifiedIncident(
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


def list_incidents(
    camera_id: Optional[str] = None,
    category: Optional[Category] = None,
    status: Optional[Status] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db_path: Optional[str] = None,
) -> tuple[list[ClassifiedIncident], int]:
    """Query incidents with optional filters and pagination, returning (items, total_count).

    'start' and 'end' consistently filter wall-clock 'created_at' in UTC.
    """
    conditions: list[str] = []
    params: list[object] = []

    if camera_id is not None:
        conditions.append("camera_id = ?")
        params.append(camera_id)

    if category is not None:
        conditions.append("category = ?")
        params.append(category.value if isinstance(category, Category) else str(category))

    if status is not None:
        conditions.append("status = ?")
        params.append(status.value if isinstance(status, Status) else str(status))

    if start is not None:
        conditions.append("created_at >= ?")
        params.append(start)

    if end is not None:
        conditions.append("created_at <= ?")
        params.append(end)

    where_clause = f" WHERE {' AND '.join(conditions)}" if conditions else ""

    with get_connection(db_path) as conn:
        count_sql = f"SELECT COUNT(*) as total FROM incidents{where_clause};"
        cursor = conn.execute(count_sql, tuple(params))
        total = cursor.fetchone()["total"]

        items_sql = f"""
            SELECT * FROM incidents{where_clause}
            ORDER BY created_at DESC, timestamp_seconds DESC, event_id ASC
            LIMIT ? OFFSET ?;
        """
        cursor = conn.execute(items_sql, tuple(params + [limit, offset]))
        rows = cursor.fetchall()
        items = [
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
            for row in rows
        ]

    return items, total


RECENT_ACTIVITY_WINDOW_SECONDS = 86400  # Fixed 24-hour window


def get_stats(
    db_path: Optional[str] = None,
    reference_time: Optional[datetime] = None,
) -> StatsResponse:
    """Calculate aggregated incident statistics from persisted records using SQL aggregation.

    Recent activity is computed over a fixed 24-hour window (86,400 seconds).
    """
    with get_connection(db_path) as conn:
        # 1. Total incidents count
        cur = conn.execute("SELECT COUNT(*) as total FROM incidents;")
        total = cur.fetchone()["total"]

        # 2. Counts grouped by canonical category (all canonical categories guaranteed present)
        by_category = {cat.value: 0 for cat in Category}
        cur = conn.execute("SELECT category, COUNT(*) as count FROM incidents GROUP BY category;")
        for row in cur.fetchall():
            by_category[row["category"]] = row["count"]

        # 3. Counts grouped by canonical status (all canonical statuses guaranteed present)
        by_status = {st.value: 0 for st in Status}
        cur = conn.execute("SELECT status, COUNT(*) as count FROM incidents GROUP BY status;")
        for row in cur.fetchall():
            by_status[row["status"]] = row["count"]

        # 4. Counts grouped by camera ID
        cur = conn.execute("SELECT camera_id, COUNT(*) as count FROM incidents GROUP BY camera_id ORDER BY camera_id ASC;")
        by_camera = {row["camera_id"]: row["count"] for row in cur.fetchall()}

        # 5. Recent activity count using fixed 24-hour window
        ref_dt = reference_time or datetime.now(timezone.utc)
        cutoff_dt = ref_dt - timedelta(seconds=RECENT_ACTIVITY_WINDOW_SECONDS)
        cutoff_str = cutoff_dt.strftime("%Y-%m-%dT%H:%M:%S.000000Z")
        cur = conn.execute("SELECT COUNT(*) as recent_count FROM incidents WHERE created_at >= ?;", (cutoff_str,))
        recent_count = cur.fetchone()["recent_count"]

    return StatsResponse(
        total=total,
        by_category=by_category,
        by_status=by_status,
        by_camera=by_camera,
        recent_activity_count=recent_count,
    )
