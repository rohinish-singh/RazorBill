# CP13 — Reliability audit and integration handoff

## Executive summary

Person 1 is reproducible as a **review-candidate** pipeline: local video,
YOLO11n/ByteTrack and optional pose/action/weapon adapters, bounded keyframes
and evidence, then the unchanged Person 1 packet. CP13 began at `ae724e4` and
ran the existing suite (59 passed). It refreshed bounded CUDA firearm and knife
smokes and revalidated the CP12 temporal candidate. No shared schema, teammate
code, model weight, dataset, or media asset is committed.

This is not an accuracy certification. Organizer clips are unlabelled, weapon
examples are repeated-image functionality smokes, and the local UR Fall split
contains only four clips under a provisional local-use assumption.

## Implemented capability and validation

- OpenCV file ingestion, YOLO11n COCO-person detection, and ByteTrack IDs.
- Restricted-zone, loitering, crowd, health, person-down, and pose review cues.
- VideoMAE `fight`/`no_fight` review windows and gun/knife temporal confirmation.
- JSONL packets, JPEG keyframes, and bounded MP4 evidence sidecars.

All internally emitted candidates remain `needs_review`. VLM or human review
must classify them; capture does not wait for VLM work.

| Cue | Local source/provenance | CP13 result | Validation |
| --- | --- | --- | --- |
| Temporal fighting | First 65 frames of authorized local `v001` derivative (CP12) | 1 `temporal_fighting_candidate` at 1.5667 s | validator clean; JPEG and 37-frame MP4 decode |
| Firearm | Repeated CC BY-SA Glock image video | fresh CUDA: 1 `weapon_firearm_candidate` at 0.1 s | validator clean; JPEG and one-frame MP4 decode |
| Knife | Repeated CC BY-SA kitchen-knife image video | fresh CUDA: 1 `weapon_knife_candidate` at 0.1 s | validator clean; JPEG and one-frame MP4 decode |

The temporal result proves plumbing only, not a confirmed fight. The weapon
sources are one image repeated five times, not independent positives.

## Fighting settings and qualitative negatives

The frozen CP10 config, `temporal_fighting_review.json`, accepts a completed
raw `fight` window at >= 0.75. `temporal_fighting_demo.json` requires >= 0.55
and two consecutive completed windows. The latter is an integration setting,
not a validated operating threshold.

| Local organizer source | Verified activity label? | Frames/windows | Fight-score range | Conservative / exploratory observation |
| --- | --- | ---: | ---: | --- |
| `v003_converted 3.avi` | No | 89 / 10 | .1780–.4802 | 0 / 0 review episodes |
| `v001_converted 3.avi` | No | 193 / 23 | .1709–.6616 | 0 / one demonstration episode |
| `v006_converted 3.avi` | No | 175 / 20 | .2378–.8036 | qualifying windows observed |
| `v026_converted 3.avi` | No | 291 / 35 | .3987–.7467 | 0 baseline; adjacent .55 windows observed |
| `w001_converted 3.avi` | No | 154 / 18 | .3430–.7854 | qualifying windows observed |

These are raw score distributions, not labels. `v003` is a useful local
non-alert observation, but no organizer source is a verified hard negative.
Precision, recall, F1, false-positive rate, and threshold superiority are
therefore unavailable.

## Weapon and person-down negatives

The local CC0 apple still was freshly predicted as `firearm`/native `gun` at
raw 0.3668 using the CP11 threshold 0.25. A new five-frame MJPG derivative
produced one object observation and no candidate. This does **not** prove that
temporal confirmation fixes the false positive: encoding/resolution affects the
detector, and repeated stable false positives can still meet the two-observation
rule. No apple-specific exception or threshold change was made.

CP13 did not retune UR Fall. CP7's frozen setting had TP=0, FP=0, TN=2, FN=2
over two falls and two ADLs. CP8's development-selected setting was evaluated
once on one fall and one ADL holdout (TP=1, FP=0, TN=1, FN=0). The two-clip
result is not reliable accuracy. Generic ADL labels do not identify sitting,
bending, crouching, and walking separately.

