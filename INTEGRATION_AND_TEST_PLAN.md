# RazorBill Integration and Test Plan (36-Hour Hackathon)

This document establishes the milestone timeline, integration gates, test criteria, and fallback procedures for the 36-hour Honeywell hackathon project.

---

## 1. 36-Hour Milestones & Checkpoints

```
[Hour 0] Kickoff & Setup
    │
[Hour 2] Milestone 1: Contracts Formally Agreed
    │
[Hour 6] Milestone 2: Runnable Stubs & Mock Payloads
    │
[Hour 12] Milestone 3: First End-to-End Vertical Slice (Mocks -> API -> UI)
    │
[Hour 18] Milestone 4: Real Component Integration (Live Video + Local VLM)
    │
[Hour 24] Milestone 5: Latency, Backpressure & Failure Stress Testing
    │
[Hour 30] Milestone 6: Feature Freeze & Polish
    │
[Hour 33] Milestone 7: Full Demo Rehearsal (with Seeded Fallback Readiness)
    │
[Hour 36] Final Presentation & Submission
```

---

### Detailed Milestone Gates

| Hour | Milestone | Deliverable | Acceptance Criteria |
| :--- | :--- | :--- | :--- |
| **Hour 2** | **Contracts Agreed** | Signoff on `SHARED_CONTRACTS.md` by all 4 owners. | Schema types, field names, allowed categories, API paths, and error envelopes finalized. |
| **Hour 6** | **Runnable Stubs & Mock Payloads** | - P1: Synthetic frame generator & candidate JSON emitter.<br>- P2: Mock VLM returning deterministic classified incident.<br>- P3: FastAPI stub with SQLite storing and querying mock data.<br>- P4: Vite/React stub displaying mock incident cards. | Each sub-project runs locally and outputs contract-compliant JSON. |
| **Hour 12** | **First End-to-End Slice** | Synthetic video candidate $\to$ mock VLM $\to$ `POST /api/incidents` $\to$ React UI auto-refresh. | A synthetic event initiated from video stub appears in the frontend dashboard without manual DB edits. |
| **Hour 18** | **Real Component Integration** | Real video ingestion (OpenCV/trackers) and local VLM inference (e.g., Qwen2-VL / Moondream / SmolVLM) wired up. | Video clip triggers candidate, local VLM classifies event within bounded latency, incident persists in SQLite. |
| **Hour 24** | **Latency & Failure Testing** | Queue stress testing, dropped frame handling, cold-start latency measurement, long video clip verification. | Video capture does not crash or block when VLM queue is saturated. Dropped count is accurately logged. |
| **Hour 30** | **Feature Freeze** | Code freeze on all new features. Focus exclusively on bug fixes, UI polish, and demo scripts. | No new API endpoints or schema changes. Query parser test suite passing 100%. |
| **Hour 33** | **Demo Rehearsal** | 3 end-to-end dry runs of the exact 5-minute presentation script. | Prepared demo clip runs cleanly; seeded fallback mode tested and operational within 1 toggle. |

---

## 2. Test Plan by Component

### 2.1 Video Pipeline (`video-pipeline/` - Person 1)
- **Unit / Stub Test**: Feed 30-second benchmark clip (`warehouse_sample.mp4`). Verify candidate packets are emitted with valid `timestamp_seconds`, bounding boxes, and saved JPEG evidence frames.
- **Queue Test**: Connect pipeline to a simulated slow consumer (5000ms delay). Verify queue bounds prevent memory exhaustion and dropped candidate counts are tracked.
- **Evidence Storage Test**: Confirm evidence images write to `data/evidence/` with unique paths matching `frame_path`.

### 2.2 VLM Classification (`vlm-classification/` - Person 2)
- **Prompt Validation**: Verify prompt outputs strictly conform to allowed categories: `person_down`, `fighting`, `tailgating`, `crowd_incident`, `suspicious_activity`, `other`, `unknown`.
- **Latency Benchmark**: Measure single-frame inference time on target hardware. Log exact milliseconds into `processing_ms` (never invent numbers).
- **Asynchronous Execution**: Ensure inference worker operates on background thread/process decoupled from video frame ingestion.

### 2.3 Backend & Query Engine (`backend/` - Person 3)
- **Contract Conformance**: Validate Pydantic models for Candidate Event and Classified Incident schemas.
- **Upsert Validation**: Calling `POST /api/incidents` with the same `event_id` updates existing record without duplicate primary keys.
- **Parameterized SQL Security**: Run injection test payloads (e.g., `' OR '1'='1`) against `POST /api/query`. Verify only allowlisted filters are applied to parameterized SQL.
- **Health & Stats API**: Confirm `GET /health` and `GET /stats` calculate aggregated metrics dynamically from SQLite.

### 2.4 Frontend Dashboard (`frontend/` - Person 4)
- **Card & Grid Render**: Render incident list with timestamp, camera tag, category badge, and evidence thumbnail.
- **Filter Controls**: Category dropdown, camera filter, and search box correctly query backend query parameters.
- **Conversational Query Panel**: Input natural-language query, display interpreted filter badges, and render matched incident cards.
- **Error State Handling**: Render clean empty states and informative error banners when backend is offline.

---

## 3. Seeded Demo Dataset & Failover Strategy

To ensure a resilient presentation during the hackathon demo:

1. **Prepared Benchmark Clips**:
   - `demo_person_down.mp4` (Clear fallen worker scenario)
   - `demo_tailgating.mp4` (Turnstile double-entry scenario)
   - `demo_normal_traffic.mp4` (Negative control, no false triggers)
2. **Seeded SQLite Fallback**:
   - A pre-populated SQLite database (`data/demo_seed.db`) containing 25 realistic incidents across various cameras and categories.
   - If local VLM inference exhibits thermal throttling or GPU OOM during live judging, backend can be toggled to `--demo-seed` mode to demonstrate search, filtering, and summarization reliably.
3. **Hardware Isolation**:
   - VLM inference must be configured with explicit memory caps (e.g., 4-bit quantization, max tokens: 128) to prevent system freezing.

