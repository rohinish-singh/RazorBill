# CP9 implementation plan

## Preserved behavior

CP7's frozen bounding-box baseline and CP8's opt-in same-ID posture-gap mode
remain independently selectable. No Person 1 → Person 2 packet field changes
are planned; every emitted event remains `needs_review`.

## Extension points

1. Add optional pose and action adapter protocols at the video-pipeline boundary.
   Their outputs are internal observations, not shared-packet fields.
2. Associate pose boxes to existing ByteTrack IDs with one-to-one IoU matching;
   reject low-confidence or ambiguous poses.
3. Feed pose-assisted down cues through a separate opt-in rule, retaining the
   existing bounding-box cue and its metrics.
4. Keep action-window outputs as evidence-backed review cues. Generic Kinetics
   labels will never be renamed to “fighting” or “fall”.
5. Add a bounded frame buffer that flushes only after an emitted candidate.
   Store optional clip paths in a local sidecar index keyed by `event_id`, so
   Person 2 can resolve optional evidence without a contract change.

## Model decision criteria

- Pose: test `yolo11n-pose.pt` through the already-installed Ultralytics
  runtime. It is lightweight enough for the RTX 4050 and performs actual
  COCO-17 keypoint inference. Its AGPL-3.0/enterprise licensing must be
  reviewed before any proprietary deployment. RTMPose/MMPose code is Apache-2.0
  but is not installed, and pretrained-weight terms/Windows Python 3.14
  compatibility have not yet been verified.
- Temporal action: implement a sliding-window adapter interface and test double.
  Evaluate VideoMAE and X3D acquisition separately. No generic Kinetics label
  will be treated as a fall/fighting detector; model output remains a raw action
  review cue.

## Evaluation discipline

Use `fall-01`/`adl-01` only for pose configuration development. Do not retune
against CP8's `fall-02`/`adl-02` holdout. Report inference only when it actually
runs; otherwise report the installation, licensing, or label blocker.
