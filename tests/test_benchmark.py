from __future__ import annotations

import json
import sys

from datasets_incident_detection.__main__ import main
from datasets_incident_detection.benchmark import evaluate_clip_candidates


def packet(trigger: str, timestamp: float = 0.0) -> dict:
    return {
        "event_id": "evt-test",
        "camera_id": "CAM_TEST",
        "video_source_id": "test-video",
        "timestamp_seconds": timestamp,
        "frame_path": "data/frames/test.jpg",
        "frame_paths": ["data/frames/test.jpg"],
        "tracks": [],
        "trigger": trigger,
        "created_at": "2026-10-16T00:00:00Z",
    }


def test_clip_benchmark_reports_balanced_confusion_and_known_delay():
    truth = [{"sequence_id": "fall-01", "category": "person_down", "event_time_seconds": 2.0}, {"sequence_id": "adl-01", "category": "other"}]
    predictions = [{"sequence_id": "fall-01", "packets": [packet("person_down_candidate", 2.5)]}, {"sequence_id": "adl-01", "packets": []}]
    result = evaluate_clip_candidates(truth, predictions)
    assert result["confusion_matrix"] == {"true_positive": 1, "false_positive": 0, "true_negative": 1, "false_negative": 0}
    assert result["precision"] == result["recall"] == result["f1"] == 1.0
    assert result["alert_delay_seconds"] == {"count": 1, "mean": 0.5}


def test_clip_benchmark_does_not_infer_delay_without_annotation_and_counts_false_positive():
    truth = [{"sequence_id": "fall-01", "category": "person_down"}, {"sequence_id": "adl-01", "category": "other"}]
    predictions = [{"sequence_id": "fall-01", "packets": []}, {"sequence_id": "adl-01", "packets": [packet("person_down_candidate", 1.0)]}]
    result = evaluate_clip_candidates(truth, predictions)
    assert result["confusion_matrix"] == {"true_positive": 0, "false_positive": 1, "true_negative": 0, "false_negative": 1}
    assert result["alert_delay_seconds"] == {"count": 0, "mean": None}


def test_benchmark_candidates_cli_writes_clip_level_report(tmp_path, monkeypatch):
    ground_truth = tmp_path / "truth.json"
    predictions = tmp_path / "predictions.json"
    output = tmp_path / "report.json"
    ground_truth.write_text(json.dumps([{"sequence_id": "fall-01", "category": "person_down"}]), encoding="utf-8")
    predictions.write_text(json.dumps([{"sequence_id": "fall-01", "packets": [packet("person_down_candidate")]}]), encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["datasets_incident_detection", "benchmark-candidates", str(ground_truth), "--predictions", str(predictions), "--output", str(output)])
    assert main() == 0
    assert json.loads(output.read_text(encoding="utf-8"))["confusion_matrix"]["true_positive"] == 1


def test_clip_benchmark_rejects_invalid_shared_contract_packets():
    truth = [{"sequence_id": "fall-01", "category": "person_down"}]
    predictions = [{"sequence_id": "fall-01", "packets": [{"trigger": "person_down_candidate"}]}]
    try:
        evaluate_clip_candidates(truth, predictions)
    except ValueError as exc:
        assert "contract validation failed" in str(exc)
    else:
        raise AssertionError("invalid shared-contract packets must fail benchmark evaluation")


def test_clip_benchmark_checks_keyframes_when_root_is_supplied(tmp_path):
    truth = [{"sequence_id": "fall-01", "category": "person_down"}]
    predictions = [{"sequence_id": "fall-01", "packets": [packet("person_down_candidate")]}]
    try:
        evaluate_clip_candidates(truth, predictions, keyframe_root=tmp_path)
    except ValueError as exc:
        assert "keyframe validation failed" in str(exc)
    else:
        raise AssertionError("missing keyframes must fail when keyframe_root is supplied")
