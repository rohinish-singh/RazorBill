from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest

from datasets_incident_detection.catalog import make_split_plan, validate_manifest
from datasets_incident_detection.contracts import validate_candidate_packet
from datasets_incident_detection.evaluation import evaluate_events


def manifest(tmp_path: Path) -> dict:
    (tmp_path / "clips").mkdir()
    (tmp_path / "clips" / "a.mp4").write_bytes(b"synthetic-a")
    (tmp_path / "clips" / "b.mp4").write_bytes(b"synthetic-b")
    return {
        "schema_version": "1.0.0", "dataset_id": "local_staged", "dataset_version": "0.1",
        "local_root": ".", "source": {"original_url": "local://consented", "publication": "local staged fixture", "terms_url": "local://consent-record", "terms_status": "verified", "acquisition_status": "available", "acquisition_date": "2026-10-15"},
        "labels": {"tailgate": "tailgating", "normal": "other"}, "provenance": {"owner": "test", "limitations": ["synthetic"]},
        "clips": [
            {"clip_id": "a", "path": "clips/a.mp4", "source_group": "session-1", "labels": ["tailgate"], "temporal_intervals": [{"start_seconds": 1, "end_seconds": 2}], "sha256": hashlib.sha256(b"synthetic-a").hexdigest(), "provenance": {"consent": "fixture"}},
            {"clip_id": "b", "path": "clips/b.mp4", "source_group": "session-2", "labels": ["normal"], "temporal_intervals": [], "sha256": hashlib.sha256(b"synthetic-b").hexdigest(), "provenance": {"consent": "fixture"}},
        ],
    }


def codes(report):
    return {issue["code"] for issue in report["issues"]}


def test_valid_manifest(tmp_path):
    assert validate_manifest(manifest(tmp_path), tmp_path, check_files=True)["valid"]


def test_missing_video_file(tmp_path):
    value = manifest(tmp_path); value["clips"][0]["path"] = "clips/missing.mp4"
    assert "missing_file" in codes(validate_manifest(value, tmp_path, True))


def test_unknown_label(tmp_path):
    value = manifest(tmp_path); value["clips"][0]["labels"] = ["not-a-label"]
    assert "unknown_label" in codes(validate_manifest(value, tmp_path))


def test_invalid_temporal_interval(tmp_path):
    value = manifest(tmp_path); value["clips"][0]["temporal_intervals"] = [{"start_seconds": 3, "end_seconds": 2}]
    assert "invalid_interval" in codes(validate_manifest(value, tmp_path))


def test_duplicate_content(tmp_path):
    value = manifest(tmp_path); value["clips"][1]["sha256"] = value["clips"][0]["sha256"]
    assert "exact_duplicate" in codes(validate_manifest(value, tmp_path))


def test_missing_provenance_and_unverified_terms(tmp_path):
    value = manifest(tmp_path); del value["provenance"]; value["source"]["terms_status"] = "unverified"
    report = validate_manifest(value, tmp_path)
    assert "missing_required" in codes(report) and "terms_unverified" in codes(report)


def test_source_groups_are_isolated_and_reproducible(tmp_path):
    value = manifest(tmp_path)
    value["clips"].append(deepcopy(value["clips"][0]) | {"clip_id": "a-second-view", "path": "clips/b.mp4"})
    plan_a, plan_b = make_split_plan(value, 123), make_split_plan(value, 123)
    assert plan_a == plan_b
    assert plan_a["clips"]["a"] == plan_a["clips"]["a-second-view"]


def test_empty_dataset_behaviour(tmp_path):
    value = manifest(tmp_path); value["clips"] = []
    assert validate_manifest(value, tmp_path)["valid"]
    assert make_split_plan(value)["clips"] == {}


def test_malformed_manifest():
    report = validate_manifest({"schema_version": "bad"})
    assert not report["valid"] and "missing_required" in codes(report)


def test_shared_candidate_packet_validation():
    packet = {"event_id": "evt_1", "camera_id": "CAM_01", "video_source_id": "demo", "timestamp_seconds": 1.5, "frame_path": "data/evt.jpg", "frame_paths": ["data/evt.jpg"], "tracks": [{"track_id": 1, "class_name": "person", "bbox_xyxy": [1, 2, 3, 4]}], "trigger": "sampled_frame", "created_at": "2026-10-15T10:00:00Z"}
    assert validate_candidate_packet(packet) == []
    packet["tracks"][0]["bbox_xyxy"] = [3, 2, 1, 4]
    assert validate_candidate_packet(packet)


def test_evaluation_not_evaluated_and_metrics():
    truth = [{"event_id": "a", "category": "fighting", "timestamp_seconds": 1.0}]
    assert evaluate_events(truth, None)["status"] == "not_evaluated"
    result = evaluate_events(truth, [{"event_id": "a", "category": "fighting", "timestamp_seconds": 1.4, "status": "classified"}])
    assert result["status"] == "evaluated" and result["per_category"]["fighting"]["f1"] == 1.0
