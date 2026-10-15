# RazorBill Shared Contracts & Data Schemas

This document defines the strict integration contracts between all components of **RazorBill**:
1. `video-pipeline/` (Person 1)
2. `vlm-classification/` (Person 2)
3. `backend/` (Person 3)
4. `frontend/` (Person 4)

All team members must conform to the field names, types, and allowed values defined here.

---

## 1. Allowed Enumerations

### 1.1 Incident Categories
All incidents must belong to one of the following 7 standardized categories:
- `person_down`: Worker or visitor fallen or collapsed.
- `fighting`: Physical altercation, aggressive struggle.
- `tailgating`: Unauthorized follower closely entering a secured access portal.
- `crowd_incident`: Rapid crowd formation, rush, or bottleneck in restricted zones.
- `suspicious_activity`: Loitering in unauthorized zone, perimeter breaches, bag abandonment.
- `other`: Noticeable anomaly not fitting the above definitions.
- `unknown`: Unclear video capture, heavy occlusion, or low confidence.

### 1.2 Allowed Source Values
Identifies the mechanism that produced the classification:
- `rule`: Fast heuristic/tracker rule trigger (e.g., bounding box aspect ratio drop for person down, rapid trajectory convergence for fight).
- `vlm`: Local Vision-Language Model classification and summarization.
- `manual`: Operator manual override or submission via frontend.

### 1.3 Allowed Status Values
Identifies the verification lifecycle of the event:
- `candidate`: Pre-VLM candidate event packet emitted by video pipeline.
- `classified`: Processed and labeled by local VLM.
- `needs_review`: Ambiguous event flagged for human operator review (low confidence or conflicting cues).
- `failed`: Pipeline or inference failure (logged for observability).

---

## 2. Event Schemas

### 2.1 Candidate Event Packet (Pipeline $\to$ VLM & Queue)
Produced by `video-pipeline/` when motion/track heuristics indicate an anomaly.

| Field | Type | Description | Example |
| :--- | :--- | :--- | :--- |
| `event_id` | string (UUIDv4) | Unique event identifier | `"evt_01J8F90A8K72M1"` |
| `camera_id` | string | Camera/Stream identifier | `"cam_north_gate_01"` |
| `video_source_id` | string | Source file or stream URL | `"warehouse_dock_clip1.mp4"` |
| `timestamp_seconds`| float | Offset in source video (seconds) | `42.5` |
| `frame_path` | string | Key evidence frame path on disk | `"data/evidence/evt_01J8F90A8K72M1_key.jpg"` |
| `frame_paths` | list[string] | Sequence of candidate frames | `["data/evidence/evt_..._01.jpg", "data/evidence/evt_..._02.jpg"]` |
| `tracks` | list[object] | Track bounding boxes and object IDs | `[{"track_id": 4, "bbox": [120, 80, 240, 310], "class": "person"}]` |
| `trigger` | string | Rule or heuristic that triggered the candidate | `"rapid_aspect_ratio_drop"` |
| `created_at` | string (ISO 8601 UTC) | Wall-clock detection timestamp | `"2026-10-15T21:45:00Z"` |

#### Sample Candidate Event Payload
```json
{
  "event_id": "evt_01J8F90A8K72M1",
  "camera_id": "cam_north_gate_01",
  "video_source_id": "warehouse_dock_clip1.mp4",
  "timestamp_seconds": 42.5,
  "frame_path": "data/evidence/evt_01J8F90A8K72M1_key.jpg",
  "frame_paths": [
    "data/evidence/evt_01J8F90A8K72M1_01.jpg",
    "data/evidence/evt_01J8F90A8K72M1_02.jpg",
    "data/evidence/evt_01J8F90A8K72M1_key.jpg"
  ],
  "tracks": [
    {
      "track_id": 12,
      "bbox": [140, 210, 280, 480],
      "class": "person",
      "velocity": 0.05
    }
  ],
  "trigger": "rapid_aspect_ratio_drop",
  "created_at": "2026-10-15T21:45:00Z"
}
```

---

