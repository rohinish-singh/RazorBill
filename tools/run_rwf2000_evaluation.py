"""Evaluate frozen VideoMAE scores and Person 1 temporal candidates on RWF-2000.

Pass the original held-out split explicitly.  This tool neither downloads data
nor uses a training/development directory as a fallback.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import cv2
import numpy as np

from behavioral_markers.config import camera_config_from_dict
from datasets_incident_detection.rwf_evaluation import binary_metrics, discover_heldout_clips
from video_pipeline.action import SlidingWindowActionAdapter, VideoMAEViolenceModel
from video_pipeline.pipeline import PipelineConfig, UltralyticsByteTrack, process_video, write_jsonl


def uniform_frames(path: Path, frame_count: int = 16):
    capture = cv2.VideoCapture(str(path))
    total = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    if total < frame_count:
        capture.release()
        raise ValueError(f"{path} has {total} frames; VideoMAE requires at least {frame_count}")
    targets = set(np.linspace(0, total - 1, frame_count, dtype=int).tolist())
    frames, index = [], 0
    while True:
        ok, frame = capture.read()
        if not ok:
            break
        if index in targets:
            frames.append(frame)
        index += 1
    capture.release()
    if len(frames) != frame_count:
        raise ValueError(f"unable to sample {frame_count} frames from {path}")
    return frames


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--test-root", type=Path, required=True, help="original held-out split containing Fight/ and NonFight/")
    parser.add_argument("--temporal-model", required=True, help="audited local VideoMAE directory; never downloaded by this tool")
    parser.add_argument("--camera-config", type=Path, default=Path("video_pipeline/temporal_fighting_review.json"))
    parser.add_argument("--output-root", type=Path, default=Path("data/raw/rwf2000/evaluation_heldout"))
    parser.add_argument("--device", default="0")
    parser.add_argument("--sample-every", type=int, default=1)
    parser.add_argument("--clip-score-threshold", type=float, default=.5, help="frozen clip-level fight score decision threshold")
    args = parser.parse_args()
    if not 0 <= args.clip_score_threshold <= 1:
        parser.error("--clip-score-threshold must be in [0, 1]")
    clips = discover_heldout_clips(args.test_root)
    camera = camera_config_from_dict(json.loads(args.camera_config.read_text(encoding="utf-8")))
    model = VideoMAEViolenceModel(args.temporal_model, device=args.device)
    rows = []
    args.output_root.mkdir(parents=True, exist_ok=True)
    for clip in clips:
        started = time.perf_counter()
        prediction = model.predict(uniform_frames(clip["path"]))
        clip_latency = time.perf_counter() - started
        adapter = SlidingWindowActionAdapter(model, 16, 8)
        config = PipelineConfig(camera, args.sample_every, args.output_root / "keyframes",
                                args.output_root / "keyframes", device=args.device)
        # ByteTrack state must start clean for each independent held-out clip.
        packets, metrics = process_video(clip["path"], config, UltralyticsByteTrack(device=args.device), action_adapter=adapter)
        packet_path = args.output_root / "packets" / (Path(clip["clip_id"]).stem + ".jsonl")
        packet_path.parent.mkdir(parents=True, exist_ok=True)
        write_jsonl(packets, packet_path)
        rows.append({"clip_id": clip["clip_id"], "is_fight": clip["is_fight"],
                     "clip_fight_score": prediction.class_scores["fight"],
                     "clip_prediction": prediction.class_scores["fight"] >= args.clip_score_threshold,
                     "candidate_prediction": any(packet["trigger"] == "temporal_fighting_candidate" for packet in packets),
                     "candidate_count": len(packets), "clip_inference_seconds": clip_latency,
                     "candidate_metrics": metrics.as_dict(), "packet_jsonl": str(packet_path)})
    report = {"dataset": "RWF-2000", "split": str(args.test_root), "settings": {"clip_score_threshold": args.clip_score_threshold,
              "camera_config": str(args.camera_config), "temporal_model": str(args.temporal_model), "sample_every": args.sample_every},
              "clip_level_videomae": binary_metrics(rows, "clip_prediction"),
              "temporal_candidate": binary_metrics(rows, "candidate_prediction"), "per_clip": rows,
              "caveat": "Metrics are valid only when --test-root is the original untouched held-out split and labels are verified."}
    (args.output_root / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
