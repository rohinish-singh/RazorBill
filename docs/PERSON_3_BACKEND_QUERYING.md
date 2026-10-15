# Person 3 Guide: Backend API & Natural Language Querying

## 1. Ownership & Boundary
- **Directory**: [`backend/`](../backend/README.md)
- **Role**: Build the FastAPI application, SQLite persistence engine, incident upsert logic, static frame serving, filtered listing, dashboard statistics, and the deterministic natural-language query engine.
- **This is the core workstream for Person 3**.
- **What You DO NOT Own**:
  - Do NOT write OpenCV video capture or motion tracking code (owned by [Person 1](PERSON_1_VIDEO_PIPELINE.md)).
  - Do NOT download or execute local VLM weights (owned by [Person 2](PERSON_2_VLM_CLASSIFICATION.md)).
  - Do NOT implement React components or CSS styling (owned by [Person 4](PERSON_4_FRONTEND_DEMO.md)).

---

## 2. MVP Priorities

1. **FastAPI Foundation & Static File Serving**:
   - Set up FastAPI app with CORS middleware enabled for local React frontend development (`http://localhost:5173`).
   - Mount `/evidence` to serve static frame images from local directory `data/evidence/`.
2. **SQLite Database & Upsert Logic**:
   - Create `incidents` table with indices on `event_id`, `camera_id`, `category`, `created_at`.
   - Store local image paths (e.g. `data/evidence/evt_123.jpg`), **never raw image bytes**.
   - `POST /api/incidents` must perform an **upsert** keyed on `event_id` (so an event can first arrive as `candidate` from Person 1 and later be updated to `classified` by Person 2).
3. **Filtering & Statistics Endpoints**:
   - `GET /api/incidents`: Support pagination (`limit`, `offset`), filtering by `camera_id`, `category`, `status`, and time ranges. Return both `total` and `items`.
   - `GET /api/stats`: Compute real-time aggregations (counts grouped by category, status, camera).
4. **Deterministic Natural Language Query Engine (`POST /api/query`)**:
   - Extract intent deterministically from user queries (e.g., matching keywords to categories, cameras, and time horizons).
   - **CRITICAL SECURITY RULE**: Never pass raw text or LLM-generated SQL directly to `sqlite3.execute()`.
   - Always build **parameterized SQL queries** (`SELECT ... WHERE category = ? AND camera_id = ?`) using allowlisted columns only.
   - For queries that cannot be mapped to supported filters, return a structured `unsupported` status with a helpful clarification rather than guessing or fabricating results.

---

## 3. Shared Endpoints & Schemas

Refer to [`SHARED_CONTRACTS.md`](../SHARED_CONTRACTS.md) for full JSON definitions.

- `GET /health` $\to$ Returns health status, uptime, and database connection state.
- `POST /api/incidents` $\to$ Upserts candidate or classified incident.
- `GET /api/incidents` $\to$ List incidents with query params (`camera_id`, `category`, `status`, `start_time`, `end_time`, `limit`, `offset`).
- `GET /api/incidents/{event_id}` $\to$ Single incident detail or 404.
- `GET /api/stats` $\to$ Aggregated counts by category, camera, and status.
- `POST /api/query` $\to$ Body: `{"query": "string"}`. Returns interpreted filters and matched incidents.

---

## 4. Early Deliverables Schedule

- **Hour 2**: Finalize endpoint parameters and response shapes in [`SHARED_CONTRACTS.md`](../SHARED_CONTRACTS.md).
- **Hour 6**: Deliver runnable FastAPI stub with in-memory or SQLite storage responding to all endpoints with mock data.
- **Hour 12**: Complete end-to-end slice: accept `POST /api/incidents` from Person 2 and serve live updates to Person 4.
- **Hour 18**: Implement deterministic NL query parser with keyword/regex mapping and parameterized SQL.
- **Hour 24**: Test SQL injection resistance, edge-case query parsing, and pagination performance with 1,000+ synthetic records.
- **Hour 30**: Lock down backend codebase during feature freeze; ensure demo seed script (`seed_demo_data.py`) is verified.

