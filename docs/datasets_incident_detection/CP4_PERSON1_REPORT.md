# CP4 Person 1 GPU and real-video validation report

## Scope and input gate

This checkpoint retains the CP3 ownership boundary: file ingestion, YOLO11n person detection, ByteTrack, behavioral-marker evaluation, keyframe creation, and Person 1 candidate packets. It does not add VLM inference or change `SHARED_CONTRACTS.md`.

The specified input, `data/raw/staged/person_test.mp4`, was not present on 2026-10-15. OpenCV could not open it and therefore reported no metadata. Per CP4, the real-video section stopped at that gate: no claim is made about real-person detections, track continuity, marker outcomes, packets, debug imagery, or CPU/GPU comparison on that video.

Git ignores `data/raw/`, `data/frames/`, `reports/`, `*.pt`, and `.venv/`; generated clips, keyframes, reports, weights, and the virtual environment remain untracked.

## GPU environment

`nvidia-smi` observed an NVIDIA GeForce RTX 4050 Laptop GPU, driver `610.62`, 6,141 MiB total VRAM (607 MiB in use at the inspection), with CUDA driver capability 13.3. Host Python is 3.14.3. A dedicated ignored `.venv` now has the official CUDA 12.8 builds `torch==2.10.0+cu128` and `torchvision==0.25.0+cu128`, plus Ultralytics `8.4.177` and `lap==0.5.13` for ByteTrack.

`torch.cuda.is_available()` returned `True`; device 0 is `NVIDIA GeForce RTX 4050 Laptop GPU`. A real YOLO11n inference on a synthetic 96×64 frame completed on `cuda:0` in 47.196 ms after warm-up, produced zero detections, and observed 69.39 MiB peak allocated / 88.00 MiB peak reserved CUDA memory. This verifies GPU execution, but is not a real-video detection result.

## Reliability improvements

The marker engine now treats a continuous crowd or camera-health condition as one candidate until the condition clears. On clear, it resets eligibility; a later sustained reactivation can emit a new candidate while still honoring cooldown. Crowd suppression is keyed by zone rather than a fluctuating member list. All marker statuses remain `needs_review`.

Pipeline metrics now expose people-bearing frames, total person detections, distinct track IDs, and consecutive-frame ID continuity observations. Candidate frame paths now have an explicit configurable relative root (`--frame-path-root`) while physical output remains independently configurable (`--output-root`). This preserves the shared packet schema.

## Synthetic camera-health regression

The eight local CP2 AVI fixtures were rerun on CPU with YOLO11n/ByteTrack integration and the existing demo camera configuration. All inputs contained zero people, so none supports a person-detection or tracking claim. The runs completed without malformed candidate-packet failures. Candidate counts were: abrupt blackout 3, blur 2, frozen 2, gradual darkening 1, lighting change 1, normal 1, obstruction 2, static scene 2.

The normal and lighting fixtures producing candidates show why these signals remain review candidates, not incident assertions: static/low-texture imagery can satisfy frozen or obstruction heuristics. Thresholds were not reduced for a demonstration.

Comparable runs over `abrupt_blackout.avi` used 30/30 sampled frames, the same camera configuration, YOLO11n/ByteTrack, and the same virtual environment. CPU completed in 8.21 s (3.66 sampled FPS; 272.03 ms mean inference; 0.56 ms mean marker); GPU completed in 3.01 s (9.97 sampled FPS; 95.14 ms mean synchronized inference; 0.63 ms mean marker; 69.39 MiB allocated / 88.00 MiB reserved CUDA peak). Each emitted three candidates and dropped none. These are synthetic camera-health regression measurements only, not person accuracy, tracking accuracy, or a real-video benchmark.

## Test result

`python -m pytest -q` completed with **23 passed**. Coverage includes invalid sources, empty detections, stable fixture track propagation, keyframes, contract validation, configurable relative paths, marker triggers, and continuous-alert reset/reactivation.

## Reproducible commands

After the CUDA environment is verified and the staged video is supplied:

```powershell
.\.venv\Scripts\python -m video_pipeline data/raw/staged/person_test.mp4 --camera-config video_pipeline/example_camera.json --sample-every 1 --device 0 --output-root data/frames --frame-path-root data/frames --jsonl reports/candidates_gpu.jsonl
.\.venv\Scripts\python -m video_pipeline data/raw/staged/person_test.mp4 --camera-config video_pipeline/example_camera.json --sample-every 1 --device cpu --output-root data/frames --frame-path-root data/frames --jsonl reports/candidates_cpu.jsonl
```

## Blockers

1. The demonstrated polygon is clip-specific; calibrate and review production zones per camera before interpreting operational restricted-entry alerts.
2. The short clip cannot validate loitering or crowd behavior under their configured thresholds.

## Real-video validation addendum — 2026-10-16

The approved staged input was supplied at `E:\honeymindproject\data\raw\staged\person_test.mp4`. It is readable without changing the source: 576×1024 pixels, 30 FPS, 55 frames (1.833 s), with OpenCV-reported fourcc `875967080`.

`python -m video_pipeline.annotate` wrote the ignored inspection artifacts `reports/person_test_annotated.mp4` and `reports/person_test_tracks.json`. The annotated MP4 overlays each COCO-person bounding box, ByteTrack ID, source-relative timestamp, and frame index. It observed 83 person detections across 55 frames, three distinct IDs, and 79 consecutive-frame continuity hits. This is an operational tracking observation, not a ground-truth accuracy claim.

The checked-in `example_camera.json` remains a 96×64 synthetic-fixture configuration and is not valid for this portrait video. A separate `video_pipeline/person_test_demo_camera.json` defines `track_1_entry_demo` as `[280,800]–[450,1000]`, based on the inspected track-1 footpoint trajectory. Track 1 was outside at frame 36 / 1.200 s `(271.84, 863.62)` and inside at frame 37 / 1.233 s `(288.86, 862.07)`, so this is a genuine observed entry transition rather than a forced full-frame zone.

The GPU pipeline run sampled all 55 frames and emitted one `restricted_zone_entry` candidate: `marker_CAM_PERSON_TEST_DEMO_restricted_zone_entry_1233`, timestamp `1.2333333333333334` seconds, track ID 1. Its packet passes `validate_candidate_packet`, has only the authoritative top-level fields, has a source-relative timestamp equal to `37 / 30`, and its ignored JPG keyframe exists at `data/frames/CAM_PERSON_TEST_DEMO/marker_CAM_PERSON_TEST_DEMO_restricted_zone_entry_1233.jpg`.

Measured run metrics: 55 frames read/sampled, 55 frames containing people, 83 detections, 3 distinct IDs, 79 continuity hits, 1 candidate emitted, 0 candidates dropped, 8.86 sampled FPS, 6.21 s elapsed, 57.29 ms mean synchronized inference, and 65.47 MiB allocated / 90.00 MiB reserved CUDA peak. No loitering or crowd result is claimed: the clip is only 1.833 s and the demo configuration keeps their 30-second / five-person thresholds.

Reproduce:

```powershell
.\.venv\Scripts\python -m video_pipeline.annotate E:\honeymindproject\data\raw\staged\person_test.mp4 --output reports\person_test_annotated.mp4 --track-report reports\person_test_tracks.json --device 0
.\.venv\Scripts\python -m video_pipeline E:\honeymindproject\data\raw\staged\person_test.mp4 --camera-config video_pipeline\person_test_demo_camera.json --sample-every 1 --device 0 --output-root data\frames --frame-path-root data/frames --jsonl reports\person_test_zone_candidates.jsonl
```
