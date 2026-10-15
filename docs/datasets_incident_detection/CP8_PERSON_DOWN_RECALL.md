# CP8 — Person-down candidate recall

## Scope and split discipline

CP8 uses the same provisional, local-only UR Fall subset as CP7. No footage,
derived video, keyframe, model, or packet output is committed. The frozen CP7
baseline (aspect ratio `1.25`, persistence `1.0 s`, zero gap tolerance) remains
unchanged. `fall-01` plus `adl-01` are the designated development pair;
`fall-02` plus `adl-02` are untouched during selection and evaluated once after
configuration selection. These two-clip splits are useful engineering checks,
not reliable accuracy estimates.

## Diagnostic findings

New additive diagnostics record qualifying-posture entry/exit, duration,
maximum aspect ratio, and track-ID appearance/disappearance counts. They do not
change shared packets or conservative rule behavior.

- `fall-01`: all five qualifying frames belonged to ByteTrack ID `4`, split
  across two posture runs. The longest continuous run was `0.100 s`; the
  maximum box aspect ratio was `1.853`.
- `fall-02`: all 15 qualifying frames belonged to ByteTrack ID `1`, split
  across four posture runs. The longest continuous run was `0.133 s`; the
  maximum aspect ratio was `2.121`.

Thus the principal failure is bounding-box posture fluctuation, not a qualifying
track-ID change. General detector gaps did occur, but there is no evidence here
that a fragmentation-tolerant accumulator should join separate IDs. CP8 does
not implement such joining: it could incorrectly combine two nearby people.

## Optional smoothing mode

`IncidentConfig.person_down_gap_tolerance_seconds` is now an opt-in setting
with default `0.0`, preserving the original immediate-reset rule. It carries
posture time only across a short non-qualifying gap for the **same ByteTrack
ID**; it never joins IDs. Candidate evidence includes the chosen tolerance.

The selected review configuration is:

```text
aspect ratio >= 1.25
persistence = 0.25 s
same-ID geometry-gap tolerance = 0.20 s
```

It is a review-candidate setting, not fall classification. A person who is
lying down, crouching, or bent over may satisfy it.

## Development threshold comparison

| Setting | `fall-01` | `adl-01` | Development result |
| --- | --- | --- | --- |
| CP7 frozen: 1.0 s, gap 0 | 0 candidates | 0 candidates | FN, TN |
| CP7 exploratory: 0.25 s, gap 0 | 0 candidates | 0 candidates | FN, TN |
| CP7 exploratory: 0.10 s, gap 0 | 1 candidate | 0 candidates | TP, TN |
| CP8 selected: 0.25 s, gap 0.20 s | 1 candidate | 0 candidates | TP, TN |

The CP8 setting was selected because it restored the dev review cue while
requiring more accumulated posture time than the 0.10 s setting. This is a
small engineering preference, not evidence that it is more accurate.

## One-time held-out evaluation

The selected configuration was evaluated once on `fall-02` and `adl-02`.

- Confusion matrix: TP=1, FP=0, TN=1, FN=0.
- Precision=1.0, recall=1.0, F1=1.0, FPR=0.0.
- `fall-02` emitted one `person_down_candidate` at source-relative 3.003 s;
  `adl-02` emitted zero candidates.
- The emitted packet passed the unchanged shared-contract validator and its
  640×480 keyframe decoded successfully.

These metrics cover one positive and one negative clip only and must not be
used as a claim of reliable real-world performance. The official posture labels
are depth-derived, so CP8 reports no RGB event latency.

## Performance and negatives

The CP8 diagnostic baseline measured 12.85 FPS (`fall-01`) and 12.79 FPS
(`fall-02`); selected-mode runs measured 13.71 FPS on dev `fall-01`, 15.39 FPS
on held-out `fall-02`, and 19.17 FPS on held-out `adl-02`. Variation includes
GPU warm-up and local run overhead; it is not attributed to smoothing alone.
Peak GPU allocation/reservation remained 71.63/88.0 MiB.

The authorized subset contains generic ADL labels only. It does not identify
sitting, bending, crouching, or walking clips, so CP8 cannot honestly add
separately labelled negatives for those activities. No unapproved external
footage was acquired. Those cases are the highest-priority negative collection
for the next benchmark.

## Remaining failures and recommendation

Bounding boxes remain a weak posture cue: camera angle, occlusion, partial-body
detections, actual lying down, and short posture changes can all cause misses or
false review candidates. A pose-based detector or temporal action model is
warranted for the next evaluation phase, but should be compared on a larger,
independently labelled split rather than tuned on these four clips.

The CP8 mode is suitable only for forwarding bounded **review candidates** to a
VLM/human workflow. It is not suitable for automatically declaring that someone
fell.

## Reproduction

```powershell
# Development selection (do not use holdout clips here)
.\.venv\Scripts\python.exe tools\run_urfall_benchmark.py `
  --device 0 --output-root data\raw\ur_fall\cp8_dev_gap020 `
  --person-down-persist-seconds 0.25 `
  --person-down-gap-tolerance-seconds 0.20 `
  --sequences fall-01 adl-01

# One-time held-out evaluation
.\.venv\Scripts\python.exe tools\run_urfall_benchmark.py `
  --device 0 --output-root data\raw\ur_fall\cp8_holdout_gap020 `
  --person-down-persist-seconds 0.25 `
  --person-down-gap-tolerance-seconds 0.20 `
  --sequences fall-02 adl-02
```
