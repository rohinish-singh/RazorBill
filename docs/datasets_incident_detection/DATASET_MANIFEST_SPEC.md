# Dataset manifest specification v1.0.0

Each JSON manifest documents a dataset without bundling videos. It is deliberately usable offline.

Required root fields are `schema_version`, `dataset_id`, `dataset_version`, `source`, `labels`, `provenance`, and `clips`. `schema_version` is currently `1.0.0`. `source` requires `original_url`, `publication`, `terms_url`, `terms_status`, `acquisition_status`, and `acquisition_date` (`null` until acquired). `terms_status` is only `verified`, `unverified`, or `restricted`; CP1 manifests use `unverified` unless original terms were inspected.

`labels` maps source labels to the shared categories: `person_down`, `fighting`, `tailgating`, `crowd_incident`, `suspicious_activity`, `other`, or `unknown`.

Every acquired clip requires `clip_id`, a path relative to `local_root`, `source_group`, source labels, per-clip provenance, and (when known) `sha256`. `source_group` is the indivisible split unit: original video/session/camera/event and alternate views must share it. Optional `temporal_intervals` contain `start_seconds` and `end_seconds`, with `0 <= start < end`.

Run from repository root:

```powershell
python -m datasets_incident_detection validate manifests/rwf_2000.json --json-report reports/rwf.json --markdown-report reports/rwf.md
python -m datasets_incident_detection split manifests/rwf_2000.json --seed 20261015 --output reports/rwf_split.json
```

Add `--check-files` only after legitimate local assets are acquired. Validation detects declared/hash-confirmed exact duplicates; equal file lengths are merely possible near-duplicates and never treated as proof.
