# RazorBill

> **Live Video Event Summarization, Classification, and Conversational Querying**  
> *Honeywell 36-Hour Hackathon Project*

RazorBill is an edge-first intelligent surveillance intelligence platform. It ingests live or recorded video streams, detects potential physical security anomalies using lightweight tracking heuristics, runs local Vision-Language Models (VLMs) to classify and summarize incidents in real time, persists structured event records in SQLite via FastAPI, and presents an interactive dashboard with deterministic natural-language querying for safety and security operators.

---

## Architecture Overview

```
[Video Source / Camera]
       │
       ▼
[video-pipeline/] (Person 1)
  - Frame sampling (OpenCV)
  - Person tracking & motion heuristics
  - Evidence frame extraction
       │
       ▼  (Candidate Event Packet via bounded queue)
[vlm-classification/] (Person 2)
  - Local VLM inference (e.g., SmolVLM / Qwen2-VL / Moondream)
  - 1-2 sentence event summarization
  - Categorization into 7 canonical categories
  - Processing latency measurement
       │
       ▼  (Classified Incident via POST /api/incidents)
[backend/] (Person 3)
  - FastAPI server
  - SQLite persistence (upsert by event_id)
  - Filtered listing & aggregate statistics
  - Deterministic NL query parser (parameterized SQL)
  - Static evidence frame delivery
       │
       ▼  (REST API / JSON)
[frontend/] (Person 4)
  - React + Vite + TypeScript dashboard
  - Live incident feed & evidence thumbnails
  - Filter controls (category, camera, status)
  - Conversational query interface
  - Demo failover & scenario controls
```

---

## Team Responsibilities & Ownership

| Workstream | Owner | Module Directory | Detailed Guide | Core Responsibilities |
| :--- | :--- | :--- | :--- | :--- |
| **Video Pipeline** | **Person 1** | [`video-pipeline/`](video-pipeline/README.md) | [`docs/PERSON_1_VIDEO_PIPELINE.md`](docs/PERSON_1_VIDEO_PIPELINE.md) | Video ingestion, sampling, detection/tracking, evidence frames, candidate event packets. |
| **VLM Classification** | **Person 2** | [`vlm-classification/`](vlm-classification/README.md) | [`docs/PERSON_2_VLM_CLASSIFICATION.md`](docs/PERSON_2_VLM_CLASSIFICATION.md) | Local VLM inference, incident classification, summarization, async queue consumer. |
| **Backend & Querying** | **Person 3** | [`backend/`](backend/README.md) | [`docs/PERSON_3_BACKEND_QUERYING.md`](docs/PERSON_3_BACKEND_QUERYING.md) | FastAPI, SQLite, incident persistence, filters, statistics, deterministic NL query parsing. |
| **Frontend & Demo** | **Person 4** | [`frontend/`](frontend/README.md) | [`docs/PERSON_4_FRONTEND_DEMO.md`](docs/PERSON_4_FRONTEND_DEMO.md) | React/Vite/TS UI, API integration, incident views, filters, query interface, demo experience. |

---

## Repository Structure

```
RazorBill/
├── README.md                          # Master project documentation
├── SHARED_CONTRACTS.md                # Data schemas, enums, payload contracts, API specs
├── INTEGRATION_AND_TEST_PLAN.md       # 36-hour schedule, milestones, test gates, fallbacks
├── .gitignore                         # Build, venv, model weight, media, and cache exclusions
├── docs/
│   ├── PERSON_1_VIDEO_PIPELINE.md     # Person 1 ownership, boundaries, MVP & deliverables
│   ├── PERSON_2_VLM_CLASSIFICATION.md # Person 2 ownership, boundaries, MVP & deliverables
│   ├── PERSON_3_BACKEND_QUERYING.md   # Person 3 ownership, boundaries, MVP & deliverables
│   └── PERSON_4_FRONTEND_DEMO.md      # Person 4 ownership, boundaries, MVP & deliverables
├── video-pipeline/                    # Video ingestion & anomaly trigger heuristics
│   └── README.md
├── vlm-classification/                # Local VLM inference & structured summarizer
│   └── README.md
├── backend/                           # FastAPI backend, SQLite DB & NL query engine
│   └── README.md
└── frontend/                          # React + Vite + TypeScript dashboard
    └── README.md
```

