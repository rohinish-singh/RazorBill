# RazorBill — Backend API & Query Engine

**Owner**: Person 3  
**Detailed Guide**: [`../docs/PERSON_3_BACKEND_QUERYING.md`](../docs/PERSON_3_BACKEND_QUERYING.md)  
**Contract Reference**: [`../SHARED_CONTRACTS.md`](../SHARED_CONTRACTS.md)

---

## Overview

The `backend/` module is built using **FastAPI** and **SQLite**. It serves as the central data store and query engine for RazorBill. It persists candidate and classified incidents via upsert, serves evidence frame images statically, provides filtered queries and aggregated stats to the frontend, and powers the natural-language query interface via safe, parameterized SQL execution.

---

## Planned Directory Structure

```
backend/
├── README.md
├── requirements.txt
├── src/
│   ├── main.py            # FastAPI entrypoint and route mounting
│   ├── config.py          # App settings (database path, evidence directory)
│   ├── database.py        # SQLite connection pool and schema migrations
│   ├── models.py          # Pydantic schemas (Candidate, Incident, Query)
│   ├── routes/
│   │   ├── incidents.py   # GET/POST /api/incidents and GET /api/incidents/{id}
│   │   ├── stats.py       # GET /api/stats
│   │   ├── query.py       # POST /api/query
│   │   └── health.py      # GET /health
│   ├── query_parser.py    # Deterministic NL query mapper (filters & params)
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
```

### Key Dependencies
- `fastapi`
- `uvicorn[standard]`
- `pydantic`
- `sqlite3` (built-in Python standard library)

---

## Endpoints

| Method | Path | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | System health check and DB status |
| `POST`| `/api/incidents` | Upsert incident by `event_id` |
| `GET` | `/api/incidents` | Query incidents (camera, category, time, pagination) |
| `GET` | `/api/incidents/{id}` | Single incident detail |
| `GET` | `/api/stats` | Aggregated incident metrics |
| `POST`| `/api/query` | Deterministic natural language query parser |
| `GET` | `/evidence/{filename}`| Static evidence thumbnail access |

---

## Security & Architecture Directives

1. **Strict Parameterized SQL**: Never execute arbitrary or model-generated SQL strings. Natural-language questions map to allowlisted parameters (`category`, `camera_id`, `time_range`) and query SQLite using `?` placeholders.
2. **Upsert by `event_id`**: Ensure `POST /api/incidents` smoothly updates an existing `candidate` event to `classified` without duplicate key errors.
3. **No Raw Image Bytes**: Store evidence file paths, never image blobs, in SQLite.
4. **Demo Data Seed Ready**: Maintain `src/seed.py` with 25 realistic sample incidents for offline demo resilience.