## Performance

| Path | Measurement | Value | Scope |
| --- | --- | ---: | --- |
| Detector + temporal candidate | sampled throughput | 4.17 FPS | CP12 65-frame derivative |
| Temporal model | inference | 723.48 ms/window | CP12, seven completed windows |
| Temporal CUDA | allocated/reserved | 654.36 / 704.0 MiB | CP12 |
| Firearm smoke | throughput / weapon latency | 1.85 FPS / 37.52 ms/frame | fresh CP13 five-frame run |
| Knife smoke | throughput / weapon latency | 1.44 FPS / 42.49 ms/frame | fresh CP13 five-frame run |
| Weapon CUDA | allocated/reserved | 81.99 / 98.0 MiB | fresh CP13 runs |
| Frozen person-down | throughput | 13.81–14.95 FPS | CP7 four UR Fall clips |

Weapon throughput includes short-run person-detector overhead. All CUDA results
are on the RTX 4050 Laptop GPU reported with 6,141 MiB VRAM.

## Local handoff package

The ignored package is `E:\honeymindproject\RazorBill\data\raw\person1_handoff`.
It has canonical packet copies, matching keyframes/evidence copies, a manifest,
validation report, and commands. Canonical packets retain contract-valid paths
relative to the RazorBill repository root; they must be regenerated on another
machine rather than rebased silently.

Person 2 should read JSONL one line at a time, open `frame_path` relative to
the repository root, and classify asynchronously. Do not add fields to Person
1 input; return the Person 2 → Person 3 schema in `SHARED_CONTRACTS.md`.
Person 3 integration was not safely run: the backend receives classified
incidents, not a Person 1 candidate as if it were already classified.

## Reproduction

```powershell
# Conservative temporal review; model files and source video are local/ignored.
.\.venv\Scripts\python.exe -m video_pipeline <local-video> `
  --camera-config video_pipeline\temporal_fighting_review.json --sample-every 1 --device 0 `
  --temporal-fighting-model E:\path\outside\repo\archit11-fight-nofight `
  --temporal-window-frames 16 --temporal-stride-frames 8 `
  --output-root data\raw\local_temporal\keyframes `
  --frame-path-root data/raw/local_temporal/keyframes --jsonl data\raw\local_temporal\candidates.jsonl `
  --evidence-pre-seconds 1 --evidence-post-seconds 1 `
  --evidence-root data\raw\local_temporal\evidence --relative-evidence-root data/raw/local_temporal/evidence

# Audited specialized weapon adapter.
.\.venv\Scripts\python.exe -m video_pipeline <local-video> `
  --camera-config video_pipeline\weapon_review.json --sample-every 1 --device 0 `
  --weapon-model E:\path\outside\repo\best.pt --weapon-confidence 0.25 --weapon-imgsz 640 `
  --weapon-every 1 --weapon-min-observations 2 --weapon-max-gap-seconds 0.5 `
  --output-root data\raw\local_weapon\keyframes --frame-path-root data/raw/local_weapon/keyframes `
  --jsonl data\raw\local_weapon\candidates.jsonl --evidence-root data\raw\local_weapon\evidence `
  --relative-evidence-root data/raw/local_weapon/evidence

.\.venv\Scripts\python.exe -m pytest -q
```

## Licensing, demo, and go/no-go

VideoMAE is experimental CC BY-NC 4.0. The gun/knife checkpoint has model-card
MIT metadata but its training provenance and Ultralytics/base-weight deployment
obligations need review. UR Fall is local-only under a provisional
non-commercial-use assumption.

Recommended demo: normal stream; known temporal review candidate and evidence;
firearm or knife review candidate; then, when available, Person 2 VLM, Person 3
history/query, and Person 4 dashboard. Mark those integrations pending until
they run. **Go for an assisted local demo; no-go for autonomous claims or an
accuracy/production demonstration.**
