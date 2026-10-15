# CP1 dataset engineering report

## Repository and integration audit

Started from `main` / `origin/main` at `ec5df5bd80d9c5b480f6f64a9f6d405e5e3879d4` and created `feature/datasets-incident-detection`. The RazorBill checkout contained only handoff Markdown files and empty owner directories: no Person 1 detector/tracker implementation, Person 2 VLM module, Python package/dependencies, tests, CI workflow, candidate-packet implementation, or prior dataset tooling. Therefore no working functionality was duplicated.

The authoritative contract is `SHARED_CONTRACTS.md`. CP1 does not alter it. `datasets_incident_detection.contracts.validate_candidate_packet()` validates the Person 1 → Person 2 packet fields, relative frame paths, source-relative timestamps, track IDs, and `bbox_xyxy` geometry without owning or invoking video ingestion.

## Delivered

- Five versioned, no-media catalogs in `manifests/`: RWF-2000, UR Fall, Le2i, local consented staged clips, and deferred UCF-Crime.
- Standard-library manifest validation: structure, source metadata, terms status, labels, temporal intervals, optional local file/checksum checks, exact duplicate detection, and advisory same-size near-duplicate reporting.
- Deterministic source-group split plans with no group leakage.
- JSON and Markdown validation reports through `python -m datasets_incident_detection`.
- Candidate-packet compatibility validation and event-level evaluation that reports `not_evaluated` when predictions are absent. When predictions exist it reports per-category precision/recall/F1, confusion matrix, false positives/negatives, latency mean, and sample count. VLM confidence is not interpreted as calibrated.

## Dataset status and limitations

No external dataset, weight, or video was downloaded. Every catalog has `terms_status: unverified`; neither acquisition nor redistribution should proceed until original terms are reviewed and recorded. UCF-Crime remains deferred. The local staged catalog requires individual consent/provenance before any media is admitted.

## Verification

`python -m pytest -q` completed with **11 passed**. `python -m datasets_incident_detection validate <each manifests/*.json> --json-report <report>` completed successfully for all five catalogs; each correctly reports an `unverified`-terms warning and no structural errors. `split` completed deterministically for the empty, unacquired RWF catalog. These checks do not validate raw footage because none was acquired.

## CP2 handoff

Person 1 should retain ownership of ingestion/detection/tracking and may call the packet validator in a unit test. Before CP2, agree whether to add an adapter import from this package or keep validation as a CI-only contract test. Acquire no data until terms are reviewed; once approved, populate clips, hashes, temporal intervals, and source groups, then run `validate --check-files` and `split` before benchmarking.
