# Person 2 — Local VLM Event Understanding and Classification

## Mission
Own local open-source VLM inference and conversion of candidate frames into evidence-based structured incident classifications. Keep this module replaceable and asynchronous.

## Must have
- Check actual hardware (GPU/VRAM/RAM/OS) before choosing a model.
- Inspect Eagle's VLM/reasoning implementation and verify it runs.
- Select one primary local open-source model/runtime; at most one fallback.
- Accept Person 1's candidate packet and analyze a selected frame or small frame set.
- Map output to the shared fixed categories; allow `unknown`/`other`.
- Return the incident schema from `SHARED_CONTRACTS.md`.
- Measure inference latency and handle errors/timeouts.
- Provide a stub classifier early for integration.

## Stretch
Multi-frame context, quantization, prefilters, labelled evaluation/confusion matrix.

## Do not own
Video capture/tracking, database/API, frontend, paid cloud APIs, custom VLM training.

## Interface
Agree on `classify_candidate(candidate: dict) -> dict` or an async/worker equivalent by hour 4. Do not expose private model-runtime objects to Person 3.

## Confidence and safety
Never ask a generative model to invent a probability. Set confidence to null unless a real score is available; document score semantics. Do not call a score calibrated unless calibrated. Use `unknown`/`needs_review` when ambiguous. Describe visible evidence, not inferred intent.

## Latency
VLM must never run inside Person 1's capture loop. Bound concurrency/queues, use a small number of useful frames, measure model-load time separately from event inference, and report p50/p95 only with sample count. If slow, let rules/detection generate a candidate/early alert and enrich asynchronously.

## Deliverables and acceptance
- Local inference module and setup/model license link.
- Stub/mock mode and example outputs.
- Schema-compatible result including `processing_ms`, `source`, `status`.
- Reproducible test command and measured timing report (hardware, model, resolution, sample count).
- Small labelled evaluation and limitations.
- Clear fallback if model fails to load.

## Time box
0–2 h hardware/repo check; 2–6 h model choice and frame test + stub; 6–12 h classifier; 12–18 h integration; then optimize only after end-to-end path works.

## Copy-paste ChatGPT/Claude prompt
You are helping Person 2 on a 36-hour open-source live video summarization/classification/querying project. Read `README.md`, `SHARED_CONTRACTS.md`, and this file. Inspect Eagle's VLM code before replacing it. My ownership is local VLM inference, evidence-based summaries, fixed-category classification, and measured latency. Do not implement video capture/tracking, API/database, or frontend. Use local open-source inference only, no paid cloud APIs. Choose a model based on actual hardware; do not recommend a model without checking resource needs. Provide a stub immediately. Match the incident schema; confidence is null unless a real score exists. Ambiguous events must be `unknown`/`needs_review`. Inference must be asynchronous/bounded and must not block capture. Include setup, license, tests, sample outputs, measured timings, and limitations. Do not invent metrics. Propose contract changes before making them.