### 2.2 Classified Incident Record (VLM / Pipeline $\to$ Backend)
Emitted by `vlm-classification/` after local multimodal inference, and persisted in SQLite by `backend/`.

| Field | Type | Description | Example |
| :--- | :--- | :--- | :--- |
| `event_id` | string (UUIDv4) | Unique event identifier (matches candidate packet) | `"evt_01J8F90A8K72M1"` |
| `camera_id` | string | Camera/Stream identifier | `"cam_north_gate_01"` |
| `timestamp_seconds`| float | Source video offset in seconds | `42.5` |
| `category` | string | One of the 7 allowed categories | `"person_down"` |
| `summary` | string | Concise 1-2 sentence human-readable description | `"Individual fell near pallet loading zone and remains motionless."` |
| `confidence` | float | Model or rule confidence in range [0.0, 1.0] | `0.88` |
| `confidence_type` | string | Confidence methodology (`vlm_calibrated`, `heuristic`, `manual`) | `"vlm_calibrated"` |
| `frame_path` | string | Relative path to principal evidence frame | `"data/evidence/evt_01J8F90A8K72M1_key.jpg"` |
| `source` | string | Allowed source: `rule`, `vlm`, `manual` | `"vlm"` |
| `processing_ms` | integer | Total inference & analysis latency in milliseconds | `430` |
| `status` | string | Allowed status: `candidate`, `classified`, `needs_review`, `failed` | `"classified"` |
| `evidence_notes` | string | Diagnostic or detection notes | `"Motion ceased at t=41.8s; bounding box height decreased by 65%."` |
| `created_at` | string (ISO 8601 UTC) | Wall-clock detection timestamp | `"2026-10-15T21:45:00Z"` |

#### Sample Classified Incident Payload
```json
{
  "event_id": "evt_01J8F90A8K72M1",
  "camera_id": "cam_north_gate_01",
  "timestamp_seconds": 42.5,
  "category": "person_down",
  "summary": "Individual slipped near dock door 4 and remains stationary on the floor.",
  "confidence": 0.88,
  "confidence_type": "vlm_calibrated",
  "frame_path": "data/evidence/evt_01J8F90A8K72M1_key.jpg",
  "source": "vlm",
  "processing_ms": 430,
  "status": "classified",
  "evidence_notes": "Rapid aspect ratio drop detected at 42.1s; VLM confirms prone human subject.",
  "created_at": "2026-10-15T21:45:00Z"
}
```

---

## 3. Baseline REST API Specification (Backend)

Base URL: `http://localhost:8000`

### 3.1 `GET /health`
Returns system health status and component checks.
- **Response** (`200 OK`):
  ```json
  {
    "status": "healthy",
    "uptime_seconds": 1284,
    "database": "connected",
    "version": "0.1.0"
  }
  ```

---

### 3.2 `POST /api/incidents`
Upserts an incident record by `event_id`. If `event_id` exists, it updates fields (e.g., transition from `candidate` to `classified`); if not, it inserts.
- **Request Body**: Classified Incident Record (or Candidate packet converted to incident schema with status `candidate`).
- **Response** (`200 OK` or `201 Created`):
  ```json
  {
    "success": true,
    "event_id": "evt_01J8F90A8K72M1",
    "action": "upserted",
    "status": "classified"
  }
  ```

---

### 3.3 `GET /api/incidents`
Query paginated incidents with filtering.
- **Query Parameters**:
  - `camera_id` (optional, string)
  - `category` (optional, string: one of 7 categories)
  - `status` (optional, string: one of 4 status values)
  - `start_time` (optional, ISO 8601 UTC string or float video timestamp)
  - `end_time` (optional, ISO 8601 UTC string or float video timestamp)
  - `limit` (integer, default `50`, max `200`)
  - `offset` (integer, default `0`)
