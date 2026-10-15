# Person 4 — Frontend, Dashboard, Demo, and Evaluation Display

## Mission
Build a polished, reliable industrial-style dashboard. Work with mock data immediately, then connect to Person 3's API without depending on backend internals.

## Must have
- React + Vite + TypeScript (unless an existing compatible UI is agreed).
- Monitoring/demo view.
- Incident list with category, camera, timestamp and summary.
- Camera/category/date filters.
- Incident detail view with keyframe/evidence.
- Natural-language query input and results.
- Metrics panel showing measured latency and evaluation data.
- Loading, empty, error, offline and missing-frame states.
- Mock data matching `SHARED_CONTRACTS.md`.

## Stretch
Video playback/overlays, charts, camera status cards, export.

## Do not own
AI inference, SQLite, direct database access, fabricated metrics, excessive animations.

## UI principles
Clear hierarchy, readable labels, strong contrast, evidence and timestamp prominent. Distinguish `candidate`, `classified`, `needs_review`, and `failed`. If VLM analysis is pending, show pending status rather than freezing the interface. A single polished dashboard with tabs is better than many unfinished pages.

## Integration
Create one API client module. Read base URL from `VITE_API_BASE_URL`, not a teammate-specific hardcoded address. Use backend endpoints in `SHARED_CONTRACTS.md`. Frontend must not import Python modules or access SQLite directly. Handle relative keyframe paths and missing images gracefully.

## Demo story
1. Select prepared video/camera.
2. Show processing/detection status.
3. Show incident category, summary, timestamp and keyframe.
4. Open incident details.
5. Ask a natural-language question.
6. Display matching database-backed incidents.
7. Show measured latency/evaluation results.
Keep a fallback mode using seeded data and label it clearly as demo/mock data.

## Deliverables and acceptance
- Independent run instructions.
- Mock mode that works before backend integration.
- API client and configurable base URL.
- Incident list/details/query views.
- Error/loading/empty states and missing-frame handling.
- Manual test checklist or basic UI test.
- Demo script and fallback.
- No fabricated metrics.

## Time box
0–2 h inspect existing UI/contracts; 2–6 h app shell/mock data; 6–12 h list/details/filters; 12–18 h query/API client; 18–24 h backend integration; 24–30 h polish; final hours demo rehearsal/fixes.

## Copy-paste ChatGPT/Claude prompt
You are helping Person 4 on a 36-hour open-source live video event summarization/classification/querying project. Read `README.md`, `SHARED_CONTRACTS.md`, and this file. Inspect the existing repo before generating a new app. My ownership is the React/Vite/TypeScript dashboard, incident views, query UI, demo flow, and display of measured metrics. Do not implement AI inference or database internals. Build against mock data matching the shared schema first, then connect through one API client to Person 3's endpoints. Use a configurable API base URL, not hardcoded hostnames. Include loading/error/empty/pending states, missing-frame handling, and a clear mock-data indicator. Do not fabricate latency/accuracy values. Prioritize polished, reliable workflow over unnecessary animations. Propose shared contract changes before assuming them.
