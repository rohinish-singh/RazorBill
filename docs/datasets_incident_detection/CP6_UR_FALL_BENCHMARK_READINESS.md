# CP6 — UR Fall labeled benchmark readiness

## Acquisition decision

UR Fall is the first proposed independently sourced benchmark because the official
dataset page describes 70 RGB/depth sequences (30 falls and 40 everyday activities)
and publishes synchronization data. The official terms identify the dataset as
CC BY-NC-SA 4.0 and state that its intended use is non-commercial academic use;
the page directs commercial-use enquiries to the dataset owner.

**Status: blocked before acquisition.** The hackathon's organizer/sponsor and
deployment classification have not been documented as non-commercial academic
use. A public download URL does not establish that the planned hackathon use is
permitted. No UR Fall archive, frame, synchronization file, converted video, or
model weight was downloaded for CP6.

Acquisition may proceed only after one of the following is retained with the
benchmark record:

1. a written determination from the organizer/sponsor that this specific
   hackathon use is non-commercial academic use under CC BY-NC-SA 4.0; or
2. written permission or an alternative license from the dataset owner for the
   intended hackathon use.

The source and terms to review are the [official UR Fall dataset page](https://fenix.ur.edu.pl/~mkepski/ds/uf.html).

## Planned acquisition and local layout after approval

Start with a small balanced RGB subset: two fall sequences and two everyday
activity sequences, retaining their official synchronization/annotation assets.
The exact sequence archives, original URLs, dates, byte sizes, SHA-256 checksums,
and official split information will be recorded at download time; none is
invented in advance.

All external media remains ignored:

```text
data/raw/ur_fall/
  archives/       # original downloaded archives
  extracted/      # official RGB frames and timing/annotation files
  derived/        # local temporary video conversions
  annotations/    # copied official labels/synchronization files
```

For conversion, the runner will retain a frame-to-source-time mapping from the
official synchronization CSV (milliseconds since sequence start). If a sequence
does not provide usable per-frame timing, a constant-rate video is only a
playback approximation; it will be labelled as such and never treated as a
precise event-time annotation.

## Candidate benchmark protocol

The current YOLO11n + ByteTrack + person-down configuration is frozen for the
first benchmark run. The benchmark asks a clip-level question: did a labelled
fall clip receive at least one `person_down_candidate` packet, and did an
everyday-activity clip avoid one? It does **not** infer frame-level ground truth
from a clip label or claim that a horizontal bounding box proves a fall.

After approval and pipeline execution, prepare two JSON arrays outside version
control (for example under `reports/`):

```json
[
  {
    "sequence_id": "official-sequence-id",
    "category": "person_down",
    "event_time_seconds": null
  }
]
```

```json
[
  {
    "sequence_id": "official-sequence-id",
    "packets": [
      {
        "event_id": "unchanged-person1-event-id",
        "camera_id": "camera-0",
        "video_source_id": "official-sequence-id",
        "timestamp_seconds": 0.0,
        "frame_path": "relative/keyframe.jpg",
        "frame_paths": ["relative/keyframe.jpg"],
        "tracks": [],
        "trigger": "person_down_candidate",
        "created_at": "2026-10-16T00:00:00Z"
      }
    ]
  }
]
```

`event_time_seconds` is optional. The evaluator computes alert delay only when
an official, usable event time is present; otherwise it reports no delay rather
than manufacturing one. Packet fields remain the unchanged Person 1 → Person 2
shared packet shape.

Run the evaluator with:

```powershell
.\.venv\Scripts\python.exe -m datasets_incident_detection benchmark-candidates `
  reports\ur_fall_ground_truth.json `
  --predictions reports\ur_fall_predictions.json `
  --target-category person_down `
  --target-trigger person_down_candidate `
  --keyframe-root . `
  --output reports\ur_fall_candidate_benchmark.json
```

It first validates every supplied packet against the existing shared Person 1 →
Person 2 contract and, with `--keyframe-root`, requires each primary keyframe to
exist and decode. It then produces per-sequence outcomes, a clip-level confusion
matrix, precision, recall, F1, false-positive rate, candidate counts, and delay
statistics when labels permit. Predictions for unknown sequence IDs are surfaced
explicitly.

## Results and limitations

No sequences were acquired or evaluated in CP6 because permission is unresolved.
Accordingly, positive/negative counts, candidate counts, recall, precision, F1,
false-positive rate, throughput, and delay are **not evaluated**. There are no
observed UR Fall failure cases to report.

When acquisition is approved, review failures by camera angle, occlusion, missed
person detection, track fragmentation, and horizontal-box review cues. Any
threshold experiment must use a separately named exploratory configuration and
must not be selected from the held-out evaluation results.