- **Response** (`200 OK`):
  ```json
  {
    "total": 1,
    "limit": 50,
    "offset": 0,
    "items": [
      {
        "event_id": "evt_01J8F90A8K72M1",
        "camera_id": "cam_north_gate_01",
        "timestamp_seconds": 42.5,
        "category": "person_down",
        "summary": "Individual slipped near dock door 4 and remains stationary on the floor.",
        "confidence": 0.88,
        "confidence_type": "vlm_calibrated",
        "frame_path": "data/evidence/evt_01J8F90A8K72M1_key.jpg",
        "source": "vlm",
        "processing_ms": 430,
        "status": "classified",
        "evidence_notes": "Rapid aspect ratio drop detected at 42.1s; VLM confirms prone human subject.",
        "created_at": "2026-10-15T21:45:00Z"
      }
    ]
  }
  ```

---

### 3.4 `GET /api/incidents/{event_id}`
Retrieve a single incident by its unique ID.
- **Response** (`200 OK`): Returns incident object.
- **Response** (`404 Not Found`): If `event_id` does not exist.

---

### 3.5 `GET /api/stats`
Summary statistics for dashboard metrics and charts.
- **Response** (`200 OK`):
  ```json
  {
    "total_incidents": 42,
    "by_category": {
      "person_down": 8,
      "fighting": 3,
      "tailgating": 14,
      "crowd_incident": 4,
      "suspicious_activity": 11,
      "other": 2,
      "unknown": 0
    },
    "by_status": {
      "classified": 36,
      "needs_review": 5,
      "candidate": 1,
      "failed": 0
    },
    "by_camera": {
      "cam_north_gate_01": 22,
      "cam_loading_dock_02": 20
    },
    "recent_activity_count": 6
  }
  ```

---

### 3.6 `POST /api/query`
Natural-language conversational querying over incident records.
- **Security Rule**: The backend parses NL queries into allowlisted parameters (`category`, `camera_id`, `time_range`, `status`) and executes **only parameterized SQL**. It **NEVER** runs raw or model-generated SQL.
- **Request Body**:
  ```json
  {
    "query": "Show me all tailgating events at the north gate in the last hour"
  }
  ```
- **Response (Resolved Query - 200 OK)**:
  ```json
  {
    "query": "Show me all tailgating events at the north gate in the last hour",
    "interpreted_intent": {
      "category": "tailgating",
      "camera_id": "cam_north_gate_01",
      "time_window": "last_hour"
    },
    "match_count": 2,
    "results": [
      {
        "event_id": "evt_01J8FA...",
        "camera_id": "cam_north_gate_01",
        "timestamp_seconds": 184.2,
        "category": "tailgating",
        "summary": "Second person entered turnstile within 1.2s without badge swipe.",
        "confidence": 0.94,
        "frame_path": "data/evidence/evt_01J8FA_key.jpg",
        "created_at": "2026-10-15T21:10:00Z"
      }
    ],
    "explanation": "Filtered by category 'tailgating' on camera 'cam_north_gate_01' within the last 60 minutes."
  }
  ```
- **Response (Unsupported / Unclear Query - 200 OK)**:
  ```json
  {
    "query": "What color was the intruder's shoes?",
    "interpreted_intent": null,
    "match_count": 0,
    "results": [],
    "status": "unsupported",
    "message": "Query cannot be mapped to allowlisted filters. RazorBill supports queries filtering by category (e.g. person down, tailgating), camera ID, and time window."
  }
  ```

---

## 4. Fundamental Engineering Guidelines

1. **Evidence Frames vs Image Bytes**: Never store raw image bytes or base64 blobs in SQLite. Store relative disk paths (`data/evidence/<event_id>.jpg`). Backend exposes static frame serving.
2. **Dual Timestamps**: Always distinguish `timestamp_seconds` (float position inside the video file) from `created_at` (UTC ISO 8601 timestamp of processing).
3. **No Fabricated Data**: Never invent confidence scores, processing latencies, or fake accuracy metrics. All metrics must reflect real measurements or explicitly tagged sample data.
4. **Resilience**: The video capture loop must push to a bounded queue (`maxsize=50`). If VLM latency spikes, drop or defer work and increment a `dropped_candidates` counter rather than locking the ingestion stream.

