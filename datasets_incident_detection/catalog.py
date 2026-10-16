"""Versioned dataset-manifest validation and source-group split planning.

No dataset, model, GPU, or third-party package is required.  The JSON format is
documented in docs/datasets_incident_detection/DATASET_MANIFEST_SPEC.md.
"""
from __future__ import annotations

import hashlib
import json
import random
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any

from .constants import INCIDENT_CATEGORIES, SCHEMA_VERSION, SPLITS, TERMS_STATUSES


def load_manifest(path: str | Path) -> dict[str, Any]:
    with Path(path).open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError("manifest root must be a JSON object")
    return value


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _issue(level: str, code: str, message: str, clip_id: str | None = None) -> dict[str, str]:
    result = {"level": level, "code": code, "message": message}
    if clip_id:
        result["clip_id"] = clip_id
    return result


def validate_manifest(manifest: dict[str, Any], manifest_path: str | Path | None = None,
                      check_files: bool = False) -> dict[str, Any]:
    """Return a machine-readable report; malformed input never needs a GPU."""
    issues: list[dict[str, str]] = []
    for key in ("schema_version", "dataset_id", "dataset_version", "source", "labels", "clips", "provenance"):
        if key not in manifest:
            issues.append(_issue("error", "missing_required", f"missing required field: {key}"))
    if manifest.get("schema_version") != SCHEMA_VERSION:
        issues.append(_issue("error", "schema_version", f"expected schema_version {SCHEMA_VERSION}"))
    source = manifest.get("source")
    if not isinstance(source, dict):
        issues.append(_issue("error", "source", "source must be an object"))
        source = {}
    for key in ("original_url", "publication", "terms_url", "terms_status", "acquisition_status"):
        if not source.get(key):
            issues.append(_issue("error", "source_metadata", f"source.{key} is required"))
    if "acquisition_date" not in source:
        issues.append(_issue("error", "source_metadata", "source.acquisition_date is required (use null when unacquired)"))
    if source.get("terms_status") not in TERMS_STATUSES:
        issues.append(_issue("error", "terms_status", "terms_status must be verified, unverified, or restricted"))
    elif source.get("terms_status") != "verified":
        issues.append(_issue("warning", "terms_unverified", "dataset terms are not verified; acquisition/use requires review"))
    labels = manifest.get("labels")
    if not isinstance(labels, dict) or not labels:
        issues.append(_issue("error", "labels", "labels must be a non-empty mapping"))
        labels = {}
    for raw, mapped in labels.items():
        if mapped not in INCIDENT_CATEGORIES:
            issues.append(_issue("error", "unknown_label_mapping", f"label {raw!r} maps to unsupported category {mapped!r}"))
    clips = manifest.get("clips")
    if not isinstance(clips, list):
        issues.append(_issue("error", "clips", "clips must be a list"))
        clips = []
    ids: set[str] = set()
    hashes: dict[str, str] = {}
    size_groups: defaultdict[int, list[str]] = defaultdict(list)
    root = _resolve_root(manifest, manifest_path)
    for clip in clips:
        clip_id = clip.get("clip_id") if isinstance(clip, dict) else None
        if not isinstance(clip, dict):
            issues.append(_issue("error", "clip_type", "each clip must be an object"))
            continue
        for key in ("clip_id", "path", "source_group", "labels", "provenance"):
            if not clip.get(key):
                issues.append(_issue("error", "clip_metadata", f"clip.{key} is required", clip_id))
        if clip_id in ids:
            issues.append(_issue("error", "duplicate_clip_id", f"duplicate clip_id {clip_id}", clip_id))
        if clip_id:
            ids.add(clip_id)
        raw_labels = clip.get("labels", [])
        if not isinstance(raw_labels, list) or not raw_labels:
            issues.append(_issue("error", "clip_labels", "clip labels must be a non-empty list", clip_id))
        else:
            for label in raw_labels:
                if label not in labels:
                    issues.append(_issue("error", "unknown_label", f"label {label!r} absent from labels mapping", clip_id))
        _validate_intervals(clip.get("temporal_intervals", []), issues, clip_id)
        expected_hash = clip.get("sha256")
        if expected_hash:
            prior = hashes.get(expected_hash)
            if prior:
                issues.append(_issue("error", "exact_duplicate", f"same sha256 as {prior}", clip_id))
            else:
                hashes[expected_hash] = str(clip_id)
        if check_files and clip.get("path"):
            file_path = root / clip["path"]
            if not file_path.is_file():
                issues.append(_issue("error", "missing_file", f"referenced file not found: {file_path}", clip_id))
            else:
                size_groups[file_path.stat().st_size].append(str(clip_id))
                actual_hash = sha256_file(file_path)
                if expected_hash and actual_hash != expected_hash:
                    issues.append(_issue("error", "checksum_mismatch", "sha256 does not match local file", clip_id))
    for size, members in size_groups.items():
        if len(members) > 1:
            issues.append(_issue("warning", "possible_near_duplicate", f"same byte length ({size}) for {', '.join(members)}; inspect content"))
    return {
        "schema_version": "1.0.0", "dataset_id": manifest.get("dataset_id"),
        "clip_count": len(clips), "error_count": sum(x["level"] == "error" for x in issues),
        "warning_count": sum(x["level"] == "warning" for x in issues), "issues": issues,
        "valid": not any(x["level"] == "error" for x in issues),
    }


