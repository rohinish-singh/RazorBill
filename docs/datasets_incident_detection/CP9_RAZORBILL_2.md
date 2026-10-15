# CP9 — RazorBill 2.0: pose, temporal action, and evidence fusion

## Scope and preserved behavior

CP9 is a Person 1 local-only extension. It preserves the CP7 frozen bounding-box baseline and CP8 optional same-ID posture-gap configuration. It does not alter `SHARED_CONTRACTS.md`, Person 2/3/4 code, packet fields, raw UR Fall media, generated keyframes/evidence, or model weights. All emitted candidates remain review cues, not confirmed incidents.

The implementation plan is retained in `CP9_IMPLEMENTATION_PLAN.md`. The only threshold selection below used the designated CP8 development pair (`fall-01`, `adl-01`). CP8 holdout clips (`fall-02`, `adl-02`) were not opened or used for CP9 selection or evaluation. No new independently labelled footage or separately labelled sitting/bending/crouching/walking negatives were available with confirmed local-use permission.

## Model and dependency audit

| Component | Decision | Local result | Licensing / semantic limit |
| --- | --- | --- | --- |
| YOLO11n-pose | Selected optional pose adapter | `yolo11n-pose.pt` ran on RTX 4050: one initial RGB frame returned one box and 17 keypoints; it then ran through the full `fall-01` development clip. | Ultralytics offers AGPL-3.0 and enterprise licensing; a deployment owner must choose a compatible option. COCO 17-keypoint posture geometry is not fall recognition. |
| RTMPose / MMPose | Not selected | MMPose/MMCV were not installed; no weight/runtime evaluation was performed. | MMPose source is Apache-2.0, but checkpoint terms and Windows runtime compatibility require separate review. |
| VideoMAE Kinetics | Optional adapter only | `transformers` imported locally, but an unauthenticated checkpoint fetch left an incomplete zero-byte weight download and did not reach inference. | The examined `MCG-NJU/videomae-base-finetuned-kinetics` card declares CC-BY-NC-4.0. Its generic Kinetics labels must not be equated with fighting, falling, or weapons. |
| X3D / PyTorchVideo | Not selected | PyTorchVideo was not installed and no checkpoint was downloaded. | PyTorchVideo source is Apache-2.0; pretrained checkpoint provenance/terms and generic Kinetics semantics need separate review. |

No dedicated, licensed weapon model or labelled fighting-action model was selected. Existing optional knife/firearm flags still require an explicitly mapped specialized detector. A generic detector or generic action class cannot silently become a weapon or fighting alert.

## Implemented pipeline

`video_pipeline.pose.UltralyticsPoseEstimator` produces COCO keypoints locally. `associate_pose_cues` performs greedy, one-to-one association only where a person track and pose box reach IoU >= 0.30. It rejects poses with fewer than six keypoints whose confidence is at least 0.30; unmatched, weak, and additional poses produce no cue. The cue is a visible-keypoint width/height posture ratio, not a fall label.

Pose activation is opt-in through `IncidentConfig.pose_enabled`. It produces a separate `pose_person_down_candidate` after configured temporal persistence, with `cue_source: pose_geometry` and a review caveat in event evidence. It does not replace or weaken `person_down_candidate` bounding-box behavior. The demo uses `pose_review_demo.json` (0.25 s persistence); the explicitly development-only configuration uses 0.10 s in `pose_review_development.json`.

`EvidenceBuffer` retains a bounded pre-event ring and only continues collecting until each candidate's requested post-event end time. It writes a collision-safe `event_id.mp4` plus `index.jsonl` sidecar containing event ID, clip path, source-relative start/end time, output FPS, and frame count. The Person 1 packet remains exactly the shared schema; the evidence location is deliberately not injected into it. Existing marker cooldowns/deduplication remain in force. Cross-rule fusion was intentionally not added: joining independent cues without identity certainty could collapse unrelated people into a single alert.

