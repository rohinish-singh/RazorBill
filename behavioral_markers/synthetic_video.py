"""Deterministic camera-health video and interval fixture generator.

Requires optional ``opencv-python-headless`` only when generating AVI files.
"""
from __future__ import annotations

import json
import hashlib
from pathlib import Path
import numpy as np

def generate(output_dir: str | Path, fps: int = 10, width: int = 96, height: int = 64) -> list[dict]:
    try:
        import cv2
    except ImportError as error:  # clear instead of emitting invalid media
        raise RuntimeError("synthetic video generation requires opencv-python-headless") from error
    out = Path(output_dir); out.mkdir(parents=True, exist_ok=True); rng = np.random.default_rng(20261015)
    base = np.tile(np.linspace(40, 210, width, dtype=np.uint8), (height, 1)); base = np.dstack([base, base, base])
    def moving(index: int):
        frame = base.copy(); x = (index * 3) % (width - 8); frame[20:28, x:x + 8] = 255
        return frame
    scenarios = {
        "normal": ([moving(index) for index in range(30)], []),
        "abrupt_blackout": ([base] * 10 + [np.zeros_like(base)] * 20, [{"label": "camera_dark", "start_seconds": 1.0, "end_seconds": 3.0}]),
        "gradual_darkening": ([np.clip(base.astype(float) * (1 - i / 40), 0, 255).astype(np.uint8) for i in range(30)], [{"label": "camera_dark", "start_seconds": 2.0, "end_seconds": 3.0}]),
        "obstruction": ([base] * 10 + [np.full_like(base, 80)] * 20, [{"label": "camera_obstruction_candidate", "start_seconds": 1.0, "end_seconds": 3.0}]),
        "blur": ([base] * 10 + [cv2.GaussianBlur(base, (15, 15), 0)] * 20, [{"label": "camera_obstruction_candidate", "start_seconds": 1.0, "end_seconds": 3.0}]),
        "frozen": ([moving(0), moving(1)] + [base] * 28, [{"label": "frozen_feed_candidate", "start_seconds": 0.2, "end_seconds": 3.0}]),
        "static_scene": ([base + (rng.normal(0, 2, base.shape)).astype(np.int16).clip(-5, 5).astype(np.uint8) for _ in range(30)], []),
        "lighting_change": ([np.clip(base.astype(float) * (1 + 0.25 * i / 29), 0, 255).astype(np.uint8) for i in range(30)], []),
    }
    records = []
    for name, (frames, intervals) in scenarios.items():
        path = out / f"{name}.avi"; writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"MJPG"), fps, (width, height))
        for frame in frames: writer.write(frame)
        writer.release(); records.append({"clip_id": name, "path": path.name, "source_group": name, "labels": [item["label"] for item in intervals] or ["normal"], "temporal_intervals": intervals, "provenance": {"generator": "deterministic CP2 synthetic"}})
    (out / "ground_truth.json").write_text(json.dumps({"fps": fps, "clips": records}, indent=2) + "\n", encoding="utf-8")
    for record in records:
        record["sha256"] = hashlib.sha256((out / record["path"]).read_bytes()).hexdigest()
    catalog = {
        "schema_version": "1.0.0", "dataset_id": "synthetic_camera_health", "dataset_version": "1.0.0",
        "local_root": ".", "source": {"original_url": "local://behavioral_markers.synthetic_video",
        "publication": "Deterministic CP2 synthetic camera-health generator", "terms_url": "local://repository-license",
        "terms_status": "verified", "acquisition_status": "generated", "acquisition_date": "2026-10-15"},
        "labels": {"camera_dark": "other", "camera_obstruction_candidate": "other",
        "frozen_feed_candidate": "other", "normal": "other"},
        "provenance": {"generator": "deterministic CP2 synthetic", "limitations": ["synthetic-only evaluation"]},
        "clips": records,
    }
    (out / "catalog.json").write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")
    return records
