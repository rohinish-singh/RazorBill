# CP2 integration guide

Person 1 remains the owner of capture/detection/tracking. Instantiate one `MarkerEngine(CameraConfig(...))` per camera and call `process_tracks(source_relative_seconds, tracks)` after tracking. Convert each returned event with `to_candidate_packet(event, relative_frame_path)` and submit it through the existing bounded candidate queue/callback. The engine does not read video, run YOLO, call a VLM, use the GPU, or create a queue; that avoids slowing the detection loop.

For health, Person 1 may call `observe_frame(frame, timestamp, previous_frame)` on sampled frames and pass the result to `process_frame_observation`. Call `source_read_failed` only on actual read/decoder errors. Use a low sampling rate and a bounded upstream queue; marker processing is synchronous and lightweight.

`to_candidate_packet` preserves the authoritative candidate packet fields. Health events use `category: other` and their marker name as `trigger`; behavioral marker events use existing categories. The adapter does not add top-level fields or modify `SHARED_CONTRACTS.md`.

```python
events = engine.process_tracks(timestamp_seconds, tracks)
for event in events:
    on_candidate(to_candidate_packet(event, frame_path="data/frames/CAM_01/key.jpg"))
```

No Person 1 code existed during CP2, so this is an unintegrated adapter awaiting team agreement. Person 2 should treat marker evidence as context, not ground truth; Person 3/4 should agree on a label for camera-health `other` events before exposing them.
