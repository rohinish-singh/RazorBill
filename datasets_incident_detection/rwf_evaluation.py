"""RWF-2000 held-out split discovery and clip-level metric helpers.

The dataset is intentionally not acquired by this module.  Callers must pass
the original held-out split explicitly after independently verifying access.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

VIDEO_SUFFIXES = {".avi", ".mp4", ".mov", ".mkv"}
LABELS = {"fight": True, "nonfight": False}


def discover_heldout_clips(test_root: str | Path) -> list[dict[str, Any]]:
    """Return original split clips from explicit Fight/NonFight directories.

    No fallback to a training split is allowed: evaluation must fail rather than
    silently score training videos as held-out data.
    """
    root = Path(test_root)
    if not root.is_dir():
        raise FileNotFoundError(f"RWF-2000 held-out root does not exist: {root}")
    directories = {path.name.lower(): path for path in root.iterdir() if path.is_dir()}
    missing = sorted(set(LABELS) - set(directories))
    if missing:
        raise FileNotFoundError(
            f"expected original held-out Fight and NonFight directories beneath {root}; missing {', '.join(missing)}"
        )
    clips = []
    for label, positive in LABELS.items():
        for path in sorted(directories[label].rglob("*")):
            if path.is_file() and path.suffix.lower() in VIDEO_SUFFIXES:
                clips.append({"clip_id": path.relative_to(root).as_posix(), "path": path, "is_fight": positive})
    if not clips:
        raise FileNotFoundError(f"no supported video files beneath RWF-2000 held-out root: {root}")
    return clips


def binary_metrics(rows: list[dict[str, Any]], prediction_key: str) -> dict[str, Any]:
    """Compute clip-level metrics without substituting undefined values."""
    confusion = {"true_positive": 0, "false_positive": 0, "true_negative": 0, "false_negative": 0}
    for row in rows:
        actual = bool(row["is_fight"])
        predicted = bool(row[prediction_key])
        key = "true_positive" if actual and predicted else "false_negative" if actual else "false_positive" if predicted else "true_negative"
        confusion[key] += 1
    tp, fp, tn, fn = (confusion[key] for key in ("true_positive", "false_positive", "true_negative", "false_negative"))
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    return {
        "sample_count": len(rows), "confusion_matrix": confusion,
        "precision": precision, "recall": recall,
        "f1": 2 * precision * recall / (precision + recall) if precision is not None and recall is not None and precision + recall else None,
        "accuracy": (tp + tn) / len(rows) if rows else None,
        "false_positive_rate": fp / (fp + tn) if fp + tn else None,
    }
