import argparse
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Optional

try:
    from backend.src.database import (
        DEFAULT_DB_PATH,
        get_incident_by_id,
        init_db,
        upsert_incident,
    )
    from backend.src.main import get_frames_dir
    from backend.src.schemas import (
        Category,
        ClassifiedIncident,
        Source,
        Status,
    )
except ModuleNotFoundError:
    from src.database import (
        DEFAULT_DB_PATH,
        get_incident_by_id,
        init_db,
        upsert_incident,
    )
    from src.main import get_frames_dir
    from src.schemas import (
        Category,
        ClassifiedIncident,
        Source,
        Status,
    )


SYNTHETIC_INCIDENT_SPECS = [
    {
        "event_id": "demo_synth_001",
        "camera_id": "CAM_01",
        "timestamp_seconds": 45.0,
        "category": Category.person_down,
        "summary": "[SYNTHETIC DEMO] Simulated event: Individual observed seated or collapsed on floor near entrance vestibule.",
        "confidence": None,
        "confidence_type": "unavailable",
        "frame_relative_path": "CAM_01/demo_sample_01.jpg",
        "source": Source.manual,
        "processing_ms": None,
        "status": Status.classified,
        "evidence_notes": "[SYNTHETIC DEMO] Synthetic evaluation record. Posture consistent with floor collapse. Not a real detection.",
        "hours_offset": 2.0,  # ~2 hours ago (today)
    },
    {
        "event_id": "demo_synth_002",
        "camera_id": "CAM_02",
        "timestamp_seconds": 112.5,
        "category": Category.tailgating,
        "summary": "[SYNTHETIC DEMO] Simulated event: Second individual closely follows badge holder through secure portal without badge scan.",
        "confidence": None,
        "confidence_type": "unavailable",
        "frame_relative_path": "CAM_02/demo_sample_02.jpg",
        "source": Source.manual,
        "processing_ms": None,
        "status": Status.classified,
        "evidence_notes": "[SYNTHETIC DEMO] Synthetic evaluation record. Two tracks detected within single portal release window.",
        "hours_offset": 4.5,  # ~4.5 hours ago (today)
    },
    {
        "event_id": "demo_synth_003",
        "camera_id": "CAM_01",
        "timestamp_seconds": 230.0,
        "category": Category.crowd_incident,
        "summary": "[SYNTHETIC DEMO] Simulated event: Sudden density accumulation and rapid bidirectional movement in main corridor.",
        "confidence": None,
        "confidence_type": "unavailable",
        "frame_relative_path": "CAM_01/demo_sample_03.jpg",
        "source": Source.manual,
        "processing_ms": None,
        "status": Status.candidate,
        "evidence_notes": "[SYNTHETIC DEMO] Synthetic evaluation record. Bounded candidate awaiting full asynchronous classification.",
        "hours_offset": 7.0,  # ~7 hours ago (today)
    },
    {
        "event_id": "demo_synth_004",
        "camera_id": "CAM_03",
        "timestamp_seconds": 310.2,
        "category": Category.fighting,
        "summary": "[SYNTHETIC DEMO] Simulated event: Rapid high-velocity physical altercation between two individuals near loading bay.",
        "confidence": None,
        "confidence_type": "unavailable",
        "frame_relative_path": "CAM_03/demo_sample_04.jpg",
        "source": Source.manual,
        "processing_ms": None,
        "status": Status.needs_review,
        "evidence_notes": "[SYNTHETIC DEMO] Synthetic evaluation record. Overlapping high-acceleration bounding boxes flagged for human operator review.",
        "hours_offset": 26.0,  # ~26 hours ago (yesterday)
    },
    {
        "event_id": "demo_synth_005",
        "camera_id": "CAM_02",
        "timestamp_seconds": 415.8,
        "category": Category.suspicious_activity,
        "summary": "[SYNTHETIC DEMO] Simulated event: Loitering individual stationary near server room perimeter for extended duration.",
        "confidence": None,
        "confidence_type": "unavailable",
        "frame_relative_path": "CAM_02/demo_sample_05.jpg",
        "source": Source.manual,
        "processing_ms": None,
        "status": Status.classified,
        "evidence_notes": "[SYNTHETIC DEMO] Synthetic evaluation record. Track dwell duration exceeded 300 seconds without badge activity.",
        "hours_offset": 30.0,  # ~30 hours ago (yesterday)
    },
    {
        "event_id": "demo_synth_006",
        "camera_id": "CAM_01",
        "timestamp_seconds": 520.0,
        "category": Category.unknown,
        "summary": "[SYNTHETIC DEMO] Simulated event: Low-illumination visual occlusion caused classification uncertainty.",
        "confidence": None,
        "confidence_type": "unavailable",
        "frame_relative_path": "CAM_01/demo_sample_06.jpg",
        "source": Source.manual,
        "processing_ms": None,
        "status": Status.failed,
        "evidence_notes": "[SYNTHETIC DEMO] Synthetic evaluation record. Image contrast below analysis threshold; marked failed without guessing.",
        "hours_offset": 50.0,  # ~50 hours ago (older)
    },
]


