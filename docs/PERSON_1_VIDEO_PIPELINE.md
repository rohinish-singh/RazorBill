# Person 1 Guide: Video Ingestion & Event Detection Pipeline

## 1. Ownership & Boundary
- **Directory**: [`video-pipeline/`](../video-pipeline/README.md)
- **Role**: Ingest video streams/files, run frame sampling, execute object detection/tracking, identify candidate anomaly triggers, save key evidence frames, and emit candidate event packets to the processing queue.
- **What You DO NOT Own**:
  - Do NOT run heavy Vision-Language Models (VLMs) or generate natural-language incident summaries (owned by [Person 2](PERSON_2_VLM_CLASSIFICATION.md)).
  - Do NOT write directly to SQLite or create REST APIs (owned by [Person 3](PERSON_3_BACKEND_QUERYING.md)).
  - Do NOT build dashboard visualizations or UI alerts (owned by [Person 4](PERSON_4_FRONTEND_DEMO.md)).

---

## 2. MVP Priorities

1. **Clip Playback & Frame Sampler**: Read video files (e.g. OpenCV `cv2.VideoCapture`) at steady frame intervals (e.g., 2–5 FPS sampling to conserve compute).
2. **Detection & Tracking**: Lightweight detector (e.g., YOLOv8n or basic motion tracker) tracking person bounding boxes and trajectory changes.
3. **Trigger Heuristics**:
   - *Person Down*: Sudden change in bounding box aspect ratio (width > height) or sudden drop in bounding box vertical centroid followed by lack of movement.
   - *Tailgating*: Multiple person tracks entering a designated ROI within a rapid time window (< 1.5s).
4. **Evidence Frame Extractor**: When a trigger fires, export the key frame (`evt_<id>_key.jpg`) and optionally 2 contextual frames to disk (`data/evidence/`).
5. **Non-Blocking Queue Producer**: Push candidate packet to a bounded queue (`queue.Queue(maxsize=50)`). Never block the video stream if the consumer is slow.

---

## 3. Shared Interface: Candidate Event Packet

You must produce JSON packets strictly matching the schema in [`SHARED_CONTRACTS.md`](../SHARED_CONTRACTS.md):

```json
{
  "event_id": "evt_01J8F90A8K72M1",
  "camera_id": "cam_north_gate_01",
  "video_source_id": "warehouse_dock_clip1.mp4",
  "timestamp_seconds": 42.5,
  "frame_path": "data/evidence/evt_01J8F90A8K72M1_key.jpg",
  "frame_paths": [
    "data/evidence/evt_01J8F90A8K72M1_key.jpg"
  ],
  "tracks": [
    {
      "track_id": 12,
      "bbox": [140, 210, 280, 480],
      "class": "person"
    }
  ],
  "trigger": "rapid_aspect_ratio_drop",
  "created_at": "2026-10-15T21:45:00Z"
}
```

### Critical Rules
- `timestamp_seconds`: Floating-point offset within the source video (e.g., `42.5` seconds), NOT wall-clock time.
- `created_at`: UTC ISO-8601 string when detection happened.
- `frame_path`: Valid path on local disk where your code saved the image.

---

## 4. Early Deliverables Schedule

- **Hour 2**: Review and confirm Candidate Event packet schema with [Person 2](PERSON_2_VLM_CLASSIFICATION.md) and [Person 3](PERSON_3_BACKEND_QUERYING.md).
- **Hour 6**: Create runnable stub (`mock_emitter.py`) that reads a video or loop and dumps mock candidate packets + mock JPEG files to disk every 5 seconds.
- **Hour 12**: Working video ingestion loop with OpenCV saving real keyframes to `data/evidence/`.
- **Hour 18**: Connect pipeline to Person 2's VLM inference queue.
- **Hour 24**: Test queue backpressure: drop excess candidate frames cleanly when consumer is saturated and record drop statistics.

