# Integration and Test Plan

## Checkpoints
### Hour 2 — contracts agreed
Everyone has read `SHARED_CONTRACTS.md`; agree IDs, timestamps, categories, path rules, queue/callback shape, and API fields. Confirm hardware/model feasibility.

### Hour 6 — all modules have stubs
Person 1 emits a valid sample packet; Person 2 classifies it with a stub; Person 3 stores/returns seeded incidents; Person 4 renders mock data. Each has a run command.

### Hour 12 — first vertical slice
`video → event packet → classifier/stub → API/SQLite → dashboard` works. Do not add categories until this works.

### Hour 18 — real components integrated
Detector packet reaches classifier; output is accepted by API; UI renders incidents; keyframe paths work; failures are visible.

### Hour 24 — latency/robustness
Slow VLM does not block capture; queue behavior is bounded; duplicate IDs upsert; queries return known seeded records; timings captured.

### Hour 30 — feature freeze
Fix high-impact bugs only. Preserve a known-good demo path.

## Test matrix
- Valid video → frames sampled.
- Invalid video → clear error, no whole-app crash.
- No event → no invented incident.
- Ambiguous event → `unknown`/`needs_review`.
- VLM unavailable/slow → pipeline continues; status/drop count visible.
- Duplicate event ID → upsert, not duplicate.
- Invalid category/payload → clear validation response.
- Missing keyframe → UI fallback, no crash.
- Matching query → correct incidents.
- No-match query → empty result, no fabrication.
- Unsupported query → clarification/unsupported response.
- Backend offline → UI error/fallback.
- Slow laptop → measured latency and dropped work reported honestly.

## Latency metrics
Use a monotonic clock for durations. Measure frame read, detector, VLM, persistence/API, event-to-alert, and event-to-classified-summary separately. Report hardware/runtime, model/quantization, resolution, sampling rate, sample count, p50/p95 when meaningful, dropped work, false positives, and misses on labelled footage. Clearly distinguish offline processing speed from live latency.

## Demo reliability
Keep a short legal prepared clip and a fallback clip or seeded data. Test a clean startup. Label mock data clearly. Avoid last-minute model/runtime changes. Have a one-page start checklist.

## Team rules
Work in clearly owned directories/branches. Update this contract before shared interface changes. Commit small changes. Do not commit model weights, secrets, private videos, or huge temporary frames. If blocked for more than 30 minutes, communicate and provide a stub/adapter so others can continue. By hour 18, integration outranks isolated feature work.
