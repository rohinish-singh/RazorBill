# Changelog

## 2026-10-16 — CP13 reliability audit and handoff

- Re-ran the deterministic suite, refreshed local CUDA firearm/knife candidate smokes, and revalidated the CP12 temporal packet/keyframe/evidence lifecycle without changing shared contracts or candidate semantics.
- Documented score-only organizer-clip observations, the reproducible CC0 apple false-positive observation, UR Fall sample limitations, measured local performance, and an ignored Person 1 handoff package for asynchronous Person 2/3 integration.

## 2026-10-16 — CP12 temporal fighting-review audit

- Added an opt-in completed-window temporal episode filter with explicit smoothing and consecutive-window safeguards; conservative CP10 defaults remain equivalent to their prior single-window behavior.
- Added deterministic regression coverage for smoothing, completed-negative resets, consecutive review gating, packet validity, and episode deduplication.
- Ran local CUDA qualitative score schedules on all five organizer clips and verified one complete ignored derivative candidate/keyframe/evidence lifecycle. No labelled fighting benchmark or accuracy metric is claimed.

## 2026-10-16 — CP11 gun/knife review candidates

- Added an opt-in, fail-closed adapter for the verified local gun/knife YOLO checkpoint, including explicit native-class validation, CUDA/CPU configuration, sampling controls, and bounded spatial-temporal confirmation.
- Preserved first/strongest detection provenance in internal evidence, uses the strongest supporting frame for the existing keyframe path, and reuses CP9 evidence sidecars without changing shared packets.
- Added deterministic mapping, filtering, packet, keyframe, evidence, missing-weight, and disabled-mode tests; documented actual licensed-image CUDA smoke tests and a real harmless-object false positive.

## 2026-10-16 — CP10 temporal fighting review

- Added fail-closed task-specific VideoMAE fight/no-fight adapter, correct processor-driven RGB temporal preprocessing, sliding windows, raw-class-score evidence, and numeric CUDA-device normalization.
- Added conservative temporal fighting review candidates with overlapping-window episode deduplication, cooldown preservation, and stride-gap handling; shared Person 1 packet fields remain unchanged.
- Verified actual local CUDA inference and one combined detector/pose/temporal run, while documenting that organizer clips are qualitative only and no labelled benchmark metrics exist.
- Rejected a second checkpoint because its model weights did not load exactly; no invalid scores are reported as recognition results. No weights, footage, keyframes, or evidence clips were committed.

## 2026-10-16 — CP9 pose, temporal-action interface, and evidence fusion

- Added optional YOLO11n-pose inference with conservative one-to-one IoU association to existing ByteTrack people, low-confidence/multiple-match rejection, and a separate pose-geometry person-down review cue. Conservative bounding-box behavior and shared packets remain unchanged.
- Added bounded pre/post-event MP4 evidence sidecars indexed by event ID; the sidecar does not modify Person 1 → Person 2 packet fields.
- Added a sliding-window temporal-action adapter and an optional VideoMAE adapter. A checkpoint download did not complete locally, and generic Kinetics labels are retained only as potential review evidence, never incident confirmation.
- Documented actual local development-run measurements, model/license constraints, and the absence of a new independent labelled evaluation set. No raw media, model weights, or generated evidence was committed.

## 2026-10-16 — CP8 person-down recall investigation

- Added per-track posture transitions/durations and track-ID observation diagnostics without changing default candidate behavior or shared contracts.
- Added opt-in, same-ID-only posture-gap tolerance and regression tests; default tolerance remains zero and separate track IDs are never joined.
- Documented a development-only threshold selection and one-time two-clip held-out check, including the absence of separately labelled posture negatives in the authorized subset.

## 2026-10-16 — CP7 real-dataset benchmark

