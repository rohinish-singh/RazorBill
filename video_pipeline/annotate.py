"""Export an inspection-only annotated copy of a Person 1 source video."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .pipeline import DetectorTracker, UltralyticsByteTrack


def export_annotated_video(source: str | Path, output: str | Path, detector: DetectorTracker) -> dict:
    """Write boxes, ByteTrack IDs, and source-relative timestamps without changing source."""
    try:
        import cv2
    except ImportError as error:
        raise RuntimeError("OpenCV is required for annotation export") from error

    capture = cv2.VideoCapture(str(source))
    if not capture.isOpened():
        raise FileNotFoundError(f"unable to open video source: {source}")
    width, height = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)), int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = capture.get(cv2.CAP_PROP_FPS) or 30.0
    destination = Path(output); destination.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(str(destination), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))
    if not writer.isOpened():
        capture.release()
        raise OSError(f"unable to create annotated video: {destination}")

    observations: list[dict] = []
    frame_index = 0
    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            timestamp = frame_index / fps
            tracks = detector.tracks(frame)
            for track in tracks:
                x1, y1, x2, y2 = (round(value) for value in track.bbox_xyxy)
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 220, 0), 2)
                cv2.putText(frame, f"person #{track.track_id}", (x1, max(18, y1 - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 220, 0), 2, cv2.LINE_AA)
            cv2.putText(frame, f"source t={timestamp:.3f}s  frame={frame_index}", (12, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 220, 0), 2, cv2.LINE_AA)
            writer.write(frame)
            observations.append({"frame_index": frame_index, "timestamp_seconds": timestamp,
                                 "tracks": [{"track_id": track.track_id, "bbox_xyxy": list(track.bbox_xyxy), "footpoint": list(track.footpoint)} for track in tracks]})
            frame_index += 1
    finally:
        capture.release(); writer.release()
    return {"source": str(source), "annotated_video": str(destination), "width": width, "height": height,
            "fps": fps, "frames": frame_index, "observations": observations}


def main() -> int:
    parser = argparse.ArgumentParser(description="Export YOLO/ByteTrack annotations for a local video")
    parser.add_argument("video"); parser.add_argument("--output", required=True); parser.add_argument("--track-report")
    parser.add_argument("--device", default="0"); parser.add_argument("--confidence", type=float, default=0.30)
    args = parser.parse_args()
    report = export_annotated_video(args.video, args.output, UltralyticsByteTrack(confidence=args.confidence, device=args.device))
    if args.track_report:
        Path(args.track_report).parent.mkdir(parents=True, exist_ok=True)
        Path(args.track_report).write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "observations"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
