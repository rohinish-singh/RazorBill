# CP7 — UR Fall real-dataset benchmark

## Scope and permission status

This is a local-only benchmark of the Person 1 `person_down_candidate` review
cue. The source is the [official UR Fall Detection Dataset page](https://fenix.ur.edu.pl/~mkepski/ds/uf.html),
which describes 30 fall and 40 ADL sequences, per-stream RGB PNG archives,
synchronization CSVs, and depth-derived posture labels. Its published terms are
CC BY-NC-SA 4.0 for intended non-commercial academic use.

CP7 follows the user's provisional authorization for local, non-commercial
hackathon evaluation. This is **not** verified redistribution permission. All
archives, RGB frames, temporary MP4s, JSONL packets, and keyframes are ignored
under `data/raw/ur_fall/`; none is committed. Exact official URLs, archive byte
sizes, SHA-256 values, selected IDs, and label counts are in
`manifests/ur_fall.json`.

The four selected camera-0 sequences are `fall-01`, `fall-02`, `adl-01`, and
`adl-02`: two positive and two negative clips. ZIP integrity was checked before
extraction. Each source RGB frame is 640×480. Their synchronization CSVs have
approximately 33 ms increments; conversion uses the median interval (29.75–
29.97 FPS) and retains the original timestamps in ignored conversion metadata.

## Labeling and evaluation protocol

The official extracted label CSVs report depth-derived posture labels (`-1` not
lying, `0` temporary/falling, `1` lying). This benchmark maps a fall sequence
containing official `1` labels to the clip-level `person_down` target and maps
the selected ADLs to `other`. It does **not** assign a depth-label frame time to
an RGB event: the cameras are independently recorded and the available
depth-derived labels are not asserted to be RGB temporal ground truth.

Consequently, CP7 reports clip-level precision/recall/F1/FPR only. Detection
latency is unavailable, rather than invented. Every emitted packet is validated
against the unchanged shared Person 1 → Person 2 contract and every keyframe is
required to exist and decode before scoring.

## Frozen baseline

Configuration: YOLO11n COCO person detection, ByteTrack, all frames sampled,
RTX 4050 Laptop GPU, default confidence 0.30, aspect ratio threshold 1.25,
and same-track posture persistence 1.0 s. No baseline threshold was selected
from these results.

| Sequence | Official clip target | Frames | Person detections | Tracks | Continuity hits | Max box aspect | Geometry frames | Candidates | Outcome | FPS |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: |
| fall-01 | person_down | 160 | 116 | 2 | 113 | 1.853 | 5 | 0 | FN | 14.95 |
| fall-02 | person_down | 110 | 83 | 1 | 79 | 2.121 | 15 | 0 | FN | 13.81 |
| adl-01 | other | 150 | 139 | 1 | 136 | 0.881 | 0 | 0 | TN | 14.49 |
| adl-02 | other | 180 | 146 | 1 | 145 | 0.796 | 0 | 0 | TN | 14.19 |

Confusion matrix: **TP 0, FP 0, TN 2, FN 2**. Recall is **0.0** and FPR is
**0.0**. Precision and F1 are undefined because the baseline emitted no positive
candidate; they are not presented as zero. GPU peak allocated/reserved memory
was 71.63/88.0 MiB per run. Mean YOLO inference ranged from 35.47 to 41.45 ms
per sampled frame and marker work from 29.16 to 32.72 ms. These are measured
end-to-end sampled FPS values for this local setup, not a general benchmark.

## Failure analysis

Both positive clips have detected horizontal boxes above the 1.25 geometry
threshold, but only for a small number of frames. The default 1.0-second,
same-track persistence requirement therefore never emitted a candidate. This is
not a detector outage: YOLO produced 83–116 person detections on the positive
clips and ByteTrack had 79–113 continuity hits. It is a temporal/posture-rule
miss under this camera angle and duration.

No ADL false positives occurred in this two-clip sample, but that is not evidence
of broad specificity. This RGB heuristic cannot distinguish a fall from lying
down, and the sample is too small to validate robustness to occlusion, other
camera angles, multi-person scenes, or tracker fragmentation. No latency is
reported because the dataset material used here does not provide an appropriate
RGB event-time label for this purpose.

## Separate exploratory persistence experiment

Because the baseline recall was zero, `fall-01` and `adl-01` were held as a tiny
development pair. A 0.25-second persistence attempt still emitted no fall
candidate. A separate 0.10-second persistence configuration then emitted one
candidate on `fall-01` and none on `adl-01` (development TP=1, TN=1). The
unchanged 0.10-second configuration was evaluated once on untouched `fall-02`
and `adl-02`: **TP=1, FP=0, TN=1, FN=0, precision=1.0, recall=1.0, F1=1.0,
FPR=0.0**.

Those held-out numbers are only two clips and must not be interpreted as a
validated accuracy claim. The experiment confirms that persistence, rather than
the absence of a horizontal box, caused the baseline misses. It also materially
increases the risk of alerts for people merely lying down; broader independent
negative footage is required before considering it for production use.

Experimental candidate timestamps were 4.337 s (`fall-01`, development) and
2.369 s (`fall-02`, held out). Their local keyframes decoded successfully. They
are not checked into Git and are not used as ground-truth timing.

## Reproduction

With authorized local files acquired under `data/raw/ur_fall/`:

```powershell
# Frozen baseline; run selected sequences individually if the terminal has a short timeout.
.\.venv\Scripts\python.exe tools\run_urfall_benchmark.py --device 0 --sequences fall-01
.\.venv\Scripts\python.exe tools\run_urfall_benchmark.py --device 0 --sequences fall-02
.\.venv\Scripts\python.exe tools\run_urfall_benchmark.py --device 0 --sequences adl-01
.\.venv\Scripts\python.exe tools\run_urfall_benchmark.py --device 0 --sequences adl-02
.\.venv\Scripts\python.exe tools\run_urfall_benchmark.py --evaluate-existing
```

For a separately named exploratory output root, pass
`--output-root data/raw/ur_fall/benchmark_experimental_010` and
`--person-down-persist-seconds 0.10`. Keep the baseline output unchanged.

## Decision

The frozen person-down candidate system is **not suitable as a reliable gate for
VLM evaluation**: it missed both selected labelled fall clips. The exploratory
configuration can supply conservative *review candidates* for a future expanded
dataset study, but it is not a validated fall detector and should not drive an
incident decision without VLM/human review and more independent evaluation.