def _validate_intervals(intervals: Any, issues: list[dict[str, str]], clip_id: str | None) -> None:
    if intervals is None:
        return
    if not isinstance(intervals, list):
        issues.append(_issue("error", "temporal_intervals", "temporal_intervals must be a list", clip_id))
        return
    for interval in intervals:
        if not isinstance(interval, dict) or not isinstance(interval.get("start_seconds"), (int, float)) or not isinstance(interval.get("end_seconds"), (int, float)):
            issues.append(_issue("error", "invalid_interval", "interval needs numeric start_seconds and end_seconds", clip_id))
        elif interval["start_seconds"] < 0 or interval["end_seconds"] <= interval["start_seconds"]:
            issues.append(_issue("error", "invalid_interval", "interval must satisfy 0 <= start_seconds < end_seconds", clip_id))


def _resolve_root(manifest: dict[str, Any], manifest_path: str | Path | None) -> Path:
    root = Path(manifest.get("local_root", "."))
    if root.is_absolute():
        return root
    if manifest_path:
        supplied = Path(manifest_path)
        base = supplied if supplied.exists() and supplied.is_dir() else supplied.parent
    else:
        base = Path.cwd()
    return base / root


def make_split_plan(manifest: dict[str, Any], seed: int = 20261015,
                    ratios: tuple[float, float, float] = (0.7, 0.15, 0.15)) -> dict[str, Any]:
    """Assign complete source groups deterministically; never split a group."""
    if len(ratios) != 3 or any(value < 0 for value in ratios) or sum(ratios) <= 0:
        raise ValueError("ratios must contain three non-negative values with positive total")
    groups: defaultdict[str, list[str]] = defaultdict(list)
    for clip in manifest.get("clips", []):
        if isinstance(clip, dict) and clip.get("source_group") and clip.get("clip_id"):
            groups[str(clip["source_group"])].append(str(clip["clip_id"]))
    ordered = sorted(groups)
    random.Random(seed).shuffle(ordered)
    names = ("train", "validation", "test")
    targets = [len(ordered) * value / sum(ratios) for value in ratios]
    counts = [0, 0, 0]
    assignments: dict[str, str] = {}
    for group in ordered:
        index = min(range(3), key=lambda i: (counts[i] - targets[i], counts[i], i))
        assignments[group] = names[index]
        counts[index] += 1
    clips = {clip_id: assignments[group] for group, clip_ids in groups.items() for clip_id in clip_ids}
    return {"schema_version": "1.0.0", "dataset_id": manifest.get("dataset_id"), "seed": seed,
            "ratios": dict(zip(names, ratios)), "groups": assignments, "clips": clips,
            "counts": dict(zip(names, counts))}


def report_markdown(report: dict[str, Any]) -> str:
    lines = ["# Dataset validation report", "", f"- Dataset: `{report.get('dataset_id')}`", f"- Clips: {report['clip_count']}", f"- Errors: {report['error_count']}", f"- Warnings: {report['warning_count']}", "", "## Issues", ""]
    lines.extend(f"- **{issue['level']}** `{issue['code']}`: {issue['message']}" for issue in report["issues"])
    return "\n".join(lines) + "\n"
