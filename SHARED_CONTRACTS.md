# Shared Contracts and Data Formats

This is the cross-team source of truth. Propose changes in the team chat and update this file before relying on a changed contract.

## Architecture
`Video → Person 1 capture/sample/detect/track → bounded candidate queue → Person 2 VLM/classification → Person 3 FastAPI/SQLite → Person 4 React dashboard`

Person 1 can emit rule-based candidates. Person 2 enriches/classifies them asynchronously. Person 3 owns persisted incident records. Person 4 talks to the backend API only, never directly to SQLite.

## Initial categories
`person_down`, `fighting`, `tailgating`, `crowd_incident`, `suspicious_activity`, `other`, `unknown`

Confirm categories against the footage and model. Do not force uncertain clips into a threat category. Avoid unsupported claims about intent.

## Person 1 → Person 2 candidate packet
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
`timestamp_seconds` is relative to the source video. For live sources, include a wall-clock ISO timestamp if available. Paths must be configurable/relative where possible. Tracks may be empty.

## Person 2 → Person 3 classified incident
```json
{
  "event_id": "evt_unique_id",
  "camera_id": "CAM_01",
  "timestamp_seconds": 134.5,
  "category": "person_down",
  "summary": "A person appears to be lying on the floor near the entrance.",
  "confidence": null,
  "confidence_type": "unavailable",
  "frame_path": "data/frames/CAM_01/evt_unique_id.jpg",
  "source": "vlm",
  "processing_ms": 740,
  "status": "classified",
  "evidence_notes": "Visible posture is consistent with a person on the floor.",
  "created_at": "2026-10-15T10:00:01Z"
}
```
The sample values are illustrative, not measured. `confidence` must be null unless a real score exists; do not ask a generative model to invent a probability. Do not call a score calibrated unless calibrated. `source`: `rule`, `vlm`, or `manual`. `status`: `candidate`, `classified`, `needs_review`, or `failed`. Keep summaries evidence-based.

## Person 3 API baseline
- `GET /health`
- `POST /api/incidents` — validate/upsert by stable `event_id`
- `GET /api/incidents?camera_id=&category=&start=&end=&limit=&offset=`
- `GET /api/incidents/{event_id}`
- `GET /api/stats`
- `POST /api/query` with `{"question":"Show all tailgating events from camera 2 today"}`

Example query response:
```json
{
  "question": "Show all tailgating events from camera 2 today",
  "interpreted_filters": {"camera_id":"CAM_02","category":"tailgating"},
  "answer": "Found 2 matching incidents.",
  "incidents": []
}
```
Use parameterized SQL and a constrained query parser; never execute arbitrary LLM-generated SQL. The database is the source of truth. Unsupported questions should receive a clarification/unsupported response, not fabricated results. Store timestamps consistently (prefer UTC); convert for display. Configure CORS.

## Person 4 contract
Frontend consumes only the API. Use `VITE_API_BASE_URL`, not hardcoded teammate addresses. Build with mock data shaped like the incident schema.

## Latency
Use monotonic timers for durations. Measure frame read, detection, VLM, persistence/API, event-to-alert, and event-to-classified-summary separately. Report model/hardware, image size, sampling rate, sample count, p50/p95 when meaningful, dropped work, false positives, and misses. Do not confuse source-video time with processing time.

## Failure handling
VLM cannot stall capture/detection. Bound queues and count dropped work. Use timeouts, explicit status/errors, and no giant base64 images in SQLite. Store keyframe paths/references.
