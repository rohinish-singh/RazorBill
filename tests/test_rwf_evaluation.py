from pathlib import Path

import pytest

from datasets_incident_detection.rwf_evaluation import binary_metrics, discover_heldout_clips


def test_rwf_discovery_requires_explicit_original_label_directories(tmp_path):
    with pytest.raises(FileNotFoundError, match="Fight and NonFight"):
        discover_heldout_clips(tmp_path)
    for label in ("Fight", "NonFight"):
        folder = tmp_path / label; folder.mkdir(); (folder / f"{label}.avi").write_bytes(b"fixture")
    clips = discover_heldout_clips(tmp_path)
    assert {clip["clip_id"] for clip in clips} == {"Fight/Fight.avi", "NonFight/NonFight.avi"}


def test_rwf_binary_metrics_preserves_undefined_precision():
    report = binary_metrics([{"is_fight": True, "prediction": False}, {"is_fight": False, "prediction": False}], "prediction")
    assert report["confusion_matrix"] == {"true_positive": 0, "false_positive": 0, "true_negative": 1, "false_negative": 1}
    assert report["precision"] is None and report["f1"] is None and report["accuracy"] == .5
