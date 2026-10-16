# RazorBill full integration

## Branch and scope

This integration lives on `integration/person1-person2-person3-person4`, created from
`integration/person1-person2-person3` and merged with `origin/person-4-frontend`.
The merge introduced the isolated `frontend/` Next.js application without replacing
the Person 1 pipeline, Person 2 classifier, or Person 3 backend.

The dashboard runs in real API mode by default.  Set `NEXT_PUBLIC_USE_MOCK=true`
only for explicitly labelled UI-only demonstration data.  In real mode a backend
failure is shown to the operator with a retry action; mock records are never silently
substituted.

## API compatibility

The client consumes the actual Person 3 API shapes:

- `GET /api/incidents` returns `{items, total, limit, offset}`.
- `GET /api/incidents/{event_id}` returns one classified incident.
- `GET /api/stats` returns `total`, `by_category`, `by_status`, `by_camera`, and
  `recent_activity_count`.
- `POST /api/query` consumes `{question}` and returns the backend query response.
- Keyframes are requested only through `/api/evidence/{relative-frame-path}`.

The browser never receives a Windows filesystem path.  Absolute, traversal, and
missing paths fall back to the UI placeholder.  The FastAPI CORS allow-list already
includes local Next development origins (`localhost` and `127.0.0.1`, including port
3000) and may be overridden through `RAZORBILL_CORS_ORIGINS`.

## Install and run (PowerShell)

From the repository root:

```powershell
# Python environment containing backend dependencies
.\.venv\Scripts\python.exe -m uvicorn backend.src.main:app --host 127.0.0.1 --port 8000

# In a second terminal
Set-Location .\frontend
Copy-Item .env.example .env.local
npm ci
npm run dev
```

Open `http://localhost:3000`.  `NEXT_PUBLIC_API_BASE_URL` defaults to
`http://localhost:8000`; change it in `frontend/.env.local` only when the backend is
served elsewhere.  Do not commit `.env.local`.

For a dedicated local database/evidence location:

```powershell
$env:RAZORBILL_DB_PATH = "$PWD\data\razorbill.sqlite3"
$env:RAZORBILL_FRAMES_DIR = "$PWD\data\frames"
.\.venv\Scripts\python.exe -m uvicorn backend.src.main:app --host 127.0.0.1 --port 8000
```

## Candidate to dashboard demo

1. Run Person 1 to produce a contract-compatible JSONL candidate and keyframe under
   `data/frames/`.
2. Run the Person 2 worker with `--frame-root` set to the repository root. It produces
   a `ClassifiedIncident` retaining the candidate `event_id`, `camera_id`, timestamp,
   and relative `frame_path`.
3. POST the classified JSON to `http://127.0.0.1:8000/api/incidents`.
4. Refresh the dashboard. Select its card to load `GET /api/incidents/{event_id}` and
   view the backend-served keyframe.
5. Use the query tab for a supported backend query such as `Summarize incidents from
   the last 2 hours.`

For connectivity-only testing when Ollama is unavailable, use the existing deterministic
classifier fallback and label its result as fallback. It is not VLM inference and must
not be presented as such.

## Known limitations

- The dashboard displays persisted classified incidents; it does not start video
  inference itself.
- Evidence routes serve images only. Existing video/evidence clips remain sidecar
  artifacts and are not browser-streamed by the current backend.
- Real Moondream inference requires a locally installed Ollama model; it was not
  downloaded or validated as part of this frontend integration.
- The frontend build requires a complete `npm ci` installation. If npm leaves a
  partial `node_modules`, stop stale npm processes through the local environment and
  rerun `npm ci`; do not commit `node_modules`.

## Verified frontend checks

On 2026-10-16, from `frontend/` with Next.js 16.3.6 and the configured
`.env.local`, both commands completed successfully:

```powershell
npm.cmd run build
npm.cmd run lint
```

The production build completed strict TypeScript checking and generated all seven
static routes. The lint command completed with no reported violations.
