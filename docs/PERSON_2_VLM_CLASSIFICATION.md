# Person 2 Guide: Local VLM Inference & Classification

## 1. Ownership & Boundary
- **Directory**: [`vlm-classification/`](../vlm-classification/README.md)
- **Role**: Run local Vision-Language Model (VLM) inference on candidate evidence frames, classify events into standardized categories, generate concise human-readable summaries, measure processing latency, and emit Classified Incident Records.
- **What You DO NOT Own**:
  - Do NOT capture video streams, track bounding boxes, or extract frames (owned by [Person 1](PERSON_1_VIDEO_PIPELINE.md)).
  - Do NOT design database tables, SQLite migrations, or REST API endpoints (owned by [Person 3](PERSON_3_BACKEND_QUERYING.md)).
  - Do NOT create frontend React cards or alert banners (owned by [Person 4](PERSON_4_FRONTEND_DEMO.md)).
  - Do NOT make calls to paid cloud APIs (e.g., OpenAI, Claude, paid AWS endpoints). All models must run locally.

---

## 2. MVP Priorities

1. **Local Model Setup**:
   - Choose a lightweight, fast local VLM with image support (e.g., `SmolVLM-Instruct`, `Moondream2`, `Qwen2-VL-2B-Instruct`, or local Ollama/llama.cpp).
   - Use 4-bit/8-bit quantization or half-precision (`float16` / `bfloat16`) to stay within local hardware memory limits.
2. **Structured Prompting**:
   - Constrain the model output to produce valid JSON containing one of the 7 allowed categories:
     `person_down`, `fighting`, `tailgating`, `crowd_incident`, `suspicious_activity`, `other`, `unknown`.
   - Constrain summary length to 1–2 factual sentences (e.g. *"Individual has fallen to the floor near rack B and is motionless."*).
3. **Asynchronous Consumer**:
   - Run inference in a background worker reading from the candidate queue or folder inbox.
   - Never block video streaming if an inference takes 500ms–2000ms.
4. **Latency Measurement**:
   - Benchmark start to finish per inference: `processing_ms = int((time.time() - start) * 1000)`.
   - Never fabricate benchmark or latency numbers.

---

## 3. Shared Interface: Classified Incident Record

Post the resulting record to Person 3's backend via `POST /api/incidents` matching [`SHARED_CONTRACTS.md`](../SHARED_CONTRACTS.md):

```json
{
  "event_id": "evt_01J8F90A8K72M1",
  "camera_id": "cam_north_gate_01",
  "timestamp_seconds": 42.5,
  "category": "person_down",
  "summary": "Individual fell near pallet loading zone and remains motionless.",
  "confidence": 0.88,
  "confidence_type": "vlm_calibrated",
  "frame_path": "data/evidence/evt_01J8F90A8K72M1_key.jpg",
  "source": "vlm",
  "processing_ms": 430,
  "status": "classified",
  "evidence_notes": "Rapid aspect ratio drop detected; VLM confirmed subject prone on concrete floor.",
  "created_at": "2026-10-15T21:45:00Z"
}
```

### Constraints & Validations
- `category`: Must strictly match one of: `person_down`, `fighting`, `tailgating`, `crowd_incident`, `suspicious_activity`, `other`, `unknown`.
- `source`: `"vlm"`.
- `status`: `"classified"` (or `"needs_review"` if confidence < 0.60).
- `confidence`: Float between `0.0` and `1.0`.

---

## 4. Early Deliverables Schedule

- **Hour 2**: Confirm JSON schemas and prompt output formatting with [Person 3](PERSON_3_BACKEND_QUERYING.md).
- **Hour 6**: Create runnable mock VLM script (`mock_vlm.py`) that reads a candidate packet, waits 200ms, and posts a mock classified incident to `POST /api/incidents`.
- **Hour 12**: Load local model weights locally, test single-frame inference on 3 test images, and verify memory usage.
- **Hour 18**: Connect queue consumer to live pipeline output from [Person 1](PERSON_1_VIDEO_PIPELINE.md).
- **Hour 24**: Benchmark cold-start vs warm inference latency; verify fallback behavior if prompt output fails JSON validation.

