"""Event-level classification evaluation; deliberately reports not evaluated when absent."""
from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from .constants import INCIDENT_CATEGORIES, INCIDENT_STATUSES


def evaluate_events(ground_truth: list[dict[str, Any]], predictions: list[dict[str, Any]] | None) -> dict[str, Any]:
    if predictions is None:
        return {"status": "not_evaluated", "reason": "predictions were not supplied", "sample_count": len(ground_truth)}
    truth = {str(item["event_id"]): item for item in ground_truth}
    predicted = {str(item["event_id"]): item for item in predictions}
    labels = sorted(INCIDENT_CATEGORIES)
    matrix: dict[str, Counter[str]] = defaultdict(Counter)
    false_positive, false_negative, latencies = [], [], []
    for event_id, expected in truth.items():
        actual = predicted.get(event_id)
        expected_label = expected.get("category")
        if actual is None:
            false_negative.append(event_id)
            matrix[expected_label]["missing"] += 1
            continue
        actual_label = actual.get("category")
        matrix[expected_label][actual_label] += 1
        if actual_label != expected_label:
            false_negative.append(event_id)
        if isinstance(actual.get("timestamp_seconds"), (int, float)) and isinstance(expected.get("timestamp_seconds"), (int, float)):
            latencies.append(actual["timestamp_seconds"] - expected["timestamp_seconds"])
    for event_id in predicted.keys() - truth.keys():
        false_positive.append(event_id)
    per_category = {}
    for label in labels:
        tp = matrix[label][label]
        fp = sum(row[label] for expected, row in matrix.items() if expected != label) + sum(1 for item in false_positive if predicted[item].get("category") == label)
        fn = sum(count for actual, count in matrix[label].items() if actual != label)
        precision = tp / (tp + fp) if tp + fp else None
        recall = tp / (tp + fn) if tp + fn else None
        f1 = 2 * precision * recall / (precision + recall) if precision is not None and recall is not None and precision + recall else None
        per_category[label] = {"precision": precision, "recall": recall, "f1": f1, "support": sum(matrix[label].values())}
    return {"status": "evaluated", "sample_count": len(truth), "per_category": per_category,
            "confusion_matrix": {key: dict(value) for key, value in matrix.items()},
            "false_positives": false_positive, "false_negatives": false_negative,
            "event_latency_seconds": {"count": len(latencies), "mean": sum(latencies) / len(latencies) if latencies else None}}
