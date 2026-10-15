# Person 3 — FastAPI, SQLite, Incident Persistence, and Queries

## Mission
Own the API and stored incident source of truth. Implement incident persistence, filtering, statistics, and safe natural-language query mapping.

## Must have
- FastAPI service with `GET /health`.
- SQLite with documented schema/init logic and configurable database path.
- `POST /api/incidents` to validate and upsert by stable `event_id`.
- `GET /api/incidents` with camera/category/date filters and pagination.
- `GET /api/incidents/{event_id}`.
- `GET /api/stats`.
- `POST /api/query` for natural-language questions over stored events.
- Pydantic validation, CORS configuration, clear errors, seed/mock data.
- Timing fields and basic latency summaries.

## Stretch
Better date parsing, JSON/CSV export. Only add local-model query interpretation if safe and fast.

## Do not own
Detection/tracking, VLM implementation, frontend, arbitrary SQL generation, complex auth unless required.

## Query behavior
Support a constrained set of patterns: category, camera, today/date range, newest/oldest, counts, and combinations. Map language to structured filters and parameterized SQL. Never execute arbitrary LLM-generated SQL. If uncertain, ask for clarification or return `unsupported_query`. Never fabricate records or answers. Confirm camera naming and timezone conventions with the team.

## Database
Store stable event ID, camera, source-relative timestamp, optional wall-clock timestamp, category, summary, nullable confidence/type, keyframe path, source/status, processing time, evidence notes, created/updated timestamps. Index common filters. Store paths, not base64 image bytes.

## Deliverables and acceptance
- Runnable API and SQLite setup.
- Endpoint examples/curl commands and OpenAPI docs.
- Seed script/fixtures.
- Tests for insert/upsert, filters, invalid payloads, and query parsing.
- Duplicate event IDs update rather than duplicate.
- Unsupported queries do not fabricate results.
- Configurable paths and predictable errors.
- Frontend can use seeded data before Person 1/2 are ready.

## Time box
0–2 h schema/contracts; 2–6 h API skeleton and seed data; 6–12 h CRUD/filters; 12–18 h query/stats; 18–24 h integration; then edge cases.

## Copy-paste ChatGPT/Claude prompt
You are helping Person 3 on a 36-hour open-source live video event summarization/classification/querying project. Read `README.md`, `SHARED_CONTRACTS.md`, and this file. Inspect the repo before creating files. My ownership is FastAPI, SQLite, incident persistence, filters, stats, and safe natural-language querying. Do not implement detection, VLM, or frontend. Match the shared contracts and propose changes before making assumptions. Use Pydantic, parameterized SQL, stable event IDs/upsert, configurable paths, and seeded mock incidents. Natural language must map to constrained filters; never execute arbitrary LLM-generated SQL or fabricate results. Include run instructions, API examples, tests, predictable errors, and timing fields. Avoid unnecessary infrastructure and coupling to another person's private implementation.
