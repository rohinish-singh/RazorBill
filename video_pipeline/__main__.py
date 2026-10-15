from __future__ import annotations

import argparse
from pathlib import Path

from behavioral_markers.config import camera_config_from_dict
from .pipeline import PipelineConfig, UltralyticsByteTrack, process_video, write_jsonl

def main() -> int:
    parser = argparse.ArgumentParser(description="Person 1 video → YOLO11n/ByteTrack → marker candidate packets")
    parser.add_argument("video"); parser.add_argument("--camera-config", required=True)
    parser.add_argument("--sample-every", type=int, default=3); parser.add_argument("--device")
    parser.add_argument("--output-root", default="data/frames"); parser.add_argument("--jsonl", default="reports/candidates.jsonl")
    args = parser.parse_args()
    import json
    camera = camera_config_from_dict(json.loads(Path(args.camera_config).read_text(encoding="utf-8")))
    config = PipelineConfig(camera, args.sample_every, Path(args.output_root), device=args.device)
    packets, metrics = process_video(args.video, config, UltralyticsByteTrack(confidence=config.confidence, device=args.device))
    write_jsonl(packets, args.jsonl); print(json.dumps(metrics.as_dict(), indent=2)); print(f"candidate_packets={len(packets)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