---

## Shared Contracts Summary

Detailed schemas and sample JSON payloads are codified in [`SHARED_CONTRACTS.md`](SHARED_CONTRACTS.md).

### Standard Incident Categories
- `person_down`
- `fighting`
- `tailgating`
- `crowd_incident`
- `suspicious_activity`
- `other`
- `unknown`

### Core Schemas
1. **Candidate Event Packet** (`video-pipeline/` $\to$ Queue):
   - `event_id`, `camera_id`, `video_source_id`, `timestamp_seconds`, `frame_path`, `frame_paths`, `tracks`, `trigger`, `created_at`
2. **Classified Incident Record** (`vlm-classification/` $\to$ `backend/`):
   - `event_id`, `camera_id`, `timestamp_seconds`, `category`, `summary`, `confidence`, `confidence_type`, `frame_path`, `source`, `processing_ms`, `status`, `evidence_notes`, `created_at`
3. **Allowed `source` Values**: `rule`, `vlm`, `manual`
4. **Allowed `status` Values**: `candidate`, `classified`, `needs_review`, `failed`

### Baseline REST API
- `GET /health`
- `POST /api/incidents` (upsert by `event_id`)
- `GET /api/incidents` (with camera, category, time filters, limit, offset, total count)
- `GET /api/incidents/{event_id}`
- `GET /api/stats`
- `POST /api/query` (safe NL query parser via parameterized SQL)

---

## Non-Negotiable Engineering Rules

1. **No Paid Cloud Inference**: All model inference runs strictly locally (e.g., Qwen2-VL, SmolVLM, Moondream2, Ollama). No OpenAI/Claude API keys.
2. **Non-Blocking Architecture**: VLM inference must never block video capture. Use bounded queues (`maxsize=50`) and track dropped or deferred frames.
3. **Paths, Not Blobs in DB**: Store relative evidence image paths (`data/evidence/<event_id>.jpg`) in SQLite. Never store raw image bytes or base64 blobs in the database.
4. **Distinct Timestamps**: Maintain a strict separation between source video offset (`timestamp_seconds`, float) and UTC wall-clock time (`created_at`, ISO 8601).
5. **No Hallucinated Benchmarks**: Do not invent fake confidence scores, latency figures, or accuracy metrics. Real measurements only.
6. **SQL Safety**: The natural-language query engine converts questions to allowlisted filter parameters executed via parameterized SQL. Arbitrary model-generated SQL execution is strictly forbidden.
7. **Demo Resilience**: Always maintain a prepared demo video clip and a pre-populated SQLite seed fallback (`seed_demo_data.py`) to guarantee an unshakeable live pitch.
8. **Keep It Lean**: No Redis, Kubernetes, Docker Swarm, microservices, complex auth, or unrelated infrastructure.

---

## 36-Hour Integration Checkpoints

Full details in [`INTEGRATION_AND_TEST_PLAN.md`](INTEGRATION_AND_TEST_PLAN.md).

- **Hour 2**: Contracts Formally Agreed.
- **Hour 6**: Runnable Stubs & Mock Payloads.
- **Hour 12**: First End-to-End Vertical Slice (Mock Video $\to$ Mock VLM $\to$ Real API $\to$ Real UI).
- **Hour 18**: Real Component Integration (Real Video + Real Local VLM).
- **Hour 24**: Latency, Backpressure & Failure Stress Testing.
- **Hour 30**: Feature Freeze (Bug fixes and UI polish only).
- **Hour 33**: Full Demo Rehearsal (with Seeded Fallback Readiness).
- **Hour 36**: Final Presentation.

---

## Current Setup Status

- [x] Initial repository scaffold established.
- [x] Strict data contracts and API specifications codified in [`SHARED_CONTRACTS.md`](SHARED_CONTRACTS.md).
- [x] 36-hour integration milestones and test gates codified in [`INTEGRATION_AND_TEST_PLAN.md`](INTEGRATION_AND_TEST_PLAN.md).
- [x] Team ownership documentation created in [`docs/`](docs/).
- [x] Subsystem documentation initialized in component directories.
- [ ] Hour 6 Deliverable: Component mock stubs and sample payloads.

