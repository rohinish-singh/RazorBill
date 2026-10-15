# Honeywell Live Video AI (RazorBill) — Team Handoff Pack

## Goal
Build a 36-hour hackathon prototype for **Live Video Event Summarization, Classification, and Conversational Querying**. Required flow: video input → detection/tracking → local open-source VLM event analysis → classification → SQLite incident history → natural-language queries → React dashboard.

Latency matters. VLM analysis must not block video ingestion/detection. Start with a video file as the reliable demo source; webcam/RTSP are stretch goals.

## Team ownership
- **Person 1:** video ingestion, frame sampling, detection, tracking, keyframes. ([`video-pipeline/`](video-pipeline/README.md) / [`docs/PERSON_1_VIDEO_PIPELINE.md`](docs/PERSON_1_VIDEO_PIPELINE.md))
- **Person 2:** local open-source VLM, event summaries and fixed-category classification. ([`vlm-classification/`](vlm-classification/README.md) / [`docs/PERSON_2_VLM_CLASSIFICATION.md`](docs/PERSON_2_VLM_CLASSIFICATION.md))
- **Person 3:** FastAPI, SQLite, incident persistence/filtering, safe conversational querying. ([`backend/`](backend/README.md) / [`docs/PERSON_3_BACKEND_QUERYING.md`](docs/PERSON_3_BACKEND_QUERYING.md))
- **Person 4:** React/Vite/TypeScript dashboard, incident views, demo, metrics display. ([`frontend/`](frontend/README.md) / [`docs/PERSON_4_FRONTEND_DEMO.md`](docs/PERSON_4_FRONTEND_DEMO.md))

## Repository strategy
Reference: https://github.com/Devnil434/Eagle  
Inspect Eagle before coding. Reuse compatible, license-compliant code where useful, but do not assume every documented component runs. Avoid copying the whole architecture blindly. Preserve applicable license notices and check model/dependency licenses. No paid cloud inference.

## Compatibility rules
1. Read [`SHARED_CONTRACTS.md`](SHARED_CONTRACTS.md) before coding.
2. Agree on public interfaces by hour 4. Never silently change a shared schema.
3. Every module must be independently runnable/testable and include a stub or mock.
4. Person 4 uses mock data immediately; Person 3 seeds mock incidents; Person 2 tests saved frames; Person 1 uses a local video file.
5. Avoid hardcoded absolute paths, teammate-specific hostnames, circular imports, and cross-module private imports.
6. Use adapters at module boundaries so model, tracker, storage, or UI can be swapped later.
7. Slow inference must not block the pipeline. Use bounded queues, timeouts, and explicit error states.
8. Measure latency and accuracy; never invent metrics or treat generative model output as calibrated confidence.
9. Keep the end-to-end path working before adding features.

## 36-hour milestones
- **0–2 h:** agree on contracts, inspect Eagle, check hardware/model feasibility.
- **2–6 h:** each person produces a stub and independent run command.
- **6–12 h:** first vertical slice: video → packet → classifier/stub → database → UI.
- **12–18 h:** integrate real components and keyframes.
- **18–24 h:** fix integration issues and measure latency.
- **24–30 h:** evaluate categories, false alerts/misses, and UI.
- **30–33 h:** feature freeze.
- **33–36 h:** clean startup, fallback, demo rehearsal.

## Definition of done for each module
Documented public interface, run instructions, sample input/output, happy-path and failure test, timeout/error behavior, measured metrics where relevant, known limitations, and no hidden local-machine assumptions.

## Repository Structure
```
RazorBill/
├── README.md                          # Master project documentation
├── SHARED_CONTRACTS.md                # Data schemas, enums, payload contracts, API specs
├── INTEGRATION_AND_TEST_PLAN.md       # 36-hour schedule, milestones, test gates, fallbacks
├── .gitignore                         # Exclusions for models, videos, frames, and venvs
├── docs/
│   ├── PERSON_1_VIDEO_PIPELINE.md     # Person 1 ownership, boundaries, MVP & deliverables
│   ├── PERSON_2_VLM_CLASSIFICATION.md # Person 2 ownership, boundaries, MVP & deliverables
│   ├── PERSON_3_BACKEND_QUERYING.md   # Person 3 ownership, boundaries, MVP & deliverables
│   └── PERSON_4_FRONTEND_DEMO.md      # Person 4 ownership, boundaries, MVP & deliverables
├── video-pipeline/                    # Video ingestion & anomaly trigger heuristics
│   └── README.md
├── vlm-classification/                # Local VLM inference & structured summarizer
│   └── README.md
├── backend/                           # FastAPI backend, SQLite DB & NL query engine
│   └── README.md
└── frontend/                          # React + Vite + TypeScript dashboard
    └── README.md
```

## Files
- [`docs/PERSON_1_VIDEO_PIPELINE.md`](docs/PERSON_1_VIDEO_PIPELINE.md)
- [`docs/PERSON_2_VLM_CLASSIFICATION.md`](docs/PERSON_2_VLM_CLASSIFICATION.md)
- [`docs/PERSON_3_BACKEND_QUERYING.md`](docs/PERSON_3_BACKEND_QUERYING.md)
- [`docs/PERSON_4_FRONTEND_DEMO.md`](docs/PERSON_4_FRONTEND_DEMO.md)
- [`SHARED_CONTRACTS.md`](SHARED_CONTRACTS.md)
- [`INTEGRATION_AND_TEST_PLAN.md`](INTEGRATION_AND_TEST_PLAN.md)