def resolve_seed_frame_path(frame_relative_path: str, frames_dir: str) -> str:
    """Return relative frame_path if the file actually exists on disk; otherwise empty string.

    This ensures we never invent paths to images that do not exist, allowing missing-image
    handling to function cleanly.
    """
    candidate_path = os.path.join(frames_dir, frame_relative_path)
    if os.path.isfile(candidate_path):
        return os.path.join("data", "frames", frame_relative_path).replace("\\", "/")
    return ""


def build_synthetic_incidents(
    reference_time: Optional[datetime] = None,
    frames_dir: Optional[str] = None,
) -> list[ClassifiedIncident]:
    """Construct deterministic synthetic incident objects matching SHARED_CONTRACTS.md."""
    ref_dt = reference_time or datetime.now(timezone.utc)
    target_frames_dir = frames_dir or get_frames_dir()

    incidents: list[ClassifiedIncident] = []
    for spec in SYNTHETIC_INCIDENT_SPECS:
        event_time = ref_dt - timedelta(hours=spec["hours_offset"])
        created_at_iso = event_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        frame_path = resolve_seed_frame_path(spec["frame_relative_path"], target_frames_dir)

        incidents.append(
            ClassifiedIncident(
                event_id=spec["event_id"],
                camera_id=spec["camera_id"],
                timestamp_seconds=spec["timestamp_seconds"],
                category=spec["category"],
                summary=spec["summary"],
                confidence=spec["confidence"],
                confidence_type=spec["confidence_type"],
                frame_path=frame_path,
                source=spec["source"],
                processing_ms=spec["processing_ms"],
                status=spec["status"],
                evidence_notes=spec["evidence_notes"],
                created_at=created_at_iso,
            )
        )
    return incidents


def seed_demo_data(
    db_path: Optional[str] = None,
    reference_time: Optional[datetime] = None,
    frames_dir: Optional[str] = None,
) -> int:
    """Idempotently seed deterministic synthetic incidents into the specified SQLite database.

    Guarantees:
    - Never overwrites real non-synthetic incidents.
    - Idempotent: multiple executions update existing demo incidents in-place without duplicating.
    - Returns count of seeded incidents.
    """
    target_db_path = db_path or os.environ.get("RAZORBILL_DB_PATH", DEFAULT_DB_PATH)
    init_db(target_db_path)

    incidents = build_synthetic_incidents(
        reference_time=reference_time,
        frames_dir=frames_dir,
    )

    seeded_count = 0
    for incident in incidents:
        existing = get_incident_by_id(incident.event_id, db_path=target_db_path)
        if existing and existing.source != Source.manual:
            # Guard against overwriting any real detection that somehow shares an ID
            print(f"[seed] Skipping {incident.event_id}: non-synthetic incident already present.")
            continue

        upsert_incident(incident, db_path=target_db_path)
        seeded_count += 1

    return seeded_count


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Seed RazorBill database with deterministic synthetic demo incidents.",
    )
    parser.add_argument(
        "--db-path",
        default=os.environ.get("RAZORBILL_DB_PATH", DEFAULT_DB_PATH),
        help="Target SQLite database path (defaults to RAZORBILL_DB_PATH or data/razorbill.db)",
    )
    parser.add_argument(
        "--frames-dir",
        default=None,
        help="Frames directory path (defaults to RAZORBILL_FRAMES_DIR or data/frames)",
    )
    parser.add_argument(
        "--fixed-date",
        default=None,
        help="Optional reference ISO timestamp (e.g. '2026-10-16T12:00:00Z') for deterministic dates",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Display synthetic records that would be seeded without writing to database",
    )

    args = parser.parse_args()

    ref_time = None
    if args.fixed_date:
        try:
            ref_time = datetime.fromisoformat(args.fixed_date.replace("Z", "+00:00"))
        except ValueError as e:
            print(f"Error parsing --fixed-date: {e}", file=sys.stderr)
            sys.exit(1)

    if args.dry_run:
        records = build_synthetic_incidents(
            reference_time=ref_time,
            frames_dir=args.frames_dir,
        )
        print(f"Dry run: {len(records)} synthetic incidents prepared:")
        for r in records:
            print(f"  - [{r.event_id}] {r.category.value} ({r.camera_id}): {r.summary}")
            print(f"    Status: {r.status.value}, Created: {r.created_at}, Frame: '{r.frame_path}'")
        return

    count = seed_demo_data(
        db_path=args.db_path,
        reference_time=ref_time,
        frames_dir=args.frames_dir,
    )
    print(f"Successfully seeded {count} synthetic demo incidents into {args.db_path}.")


if __name__ == "__main__":
    main()
