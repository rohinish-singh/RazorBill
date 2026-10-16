# CP12 — Fighting-review candidate audit

## Scope and integrity boundary

CP12 preserves CP10's audited temporal checkpoint, its raw-score semantics,
and the unchanged Person 1 packet in `SHARED_CONTRACTS.md`.  This work adds an
optional temporal episode filter for review candidates.  It does **not** turn a
VideoMAE score into a confirmed fight or a calibrated probability.

The five organizer-provided AVI files in `E:\honeymindproject\references`
are authorized only as local qualitative material.  They have no supplied
ground truth, split, license for redistribution, or independent annotations.
They, their frames, keyframes, JSONL, evidence clips, and the model weights
remain outside Git.

## Checkpoint integrity

The only temporal checkpoint used was the CP10 selection:
`archit11/videomae-base-finetuned-fight-nofight-subset2`, loaded from the
local ignored cache.  Every CP12 inference run exercised the fail-closed
adapter and completed only after an exact load: no missing, unexpected, or
mismatched keys; `num_frames=16`, `image_size=224`, `num_labels=2`; embedded
map `0=Fight`, `1=No Fight`.  The adapter maps this to `fight` and
`no_fight`.  Numeric device `0` resolved to `cuda:0`.

The incompatible checkpoint rejected in CP10 remains rejected because the
adapter raises on loading mismatches or a class map other than this audited
map.  No replacement model, model download, or weight change occurred.

## Candidate policy

The frozen baseline is still `video_pipeline/temporal_fighting_review.json`:
one completed `fight` window with raw score at least 0.75.  CP10's documented
`v001` result remains eight top-`fight` windows around 0.50–0.66 and zero
baseline packets.

CP12 adds `TemporalFightReviewFilter`.  It is invoked only for a completed
16-frame window; a stride gap is not treated as a negative.  A completed
non-qualifying window clears its consecutive count.  The configured rolling
mean and number of consecutive qualifying completed windows are retained in
internal event evidence.  The marker engine's existing episode/cooldown logic
continues to suppress duplicate packets.

`video_pipeline/temporal_fighting_demo.json` is an **exploratory local review
configuration**, not a recommended operating point: raw fight score >= 0.55,
one-window mean, two consecutive completed windows, and the existing 30-second
cooldown.  It was selected only to test that short, adjacent review cues can
flow through the system without alerting on a single lower-score window.  It
was not selected from labels and must not be reported as an accuracy
improvement.

## Qualitative local score audit

All clips used full-rate input, 16-frame windows, stride 8, and CUDA.  Values
are raw `fight` softmax scores.  Counts are observations, not true/false
positives.  `two-adjacent >= .55` counts adjacent qualifying pairs; it can be
greater than the number of cooldown-deduplicated episodes.

| Local clip | Frames / windows | Fight top-label windows | Raw fight min / mean / max | >= .75 | >= .55 | Two-adjacent >= .55 | Action-only wall time |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `v001_converted 3.avi` | 193 / 23 | 8 | .1709 / .4218 / .6616 | 0 | 5 | 2 | 19.146 s |
| `v003_converted 3.avi` | 89 / 10 | 0 | .1780 / .2784 / .4802 | 0 | 0 | 0 | 10.237 s |
| `v006_converted 3.avi` | 175 / 20 | 11 | .2378 / .5346 / .8036 | 5 | 10 | 5 | 20.004 s |
| `v026_converted 3.avi` | 291 / 35 | 20 | .3987 / .5219 / .7467 | 0 | 11 | 6 | 29.911 s |
| `w001_converted 3.avi` | 154 / 18 | 11 | .3430 / .5539 / .7854 | 2 | 7 | 5 | 13.476 s |

These schedules demonstrate score variation within the same video and the
danger of relying on a single uniformly sampled clip result.  The baseline
would have no qualifying window on `v001`, `v003`, or `v026`; raw schedule
inspection shows qualifying windows on `v006` and `w001`.  The exploratory
setting increases review opportunities on `v001` and `v026`, but because these
clips have no labels, neither configuration has a measured precision, recall,
F1, false-positive rate, or winner.

## Actual end-to-end candidate verification

The initial full `v001` run emitted its first real keyframe at source-relative
1.5667 s before the local supervising command ended during sidecar flushing.
To verify the complete output lifecycle without editing the organizer source,
the first 65 source frames were copied to an ignored local derivative.  The
same frames, camera configuration, detector, tracker, checkpoint, and temporal
settings produced exactly one candidate:

- Trigger: `temporal_fighting_candidate`; timestamp: 1.5667 s.
- 65 frames sampled; 399 person detections; 21 distinct ByteTrack IDs; seven
  temporal windows; five top-`fight` windows; one qualifying review window and
  one emitted packet.
- `validate_candidate_packet` returned no errors.  The unchanged packet has
  four person tracks and a source-relative timestamp.
- Its saved JPEG keyframe exists (146,154 bytes).  The evidence sidecar wrote
  one 37-frame MP4 covering 0.5667–1.7667 s, and OpenCV decoded its first
  frame successfully.
- End-to-end sampled throughput was 4.17 FPS.  Detection mean was 62.23 ms per
  sampled frame; seven temporal windows took 5.064 s (723.48 ms/window);
  peak CUDA allocation/reservation was 654.36/704.0 MiB.

This validates candidate plumbing and evidence retention only.  It is not a
claim that the clip contains fighting.

## Evaluation and limitations

No independently labelled fighting/non-fighting benchmark with verified local
acquisition terms was available.  RWF-2000's official media remains
unavailable, and no mirror or unapproved dataset was used.  Therefore the
independent evaluation set contains 0 positive and 0 negative clips; a
confusion matrix and accuracy metrics are unavailable rather than fabricated.

The development/holdout separation required for threshold selection cannot be
meaningfully performed on unlabeled organizer material.  The CP12 demo config
is consequently an integration setting only, not a selected detector.  Before
any deployment claim, acquire a permitted labelled dataset, define immutable
source-disjoint development/test partitions, include hard negatives (sport,
crowd movement, running, embrace/assistance), and assess calibration and alert
burden with human review.

Remaining failure modes include camera/domain shift, score instability between
overlapping windows, high tracker fragmentation on the short `v001` derivative,
occlusion, interactions that are not fights, and fights outside the temporal
window.  Continue to send all outputs as `needs_review`; do not automate a
safety response from these cues.

## Reproduction

```powershell
.\.venv\Scripts\python.exe -m video_pipeline <local-video> `
  --camera-config video_pipeline\temporal_fighting_review.json `
  --sample-every 1 --device 0 `
  --temporal-fighting-model E:\path\outside\repo\archit11-fight-nofight `
  --temporal-window-frames 16 --temporal-stride-frames 8 `
  --output-root data\raw\local_temporal\keyframes `
  --frame-path-root data/raw/local_temporal/keyframes `
  --jsonl data\raw\local_temporal\candidates.jsonl `
  --evidence-pre-seconds 1 --evidence-post-seconds 1 `
  --evidence-root data\raw\local_temporal\evidence `
  --relative-evidence-root data/raw/local_temporal/evidence

# Exploratory plumbing demo only; not an evaluated threshold.
# Substitute temporal_fighting_demo.json deliberately.
.\.venv\Scripts\python.exe -m pytest -q
```
