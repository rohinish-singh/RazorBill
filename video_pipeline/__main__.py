from __future__ import annotations

import argparse
from pathlib import Path

from behavioral_markers.config import camera_config_from_dict
from .pipeline import PipelineConfig, UltralyticsByteTrack, UltralyticsObjectFlagDetector, process_video, write_jsonl
from .pose import UltralyticsPoseEstimator


def _weapon_labels(items: list[str]) -> dict[int, str]:
    labels = {}
    for item in items:
        try:
            class_id, label = item.split("=", 1); labels[int(class_id)] = label.lower()
        except ValueError as error:
            raise ValueError("--object-label must use CLASS_ID=knife or CLASS_ID=firearm") from error
    return labels

def main() -> int:
    parser = argparse.ArgumentParser(description="Person 1 video → YOLO11n/ByteTrack → marker candidate packets")
    parser.add_argument("video"); parser.add_argument("--camera-config", required=True)
    parser.add_argument("--sample-every", type=int, default=3); parser.add_argument("--device")
    parser.add_argument("--output-root", default="data/frames"); parser.add_argument("--jsonl", default="reports/candidates.jsonl")
    parser.add_argument("--frame-path-root", default="data/frames", help="relative root written into candidate frame_path fields")
    parser.add_argument("--object-model", help="optional specialized knife/firearm detector weights")
    parser.add_argument("--object-label", action="append", default=[], metavar="CLASS_ID=LABEL", help="explicit weapon-model class mapping; LABEL is knife or firearm")
    parser.add_argument("--pose-model", help="optional YOLO pose weights, for example yolo11n-pose.pt")
    parser.add_argument("--pose-every", type=int, default=1)
    parser.add_argument("--evidence-pre-seconds", type=float, default=0.0)
    parser.add_argument("--evidence-post-seconds", type=float, default=0.0)
    parser.add_argument("--evidence-root", help="optional local output root for evidence clips and index.jsonl")
    parser.add_argument("--relative-evidence-root", help="relative root written in the optional evidence sidecar index")
    args = parser.parse_args()
    import json
    camera = camera_config_from_dict(json.loads(Path(args.camera_config).read_text(encoding="utf-8")))
    config = PipelineConfig(camera, args.sample_every, Path(args.output_root), Path(args.frame_path_root), device=args.device,
                            pose_every=args.pose_every, evidence_pre_seconds=args.evidence_pre_seconds,
                            evidence_post_seconds=args.evidence_post_seconds,
                            evidence_root=Path(args.evidence_root) if args.evidence_root else None,
                            relative_evidence_root=Path(args.relative_evidence_root) if args.relative_evidence_root else None)
    labels = _weapon_labels(args.object_label)
    if args.object_model and not labels:
        parser.error("--object-model requires one or more --object-label CLASS_ID=knife|firearm mappings")
    if labels and not args.object_model:
        parser.error("--object-label requires --object-model")
    object_detector = UltralyticsObjectFlagDetector(args.object_model, labels, device=args.device) if args.object_model else None
    pose_estimator = UltralyticsPoseEstimator(args.pose_model, device=args.device) if args.pose_model else None
    packets, metrics = process_video(args.video, config, UltralyticsByteTrack(confidence=config.confidence, device=args.device), object_detector=object_detector, pose_estimator=pose_estimator)
    write_jsonl(packets, args.jsonl); print(json.dumps(metrics.as_dict(), indent=2)); print(f"candidate_packets={len(packets)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
