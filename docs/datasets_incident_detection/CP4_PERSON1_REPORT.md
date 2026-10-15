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

1. Restore or provide an approved readable `data/raw/staged/person_test.mp4` before real-video validation.
2. Configure zones from the actual frame dimensions before interpreting restricted-entry, loitering, or crowd results.
