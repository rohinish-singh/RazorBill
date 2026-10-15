# RazorBill — Backend API & Query Engine

**Owner**: Person 3  
**Detailed Guide**: [`../docs/PERSON_3_BACKEND_QUERYING.md`](../docs/PERSON_3_BACKEND_QUERYING.md)  
**Contract Reference**: [`../SHARED_CONTRACTS.md`](../SHARED_CONTRACTS.md)

---

## Overview

The `backend/` module is built using **FastAPI** and **SQLite**. It serves as the stored incident source of truth. It validates and persists candidate and classified incidents via upsert, serves evidence keyframe images statically, provides filtered queries and aggregated stats to the frontend, and powers safe conversational natural-language querying via constrained parameterized SQL execution.

---

## Planned Directory Structure

```
backend/
├── README.md
├── requirements.txt
├── src/
│   ├── main.py            # FastAPI entrypoint, CORS & static mounting
│   ├── config.py          # App settings (database path, evidence directory)
│   ├── database.py        # SQLite connection pool and schema migrations
│   ├── models.py          # Pydantic schemas (Incident, Query, Stats)
│   ├── routes/
│   │   ├── incidents.py   # GET/POST /api/incidents and GET /api/incidents/{id}
│   │   ├── stats.py       # GET /api/stats
│   │   ├── query.py       # POST /api/query
│   │   └── health.py      # GET /health
│   ├── query_parser.py    # Constrained NL query mapper (filters & params)
│   └── seed.py            # Demo fallback data seeder
└── tests/
    ├── test_api.py        # Endpoint contract tests
    └── test_query.py      # SQL injection and query parsing test suite
```

---

## Quickstart & Environment

```bash
# Setup virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run development server (from repository root or backend/)
backend/.venv/bin/uvicorn backend.src.main:app --port 8000

# Run tests
backend/.venv/bin/pytest backend/tests/ -v
```

### Environment Variables

| Variable | Default | Description |
| :--- | :--- | :--- |
| `RAZORBILL_DB_PATH` | `<repo_root>/data/razorbill.db` | Absolute or relative path to SQLite database |
| `RAZORBILL_FRAMES_DIR` | `<repo_root>/data/frames` | Directory containing keyframe evidence images |
| `RAZORBILL_DATA_DIR` | `<repo_root>/data` | Fallback parent directory for database and frames |

---

## Baseline API Specification

| Method | Path | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | System health check and DB status |
| `POST`| `/api/incidents` | Validate and upsert incident by stable `event_id` |
| `GET` | `/api/incidents` | Query incidents (`camera_id`, `category`, `start`, `end`, `limit`, `offset`) |
| `GET` | `/api/incidents/{event_id}` | Single incident detail |
| `GET` | `/api/stats` | Aggregated incident metrics |
| `POST`| `/api/query` | Constrained natural language query parser |
| `GET` | `/data/frames/{path:path}` | Static evidence keyframe access |

### Natural-Language Query Example
**Request (`POST /api/query`)**:
```json
{
  "question": "Show all tailgating events from camera 2 today"
}
```

**Response**:
```json
{
  "question": "Show all tailgating events from camera 2 today",
  "interpreted_filters": {
    "camera_id": "CAM_02",
    "category": "tailgating"
  },
  "answer": "Found 2 matching incidents.",
  "incidents": []
}
```

---

## Security & Architecture Directives

1. **Strict Parameterized SQL**: Map user natural language to structured filters (`category`, `camera_id`, `date_range`, `newest/oldest`, `counts`) and execute parameterized SQL only. Never execute arbitrary LLM-generated SQL.
2. **Stable `event_id` Upsert**: Ensure `POST /api/incidents` smoothly updates an existing record without duplicate primary keys.
3. **No Raw Image Bytes in DB**: Store keyframe relative paths (`data/frames/CAM_01/evt_unique_id.jpg`), never base64 blobs in SQLite.
4. **Resilient Query UX**: Unsupported questions must receive a clarification or unsupported response, never fabricated results.

---

## Demonstration Workflow & Seed Data

The backend provides a deterministic synthetic seeder (`backend/src/seed.py`) for reliable local hackathon demonstrations.

### 1. Seeding Synthetic Incidents
```bash
# Seed deterministic synthetic incidents (anchored to current time)
backend/.venv/bin/python -m backend.src.seed

# Dry-run preview without modifying database
backend/.venv/bin/python -m backend.src.seed --dry-run
```

### 2. Verified Demo Sequence
```bash
# 1. Start backend server
backend/.venv/bin/uvicorn backend.src.main:app --port 8000

# 2. Verify health
curl -s http://localhost:8000/health

# 3. List incidents with pagination
curl -s "http://localhost:8000/api/incidents?limit=10"

# 4. Query aggregate statistics
curl -s http://localhost:8000/api/stats

# 5. Execute safe natural-language query
curl -s -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Show all tailgating events from camera 2"}'

# 6. Verify missing-image handling (returns 404 with standard message)
curl -i http://localhost:8000/data/frames/CAM_01/nonexistent.jpg
```

---

## Evidence Path Convention & Security

- **Path Format**: `data/frames/CAM_XX/<event_id>.jpg`
- **Endpoints**: `GET /data/frames/{file_path:path}` and `GET /api/evidence/{file_path:path}`
- **Prefix Handling**: Redundant prefixes (`data/frames/` or `frames/`) are stripped automatically, allowing frontend clients to request `${VITE_API_BASE_URL}/${incident.frame_path}` or direct subpaths cleanly.
- **Security Protections**: Both base directory and target paths are canonicalized via `os.path.realpath`. Path traversal attempts (`../`, `..\`, `%2e%2e`, repeated slashes) and symlinks targeting files outside the frames directory are strictly rejected with `404 Not Found`.
- **Allowed Extensions**: Only `.jpg`, `.jpeg`, `.png`, `.webp`, and `.bmp` files are served.
- **Missing Images**: Nonexistent files return `HTTP 404 {"detail": "Evidence frame not found"}`.

---

## Synthetic Data Limitations

- **Purpose**: Provides immediate deterministic fallback data for local UI demonstrations before live pipeline integration.
- **Labeling**: All synthetic incident summaries and evidence notes are prefixed with `[SYNTHETIC DEMO]` and have event IDs starting with `demo_synth_`.
- **No Fabricated Metrics**: Confidence is `null` (`"unavailable"`), and processing latency is `null`. The backend never invents model benchmark scores.
- **Evidence Images**: When no image files are present on disk, `frame_path` defaults to `""`. Missing frame requests return HTTP 404 so UI fallback logic can be tested honestly.
- **Idempotency**: Running `seed.py` multiple times updates synthetic records in-place without duplicating rows, and never modifies or deletes real detections (`source != manual`).

---

## Team Integration Guide

- **Frontend (Person 4)**:
  - Configure `VITE_API_BASE_URL=http://localhost:8000`.
  - CORS allows `http://localhost:5173` and `http://127.0.0.1:5173`.
  - Display fallback UI state when keyframe images return 404.
- **VLM Classification (Person 2)**:
  - Submit classified records to `POST /api/incidents` matching the `ClassifiedIncident` schema.
  - Set `created_at` in strict UTC ISO 8601 format (e.g. `2026-10-16T12:00:00Z`).
  - Set `confidence: null` unless calibrated model probabilities are available.
- **Video Pipeline (Person 1)**:
  - Store keyframes as standard JPEGs under `data/frames/CAM_XX/`.
  - Provide relative paths (`data/frames/CAM_XX/<id>.jpg`) in candidate packets.