- Acquired an official UR Fall local-only subset under the user's provisional non-commercial-use assumption; recorded URLs, checksums, labels, and explicit no-redistribution status in the manifest while keeping all media ignored.
- Added reproducible RGB conversion/benchmark tooling, contract/keyframe validation, and pipeline geometry diagnostics.
- Measured a frozen two-fall/two-ADL baseline (TP=0, FP=0, TN=2, FN=2) and documented a separate, tiny development/held-out persistence experiment without presenting it as validated accuracy.

## 2026-10-16 — CP6 UR Fall benchmark readiness

- Verified the official UR Fall terms and stopped acquisition because compatibility of the hackathon's intended use with CC BY-NC-SA 4.0 non-commercial academic use is not documented.
- Added a label-aware clip-level candidate evaluator and tests; it reports delay only when an official event time is supplied and does not manufacture frame-level labels or benchmark results.
- Added the reproducible acquisition/evaluation protocol. No external media, derived footage, model weights, or benchmark results were added.

## 2026-10-16 — CP5 incident-candidate validation

- Validated conservative and interaction-review Person 1 cues locally against five uncommitted organizer clips; all emitted packets validated and keyframes opened locally.
- Aggregated simultaneous fighting pairs into one continuous review episode and added stable event-ID suffixes to prevent packet/keyframe collisions.
- Added an original synthetic portable packet/keyframe fixture for Person 2; no organizer footage or derived media was committed.

## 2026-10-16 — Person 1 incident candidate layer

- Added opt-in, review-only person-down and proximity/motion fighting cues, plus an optional explicitly mapped knife/firearm detector adapter.
- Added conservative incident configurations, contract/keyframe tests, and usage guidance. No weapon model or reference footage was committed.

## 2026-10-15 — CP4 Person 1 reliability and handoff

- Added deterministic reset/reactivation suppression for continuous crowd and camera-health candidates, plus regression tests.
- Added Person 1 detection/track-observation metrics and configurable relative keyframe packet paths without changing the shared schema.
- Documented that the required staged real video is missing; CUDA was separately verified with a synthetic YOLO11n GPU inference, but no real-video result is claimed.

## 2026-10-16 — CP4 real-video validation addendum

- Added an ignored annotated-video/track-report exporter and a portrait-video demo camera configuration based on an observed person footpoint crossing.
- Validated one real restricted-zone candidate, its unchanged shared packet shape, source-relative timestamp, and saved keyframe. No shared contracts changed.

## 2026-10-15 — CP3 Person 1 pipeline and acquisition audit

- Added OpenCV file ingestion, YOLO11n/ByteTrack adapter, behavioral-marker integration, keyframe writer, contract-packet output, CLI, and Person 1 tests.
- Ran CPU-only YOLO11n smoke tests on local synthetic videos; recorded measured values in the CP3 report without claiming person accuracy or GPU inference.
- Verified UR Fall’s official CC BY-NC-SA 4.0 terms but did not download because intended-use compatibility remains unresolved. Roboflow, RWF-2000, and Le2i remain blocked as documented.

## 2026-10-15 — CP2 behavioral markers

- Added review-oriented restricted-zone, loitering, crowd, camera darkness, obstruction-candidate, frozen-feed-candidate, and source-read-failure markers without modifying the shared contract or teammate-owned modules.
- Added a candidate-packet adapter, synthetic AVI generator source, synthetic fixture catalog, tests, integration guide, marker definitions, and official-source dataset audit.
- No external dataset, model, weight, or media was downloaded. Roboflow export access, CUHK Avenue terms, and AI City request/license access remain unresolved.

## 2026-10-15 — CP1 dataset engineering

- Added offline, versioned dataset manifest validation, source-group splitting, contract compatibility checking, and event evaluation tooling.
- Added unacquired catalogs for RWF-2000, UR Fall, Le2i, local staged clips, and deferred UCF-Crime. All terms remain explicitly unverified.
- Added synthetic pytest fixtures/tests. No external dataset, model, video, or GPU workload was downloaded or run.
