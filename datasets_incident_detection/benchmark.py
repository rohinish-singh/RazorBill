"""Clip-level candidate evaluation without inventing frame-level labels."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .contracts import validate_candidate_packet


def evaluate_clip_candidates(ground_truth: list[dict[str, Any]], predictions: list[dict[str, Any]] | None,
                             target_category: str = "person_down", target_trigger: str = "person_down_candidate",
                             keyframe_root: str | Path | None = None) -> dict[str, Any]:
    """Evaluate whether each labelled clip received at least one target candidate.

    Ground truth is intentionally clip-level: each item needs ``sequence_id`` and
    ``category``. ``event_time_seconds`` is optional and only enables alert-delay
    statistics; it is never inferred from a clip label or from a candidate.
    Predictions need ``sequence_id`` and a ``packets`` list in the unchanged
    Person 1 packet shape. When ``keyframe_root`` is provided, every referenced
    primary keyframe must exist under it and OpenCV must be able to decode it.
    """
    if predictions is None:
        return {"status": "not_evaluated", "reason": "predictions were not supplied", "sample_count": len(ground_truth)}
    truth = {str(item["sequence_id"]): item for item in ground_truth}
    if len(truth) != len(ground_truth):
        raise ValueError("ground_truth sequence_id values must be unique")
    predicted = {str(item["sequence_id"]): item.get("packets", []) for item in predictions}
    invalid_packets = []
    keyframe_root_path = Path(keyframe_root) if keyframe_root is not None else None
    for sequence_id, packets in predicted.items():
        if not isinstance(packets, list):
            raise ValueError(f"prediction packets for {sequence_id} must be a list")
        for index, packet in enumerate(packets):
            errors = validate_candidate_packet(packet) if isinstance(packet, dict) else ["packet must be an object"]
            if errors:
                invalid_packets.append({"sequence_id": sequence_id, "packet_index": index, "errors": errors})
    if invalid_packets:
        raise ValueError(f"candidate packet contract validation failed: {invalid_packets}")
    if keyframe_root_path is not None:
        import cv2

        unreadable_keyframes = []
        for sequence_id, packets in predicted.items():
            for index, packet in enumerate(packets):
                keyframe = keyframe_root_path / packet["frame_path"]
                if not keyframe.is_file() or cv2.imread(str(keyframe)) is None:
                    unreadable_keyframes.append({"sequence_id": sequence_id, "packet_index": index, "frame_path": packet["frame_path"]})
        if unreadable_keyframes:
            raise ValueError(f"candidate keyframe validation failed: {unreadable_keyframes}")
    unknown = sorted(set(predicted) - set(truth))
    confusion = {"true_positive": 0, "false_positive": 0, "true_negative": 0, "false_negative": 0}
    delays, sequences = [], []
    for sequence_id, expected in truth.items():
        positive = expected.get("category") == target_category
        packets = predicted.get(sequence_id, [])
        matches = [packet for packet in packets if packet.get("trigger") == target_trigger]
        detected = bool(matches)
        if positive and detected:
            outcome = "true_positive"; confusion[outcome] += 1
        elif positive:
            outcome = "false_negative"; confusion[outcome] += 1
        elif detected:
            outcome = "false_positive"; confusion[outcome] += 1
        else:
            outcome = "true_negative"; confusion[outcome] += 1
        delay = None
        event_time = expected.get("event_time_seconds")
        timestamps = [packet.get("timestamp_seconds") for packet in matches if isinstance(packet.get("timestamp_seconds"), (int, float))]
        if positive and isinstance(event_time, (int, float)) and timestamps:
            delay = min(timestamps) - event_time; delays.append(delay)
        sequences.append({"sequence_id": sequence_id, "expected_category": expected.get("category"), "candidate_count": len(packets), "target_candidate_count": len(matches), "outcome": outcome, "alert_delay_seconds": delay})
    tp, fp, tn, fn = (confusion[key] for key in ("true_positive", "false_positive", "true_negative", "false_negative"))
    precision = tp / (tp + fp) if tp + fp else None
    recall = tp / (tp + fn) if tp + fn else None
    f1 = 2 * precision * recall / (precision + recall) if precision is not None and recall is not None and precision + recall else None
    negatives = fp + tn
    return {"status": "evaluated", "target_category": target_category, "target_trigger": target_trigger,
            "sample_count": len(truth), "positive_sequence_count": tp + fn, "negative_sequence_count": negatives,
            "confusion_matrix": confusion, "precision": precision, "recall": recall, "f1": f1,
            "false_positive_rate": fp / negatives if negatives else None,
            "alert_delay_seconds": {"count": len(delays), "mean": sum(delays) / len(delays) if delays else None},
            "unknown_prediction_sequence_ids": unknown, "per_sequence": sequences}
