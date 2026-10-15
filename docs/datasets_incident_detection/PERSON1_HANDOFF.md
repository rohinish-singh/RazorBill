# Person 1 → Person 2 handoff

## Contract

Person 1 emits exactly the candidate object in `SHARED_CONTRACTS.md`:

`event_id`, `camera_id`, `video_source_id`, `timestamp_seconds`, `frame_path`, `frame_paths`, `tracks`, `trigger`, and `created_at`.

`timestamp_seconds` is source-relative. `frame_path` is relative and points to a saved JPG under the physical output root. `tracks` contain only COCO `person` detections with `track_id`, `class_name`, and `bbox_xyxy`. Marker evidence and internal categories deliberately stay inside Person 1; they are not unsupported shared top-level fields.

## Consumption

Run Person 1 with a bounded `candidate_queue` or consume its JSONL output. VLM work is deliberately outside the capture/detection loop. Person 2 should tolerate an empty `tracks` list for camera-health candidates and must not infer calibrated confidence from the packet.

Example command once the staged input and CUDA environment are available:

```powershell
.\.venv\Scripts\python -m video_pipeline data/raw/staged/person_test.mp4 --camera-config video_pipeline/example_camera.json --sample-every 1 --device 0 --output-root data/frames --frame-path-root data/frames --jsonl reports/candidates_gpu.jsonl
```

## Current readiness

Schema validation and keyframe generation are tested. CUDA is verified with PyTorch 2.10.0+cu128 and YOLO11n on the RTX 4050 Laptop GPU. The supplied `person_test.mp4` was later validated locally; its generated artifacts remain ignored until sharing permission is recorded. Do not treat synthetic health-fixture JSONL as a real surveillance result.

Person 1 also supports review-only `person_down_candidate`, `fighting_candidate`, and explicit specialized-model weapon flags. See `docs/PERSON_1_INCIDENT_CANDIDATES.md`; Person 2 should treat every trigger as a candidate rather than a confirmed incident.
