# Changelog

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
