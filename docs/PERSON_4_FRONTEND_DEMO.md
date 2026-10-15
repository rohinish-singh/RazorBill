# Person 4 Guide: Frontend Dashboard & Demo Experience

## 1. Ownership & Boundary
- **Directory**: [`frontend/`](../frontend/README.md)
- **Role**: Build the responsive, operator-friendly React/Vite/TypeScript web dashboard, integrate with Person 3's backend REST APIs, display incident streams with evidence frames, build interactive filters, create the conversational querying UI, and ensure a smooth demo presentation.
- **What You DO NOT Own**:
  - Do NOT write video capture or frame extraction code (owned by [Person 1](PERSON_1_VIDEO_PIPELINE.md)).
  - Do NOT run local VLM inference or build ML prompts (owned by [Person 2](PERSON_2_VLM_CLASSIFICATION.md)).
  - Do NOT write SQLite queries, database migrations, or query parsers (owned by [Person 3](PERSON_3_BACKEND_QUERYING.md)).

---

## 2. MVP Priorities

1. **Vite + React + TypeScript Project**:
   - Clean, lightweight setup (e.g. Vite + React + Tailwind CSS or Lucide icons).
   - Fast hot-reload and minimal bundle size.
2. **KPI Header & Metric Summary**:
   - Query `GET /api/stats` every 3–5 seconds.
   - Display total incident counters, category breakdowns (e.g., Person Down, Fighting, Tailgating), and active camera counts.
3. **Live Incident Feed & Card Component**:
   - Query `GET /api/incidents` with pagination and filter params.
   - Render incident cards displaying:
     - Evidence frame thumbnail (loaded from backend `/evidence/...`).
     - Distinct display for Source Video Time (`timestamp_seconds`) and Wall-Clock Time (`created_at`).
     - Category badge with color coding (e.g., Red for `person_down`/`fighting`, Amber for `tailgating`/`suspicious_activity`, Slate for `other`/`unknown`).
     - Confidence meter (e.g., `88% (VLM Calibrated)`).
     - 1–2 sentence human-readable summary.
4. **Interactive Filters**:
   - Filter dropdowns by Category and Camera ID.
   - Status toggle (`classified`, `needs_review`, `all`).
5. **Conversational Query Interface**:
   - Search bar: *"Ask RazorBill a question (e.g., 'Show tailgating events at north gate')..."*
   - Submit query to `POST /api/query`.
   - Display interpreted filter chips (e.g., `[Category: tailgating] [Camera: cam_north_gate_01]`).
   - If response is `unsupported`, render a clear, friendly clarification message instead of an empty broken page.
6. **Demo Mode & Fallback Toggle**:
   - Provide a 1-click toggle or banner for "Demo Mode" that uses pre-packaged fallback JSON if the live backend is unreachable.

---

## 3. Shared Endpoints (Consuming Person 3's API)

All endpoints conform to [`SHARED_CONTRACTS.md`](../SHARED_CONTRACTS.md):

- `GET /health` $\to$ Backend health check and status badge (green/red dot in navbar).
- `GET /api/stats` $\to$ Summary cards in header.
- `GET /api/incidents?camera_id=&category=&status=&limit=50&offset=0` $\to$ Main feed.
- `GET /api/incidents/{event_id}` $\to$ Incident detail modal/drawer.
- `POST /api/query` with body `{"query": "..."}` $\to$ Conversational search bar.

---

## 4. Early Deliverables Schedule

- **Hour 2**: Review API contracts and mock JSON schemas in [`SHARED_CONTRACTS.md`](../SHARED_CONTRACTS.md).
- **Hour 6**: Scaffold Vite app with mock incident state; render initial incident card grid and filter dropdowns.
- **Hour 12**: Wire frontend to Person 3's running FastAPI stub on `http://localhost:8000`.
- **Hour 18**: Connect conversational query input to `POST /api/query` and render interpreted filter badges.
- **Hour 24**: Polish UI styling, responsive layout, loading states, and thumbnail fallback placeholders.
- **Hour 30**: Feature freeze; verify UI with 50+ incidents and test edge cases.
- **Hour 33**: Run end-to-end presentation rehearsals with the full team.

