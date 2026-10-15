"""Run the frozen Person 1 person-down baseline on locally acquired UR Fall RGB frames.

External data and outputs stay beneath ``data/raw``. This tool intentionally uses
only clip-level labels: UR Fall's published posture labels are depth-derived, so
they are not treated as RGB event-time ground truth.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import cv2

from behavioral_markers.schemas import CameraConfig, IncidentConfig
from datasets_incident_detection.benchmark import evaluate_clip_candidates
from video_pipeline.pipeline import PipelineConfig, UltralyticsByteTrack, process_video, write_jsonl


def timing_rows(path: Path) -> list[tuple[int, int]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [(int(row[0]), int(row[1])) for row in csv.reader(handle) if row]


def nominal_fps(rows: list[tuple[int, int]]) -> float:
    deltas = [right[1] - left[1] for left, right in zip(rows, rows[1:]) if right[1] > left[1]]
    return 1000.0 / (sum(deltas) / len(deltas)) if deltas else 30.0


def frame_directory(extracted_root: Path, sequence_id: str) -> Path:
    root = extracted_root / f"{sequence_id}-cam0-rgb"
    nested = root / f"{sequence_id}-cam0-rgb"
    return nested if nested.is_dir() else root


def convert_sequence(extracted_root: Path, derived_root: Path, sequence_id: str) -> dict:
    frames = sorted(frame_directory(extracted_root, sequence_id).glob("*.png"))
    if not frames:
        raise FileNotFoundError(f"no RGB frames for {sequence_id}")
    timing = timing_rows(extracted_root / f"{sequence_id}-data.csv")
    if len(frames) != len(timing):
        raise ValueError(f"{sequence_id}: {len(frames)} RGB frames but {len(timing)} timing rows")
    first = cv2.imread(str(frames[0]))
    if first is None:
        raise ValueError(f"unable to decode {frames[0]}")
    height, width = first.shape[:2]
    fps = nominal_fps(timing)
    derived_root.mkdir(parents=True, exist_ok=True)
    video_path = derived_root / f"{sequence_id}-cam0.mp4"
    writer = cv2.VideoWriter(str(video_path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))
    if not writer.isOpened():
        raise RuntimeError(f"unable to create {video_path}")
    try:
        for frame_path in frames:
            frame = cv2.imread(str(frame_path))
            if frame is None or frame.shape[:2] != (height, width):
                raise ValueError(f"invalid or dimension-changing frame: {frame_path}")
            writer.write(frame)
    finally:
        writer.release()
    return {
        "sequence_id": sequence_id,
        "video_path": str(video_path),
        "frame_count": len(frames),
        "width": width,
        "height": height,
        "nominal_fps": fps,
        "source_timestamps_milliseconds": [timestamp for _, timestamp in timing],
        "timing_approximation": "MP4 uses median source frame interval; original per-frame timestamps are retained in this record.",
    }


def category_from_official_labels(extracted_root: Path, sequence_id: str) -> str:
    labels_file = "urfall-cam0-falls.csv" if sequence_id.startswith("fall-") else "urfall-cam0-adls.csv"
    with (extracted_root / labels_file).open(newline="", encoding="utf-8") as handle:
        labels = [row[2] for row in csv.reader(handle) if row and row[0] == sequence_id]
    if not labels:
        raise ValueError(f"no official labels found for {sequence_id}")
    return "person_down" if "1" in labels else "other"


def run_sequence(metadata: dict, output_root: Path, device: str | None, aspect_ratio: float, persist_seconds: float,
                 gap_tolerance_seconds: float) -> dict:
    sequence_id = metadata["sequence_id"]
    camera = CameraConfig(camera_id="URFALL_CAM0", video_source_id=sequence_id,
                          incident=IncidentConfig(enabled=True, person_down_aspect_ratio=aspect_ratio,
                                                  person_down_persist_seconds=persist_seconds,
                                                  person_down_gap_tolerance_seconds=gap_tolerance_seconds))
    config = PipelineConfig(camera=camera, sample_every=1, output_root=output_root / "keyframes",
                            relative_frame_root=output_root / "keyframes", device=device)
    packets, metrics = process_video(metadata["video_path"], config, UltralyticsByteTrack(device=device))
    jsonl_path = output_root / "packets" / f"{sequence_id}.jsonl"
    jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    write_jsonl(packets, jsonl_path)
    return {"sequence_id": sequence_id, "packets": packets, "metrics": metrics.as_dict(), "packet_jsonl": str(jsonl_path),
            "person_down_config": {"aspect_ratio": aspect_ratio, "persist_seconds": persist_seconds,
                                   "gap_tolerance_seconds": gap_tolerance_seconds}}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", type=Path, default=Path("data/raw/ur_fall"))
    parser.add_argument("--output-root", type=Path, default=Path("data/raw/ur_fall/benchmark"))
    parser.add_argument("--device", default=None)
    parser.add_argument("--sequences", nargs="+", default=["fall-01", "fall-02", "adl-01", "adl-02"])
    parser.add_argument("--person-down-aspect-ratio", type=float, default=1.25)
    parser.add_argument("--person-down-persist-seconds", type=float, default=1.0)
    parser.add_argument("--person-down-gap-tolerance-seconds", type=float, default=0.0)
    parser.add_argument("--evaluate-existing", action="store_true", help="combine previously saved per-sequence runs without rerunning inference")
    args = parser.parse_args()
    extracted = args.dataset_root / "extracted"
    if args.evaluate_existing:
        conversions = []
        predictions = [json.loads((args.output_root / "run_results" / f"{sequence}.json").read_text(encoding="utf-8")) for sequence in args.sequences]
    else:
        conversions = [convert_sequence(extracted, args.dataset_root / "derived", sequence) for sequence in args.sequences]
        predictions = [run_sequence(metadata, args.output_root, args.device, args.person_down_aspect_ratio,
                                    args.person_down_persist_seconds, args.person_down_gap_tolerance_seconds) for metadata in conversions]
    ground_truth = [{"sequence_id": sequence, "category": category_from_official_labels(extracted, sequence)} for sequence in args.sequences]
    report = evaluate_clip_candidates(ground_truth, predictions, keyframe_root=Path("."))
    args.output_root.mkdir(parents=True, exist_ok=True)
    run_results = args.output_root / "run_results"
    run_results.mkdir(parents=True, exist_ok=True)
    if not args.evaluate_existing:
        for prediction in predictions:
            (run_results / f"{prediction['sequence_id']}.json").write_text(json.dumps(prediction, indent=2) + "\n", encoding="utf-8")
    (args.output_root / "ground_truth.json").write_text(json.dumps(ground_truth, indent=2) + "\n", encoding="utf-8")
    (args.output_root / "conversions.json").write_text(json.dumps(conversions, indent=2) + "\n", encoding="utf-8")
    (args.output_root / "predictions.json").write_text(json.dumps(predictions, indent=2) + "\n", encoding="utf-8")
    (args.output_root / "benchmark.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