`SlidingWindowActionAdapter` is unit-tested with an injected local model and supports bounded windows and stride. `VideoMAEActionModel` is lazy and local only; it must not be enabled as incident detection until a compatible checkpoint is deliberately acquired and evaluated. Any raw label/score is uncalibrated review evidence, not a packet confidence or a confirmed category.

## Actual development run

The following command was run on the local, ignored UR Fall development clip. It is not a benchmark or a claim of fall-detection accuracy.

```powershell
.\.venv\Scripts\python.exe -m video_pipeline `
  data\raw\ur_fall\derived\fall-01-cam0.mp4 `
  --camera-config video_pipeline\pose_review_development.json `
  --sample-every 1 --device 0 --pose-model yolo11n-pose.pt `
  --output-root data\raw\ur_fall\cp9_pose_dev\keyframes `
  --frame-path-root data\raw\ur_fall\cp9_pose_dev\keyframes `
  --jsonl data\raw\ur_fall\cp9_pose_dev\fall-01.jsonl `
  --evidence-pre-seconds 0.5 --evidence-post-seconds 0.5 `
  --evidence-root data\raw\ur_fall\cp9_pose_dev\evidence `
  --relative-evidence-root data\raw\ur_fall\cp9_pose_dev\evidence
```

Observed on the RTX 4050:

| Clip/configuration | Frames sampled | Person detections | Pose observations / matches | Candidates | Sampled FPS | Peak CUDA allocated / reserved |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `fall-01`, pose review 0.25 s | 160 | 116 | 143 / 115 | 0 | 14.48 | 83.04 / 100.0 MiB |
| `fall-01`, development pose 0.10 s | 160 | 116 | 143 / 115 | 1 | 14.18 | 83.04 / 100.0 MiB |
| `adl-01`, development pose 0.10 s | 150 | 139 | 145 / 139 | 0 | 13.67 | 83.04 / 100.0 MiB |

On `fall-01`, the maximum observed pose posture ratio was 2.188 and six frames met the pose geometry threshold. The 0.10 s setting emitted one `pose_person_down_candidate` at source-relative 4.337381556 seconds. It passed `validate_candidate_packet`; its saved keyframe exists; the evidence sidecar clip decoded and contained 29 frames (3.837–4.837 s at 29.972 FPS). The stricter 0.25 s configuration emitted no candidate on that same clip. This is one development positive and one development negative only—not a selection-free precision, recall, or F1 measurement.

## Evaluation limits and failure risks

- Pose geometry can still confuse lying down, bending, crouching, occlusion, camera angle, and partial skeletons with a fall-like posture. It does not measure a transition from upright to down.
- ByteTrack and pose detector discrepancies can leave people unmatched; the implementation rejects rather than guesses at multiple associations.
- The only local positive/negative samples are too small for accuracy claims. CP8 holdout remains preserved; an independent labelled test set is required before any comparison or production recommendation.
- VideoMAE inference did not run because the checkpoint was not acquired; future work needs an approved local cache/download and a task-labelled action model. Generic Kinetics label scores are not calibrated incident confidence.
- Evidence MP4s are bounded by requested pre/post duration but codec write failure is intentionally non-fatal to shared packets. The sidecar index makes evidence discoverable without changing the contract.

## Reproduction and verification

Run conservative pose review with `pose_review_demo.json`; use the development configuration only for the documented development check above. Generated media must remain under ignored `data/raw/` paths.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m video_pipeline <local-video> `
  --camera-config video_pipeline\pose_review_demo.json `
  --device 0 --pose-model yolo11n-pose.pt `
  --evidence-pre-seconds 1 --evidence-post-seconds 2 `
  --evidence-root data\raw\local_evidence `
  --relative-evidence-root data\raw\local_evidence
```

The temporal action adapter can be exercised with a trusted injected model in tests. Do not download or commit a model checkpoint automatically; first record the exact weight source, terms, checksum, labels, and permitted use.
