# CP3 Person 1 video-pipeline report

## Delivered pipeline

video_pipeline is a file-streaming Person 1 implementation: OpenCV reads one frame at a time; YOLO11n is invoked for COCO person detections; Ultralytics ByteTrack maintains runtime IDs; person tracks are converted to behavioral_markers.Track; marker events save keyframes and become exact SHARED_CONTRACTS.md Person 1 candidate packets. No VLM, database, UI, or model training is in the process. An optional bounded queue.Queue or callback allows another owner to consume packets without placing VLM work in the loop.

Run:

~~~powershell
python -m pip install -e ".[person1]"
python -m video_pipeline <local-video> --camera-config video_pipeline/example_camera.json --sample-every 1 --device cpu --output-root data/frames --jsonl reports/candidates.jsonl
~~~

## Measured local smoke tests

Hardware runtime: NVIDIA RTX 4050 Laptop GPU is present (6,141 MiB total; 514 MiB reported in use after run), but installed PyTorch is 2.10.0+cpu; YOLO ran on CPU and did not consume CUDA VRAM.

| Input | Frames sampled | Candidates | Sampled FPS | Mean YOLO/ByteTrack call | Mean marker call |
|---|---:|---:|---:|---:|---:|
| Synthetic normal AVI, 96x64, 30 frames | 30 | 0 | 8.81 | 112.58 ms | 0.44 ms |
| Synthetic abrupt-blackout AVI, 96x64, 30 frames | 30 | 4 | 8.69 | 113.78 ms | 0.46 ms |

The blackout run wrote four contract-compatible packets and relative-path keyframes for camera_obstruction_candidate, camera_dark, and frozen_feed_candidate. This validates camera-health marker plumbing only; no people were in that input, so actual person detection accuracy or real ByteTrack continuity was not measured. Unit tests cover stable ID propagation with a deterministic tracker fixture.

## Contract and limitations

Packets contain exactly event_id, camera_id, video_source_id, timestamp_seconds, relative frame_path, frame_paths, tracks, trigger, and created_at. The shared packet has no evidence/category field, so rich internal marker evidence is retained only before adaptation; team approval is needed before extending a shared contract. Camera-health markers use the existing other category internally and their name in trigger.

The checked-in dependency supports a CUDA-capable environment but this host’s Torch build is CPU-only. Ultralytics/YOLO licensing must be accepted for the intended deployment or the detector adapter swapped before proprietary release. The model weight and raw synthetic assets are ignored and not committed.
