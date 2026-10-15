# RazorBill — Video Pipeline

**Owner**: Person 1  
**Detailed Guide**: [`../docs/PERSON_1_VIDEO_PIPELINE.md`](../docs/PERSON_1_VIDEO_PIPELINE.md)  
**Contract Reference**: [`../SHARED_CONTRACTS.md`](../SHARED_CONTRACTS.md)  
**Reference Repository**: [Devnil434/Eagle](https://github.com/Devnil434/Eagle)

---

## Overview

The `video-pipeline/` module handles video ingestion (pre-recorded clips and simulated live streams), frame sampling, object detection and tracking, anomaly trigger evaluation, and keyframe extraction. When an anomaly is detected, it packages a **Candidate Event Packet** and pushes it to a bounded queue or callback for Person 2.

---

## Planned Directory Structure

```
video-pipeline/
├── README.md
├── requirements.txt
├── src/
│   ├── ingestion.py       # Video capture and frame sampling loop
│   ├── detection.py       # Object detection & bounding box tracking (inspect Eagle)
│   ├── heuristics.py      # Rule triggers (aspect ratio drop, trajectory convergence)
│   ├── evidence.py        # Frame exporter and path generator (data/frames/CAM_XX/...)
│   └── queue_producer.py  # Bounded queue worker and drop counter
├── tests/
│   └── test_heuristics.py # Unit tests on trigger heuristics
└── mock_emitter.py        # Hour 6 mock candidate generator for integration
```

---

## Quickstart & Environment

```bash
# From repository root or video-pipeline/
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Key Dependencies
- `opencv-python-headless`
- `numpy`
- `pydantic`

---

## Candidate Event Packet Format

```json
{
  "event_id": "evt_unique_id",
  "camera_id": "CAM_01",
  "video_source_id": "demo_video_01",
  "timestamp_seconds": 134.5,
  "frame_path": "data/frames/CAM_01/evt_unique_id.jpg",
  "frame_paths": [],
  "tracks": [
    {"track_id": 12, "class_name": "person", "bbox_xyxy": [120, 80, 260, 410]}
  ],
  "trigger": "sampled_frame",
  "created_at": "2026-10-15T10:00:00Z"
}
```

---

## Core Engineering Directives

1. **Non-Blocking Execution**: The video capture loop must push candidate packets to a bounded queue. Never block frame capture waiting for downstream VLM inference.
2. **Distinct Timestamps**: Record source video offset (`timestamp_seconds`) distinctly from wall-clock time (`created_at`).
3. **Keyframe Storage**: Save JPEG frames under a configurable relative path (`data/frames/CAM_XX/evt_<id>.jpg`). Store file paths only, never raw image bytes in SQLite.
4. **Mock Stub Ready**: Provide `mock_emitter.py` early so Person 2, Person 3, and Person 4 can develop without waiting for detector calibration.

# Person 1 implementation

The runnable implementation is the importable `video_pipeline` package at repository root. It streams a local file; YOLO11n only detects COCO people, invokes Ultralytics ByteTrack, passes `Track` records to `behavioral_markers`, saves event keyframes, and emits only the authoritative Person 1 candidate packet shape.

```powershell
python -m pip install -e ".[person1]"
python -m video_pipeline path\\to\\video.mp4 --camera-config video_pipeline\\example_camera.json --device cpu
```

`--device cuda:0` is available only when the installed PyTorch build has CUDA support. VLM inference is intentionally absent from this process; connect the optional callback or bounded queue in the integration owner’s code.
