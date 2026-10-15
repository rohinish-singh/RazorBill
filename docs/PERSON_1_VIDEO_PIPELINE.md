# Person 1 — Video Ingestion, Detection, and Tracking

## Mission
Own video input and the fast processing path. Produce stable candidate packets for Person 2. Optimize for bounded latency and predictable resource use.

## Must have
- Open a local video with OpenCV (required reliable demo path).
- Configurable frame sampling.
- Lightweight open-source detector, preferably reusing compatible Eagle code.
- Tracking if stable within the time budget; otherwise document a stub.
- Save selected keyframes under a configurable data directory.
- Emit the packet in `SHARED_CONTRACTS.md`.
- Record detection/read timing and dropped frames/candidates.
- Provide a stub producer so integration can begin before detection is finished.

## Stretch
Webcam, RTSP, zone-entry triggers, multiple sources.

## Do not own
VLM classification, database/API, frontend, custom model training.

## First steps
1. Inspect Eagle's detection/tracking code, commands, dependencies, weights and licenses.
2. Try the smallest demo; verify on actual hardware.
3. Report blockers early. Do not spend hours repairing unrelated infrastructure.
4. Agree on a public interface by hour 4.

## Suggested interface
`process_video(source, config, on_candidate)` where `on_candidate(event_packet)` is called for each candidate. Callback/iterator/queue are all acceptable, but document the choice and get agreement first. Do not expose private detector classes to Person 2.

## Latency rules
- Never call the VLM in the capture/detection loop.
- Use a bounded queue/callback and avoid loading the entire video into RAM.
- Skip redundant work if downstream processing is behind; count drops.
- Measure with a monotonic clock.
- Do not claim real-time performance until tested.

## Deliverables and acceptance
- Runnable file pipeline and setup instructions.
- Sample packet JSON and valid keyframe.
- Tests for invalid source and packet shape.
- Detector works on one test clip.
- Errors are readable; slow downstream work cannot stall capture indefinitely.
- Note model/tracker, hardware, sampling rate and measured timings.
- Configurable paths; no teammate-specific absolute paths.

## Time box
0–2 h inspect/hardware; 2–6 h file input and packet stub; 6–12 h detector/tracker; 12–18 h integration; then only optimize after vertical slice works.

## Copy-paste ChatGPT/Claude prompt
You are helping Person 1 on a 36-hour project for open-source live video event summarization/classification/querying. Read `README.md`, `SHARED_CONTRACTS.md`, and this file first. Inspect Eagle before writing replacement code. My ownership is video ingestion, frame sampling, detection, tracking, keyframe saving, and candidate packets. Do not implement VLM, database, or frontend. Match the shared packet schema. If a detail is unresolved, make a small adapter/stub and document the assumption rather than hard-coupling to another module. Avoid absolute paths, unbounded queues, and loading full videos into RAM. Keep VLM out of the capture loop. Include run instructions, sample output, tests, timing instrumentation, and limitations. Do not invent benchmarks. Propose shared contract changes before making them.
