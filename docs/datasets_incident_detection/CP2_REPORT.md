# CP2 behavioral marker engine report

## Scope and integration state

Implemented `behavioral_markers`, an independent pure-Python/NumPy marker engine. The repository still has no Person 1 detector/tracker, Person 2 VLM, Person 3 backend, or Person 4 frontend implementation; no teammate directory or shared contract was changed. The adapter produces the existing candidate-packet shape and is documented in `INTEGRATION_GUIDE.md`.

## Implemented and tested

- Restricted-zone entry from tracked-person footpoints, with continuous-entry suppression and cooldown.
- Conservative loitering using dwell/observation thresholds; track loss and changed IDs reset state.
- Persisted crowd gathering with count threshold and cooldown.
- Sustained darkness, obstruction-candidate, frozen-feed-candidate, and explicit source-read-failure observations. Health events use `other`, never a tampering claim.
- An optional deterministic synthetic AVI generator for normal, blackout, gradual darkening, obstruction, blur, freeze, static-scene, and lighting-change cases, with interval annotations.

`python -m pytest -q` passed **17 tests in 0.23s**. Tests cover positive/negative/boundary marker paths, empty/lost tracks, ID reset conservatism, sustained/transient state, duplicate suppression, timestamps, read failure, and candidate-contract compatibility. These are unit tests, not real-surveillance precision/recall or latency measurements.

## Data and generator status

No external data, model, or weight was downloaded. Roboflow is publisher-declared MIT but export access was not verified; CUHK Avenue has unverified terms; AI City requires request-form/license acceptance. OpenCV was installed locally as the declared optional dependency and generated eight deterministic AVI fixtures under the ignored `data/raw/camera_health_synthetic/` directory. Its generated catalog passed `validate --check-files` with **8 clips, 0 errors, and 0 warnings**; deterministic split generation also completed. This is synthetic-fixture validation, not real-surveillance evaluation. To reproduce:

```powershell
python -m pip install -e ".[synthetic-video]"
python -c "from behavioral_markers.synthetic_video import generate; generate('data/raw/camera_health_synthetic')"
python -m datasets_incident_detection validate manifests/synthetic_camera_health.json --check-files --json-report reports/synthetic_health.json
```

The generator writes `ground_truth.json` and a populated, checksum-bearing `catalog.json`; validate that generated catalog rather than the no-media repository template. Treat the fixtures as synthetic-only and never report their results as real-world performance.

## CP3 handoff / open questions

Agree with Person 1 on sampling cadence, per-camera polygon configuration, candidate callback, and frame-path capture. Agree with Persons 3/4 how `category=other` plus `trigger=camera_dark` is stored/displayed. Add a bounded queue in Person 1’s owned pipeline, not this package. Camera-facing and pacing were deliberately not implemented: neither is required for the prioritized, tested subset and camera-facing requires a suitable local pose model.
