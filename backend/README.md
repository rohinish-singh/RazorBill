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

# Run development server
uvicorn src.main:app --reload --port 8000

# Run tests
pytest tests/
```

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
