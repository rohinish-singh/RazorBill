# CP11 — Real gun/knife detection

## Scope

CP11 adds an opt-in Person 1 weapon-review path. It keeps person detection,
ByteTrack, pose, temporal action, evidence sidecars, and the unchanged Person 1
candidate packet intact. Weapon outputs are candidate evidence with
`needs_review`; they are not confirmed weapon classifications and raw detector
scores are not calibrated probabilities.

No weights, input images, test videos, annotated output, keyframes, JSONL, or
evidence clip is tracked in Git.

## Checkpoint verification and licensing

Selected local checkpoint:

- Hugging Face model: `cosgun99/gun-knife-yolo11n`
- Actual repository file: `best.pt`, 5,474,259 bytes
- SHA-256:
  `07241A8FC57D0F3FD29231DD72B9F452375745290B2185440DE0165590997CB5`
- Runtime: Ultralytics 8.4.177, detection task, 2 classes
- Verified from loaded weights: `0=gun`, `1=knife`
- Internal mapping: `gun -> firearm -> weapon_firearm_candidate`;
  `knife -> knife -> weapon_knife_candidate`.

The model card metadata declares MIT and academic demonstration/comparative
evaluation intent, but those are author claims. It describes a custom merged
dataset without independently verifiable dataset provenance in this checkpoint
audit. The checkpoint's MIT metadata does **not** settle Ultralytics framework,
base-weight, or deployment obligations. Ultralytics' AGPL-3.0/enterprise
licensing must be evaluated separately before any deployment.

The adapter fails closed for missing files and for any loaded model whose names
are not exactly `{0: gun, 1: knife}`.

## Implementation

`video_pipeline.weapons.UltralyticsGunKnifeDetector` is a separate optional
adapter, enabled only by `--weapon-model`. It accepts CUDA device `0` through
Ultralytics and falls back to CPU when supplied `--device cpu`. It returns
mapped labels, native class IDs/names, boxes, and raw confidence.

`WeaponTemporalFilter` bounds state by label, spatial IoU and a maximum time
gap. Default CLI behavior requires two spatially associated observations within
0.5 seconds. It retains first detection time, strongest detection time, count,
and strongest supporting frame. One continuous episode results in one existing
marker event; marker cooldown/deduplication prevents repeated candidates. A
single observation is available only by explicitly setting
`--weapon-min-observations 1` for debugging.

When qualified, the existing marker engine writes the permitted weapon metadata
inside internal event evidence, saves the strongest available supporting frame
as the candidate keyframe, and registers an ordinary CP9 evidence sidecar. The
shared packet receives no new fields.

## Local real-inference smoke tests

All files below were stored outside Git and used only locally.

- Firearm positive: [My glock 17, Wikimedia Commons](https://commons.wikimedia.org/wiki/File:My_glock_17.jpg), CC BY-SA 4.0.
  At confidence 0.25 and image size 640, actual CUDA inference returned
  `gun` at 0.8796. A five-frame, 10 FPS repeated-image smoke video returned
  five firearm detections, confirmed after two observations, emitted one
  `weapon_firearm_candidate` at source-relative 0.1 s, and wrote a valid
  keyframe plus three-frame evidence MP4.
- Knife positive: [Knife in the kitchen, Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Knife_in_the_kitchen.jpg), CC BY-SA 4.0.
  Actual still-image CUDA inference returned `knife` at 0.4319. A 640×480
  derived video only returned one detection and correctly did not confirm. An
  original-resolution repeated-image smoke video returned five knife detections,
  confirmed after two observations, emitted one
  `weapon_knife_candidate` at 0.1 s, and wrote a valid keyframe plus
  three-frame evidence MP4.
- Harmless negative: [Red apple on white background, Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Red_apple_on_white_background.jpg), CC0.
  At 0.25, the model incorrectly returned `gun` at 0.3668. This is a real
  false positive on a harmless object, not a benchmark metric. At 0.50 this
  image is suppressed, but the tested knife still is also below that threshold;
  CP11 does not claim a validated threshold.

Both generated smoke packets passed `validate_candidate_packet`. Their
keyframes existed and their evidence clips decoded. The smoke sources contain
no people, so packet track arrays were correctly empty.

## Measured local performance

RTX 4050 Laptop GPU, 6,141 MiB reported VRAM, CUDA PyTorch environment:

- Direct still inference: firearm 2,966.69 ms including cold model start;
  knife 117.05 ms after warm-up. Peak allocation/reservation was 66.54/90.0
  MiB for the direct detector process.
- Firearm video pipeline: five frames; 1.80 sampled FPS end to end;
  205.01 ms total weapon inference (41.00 ms/frame); peak 81.99/98.0 MiB.
- Original-resolution knife video pipeline: five frames; 1.38 sampled FPS;
  221.47 ms total weapon inference (44.29 ms/frame); peak 81.99/98.0 MiB.

These short synthetic-temporal videos are functionality smoke tests, not
throughput benchmarks or accuracy evaluation. Person detector warm-up and
high-resolution frame handling dominate their end-to-end FPS.

## Usage

```powershell
# Weights must be obtained from the verified source into an ignored external cache.
.\.venv\Scripts\python.exe -m video_pipeline <local-video> `
  --camera-config video_pipeline\weapon_review.json `
  --sample-every 1 --device 0 `
  --weapon-model E:\path\outside\repo\best.pt `
  --weapon-confidence 0.25 --weapon-imgsz 640 `
  --weapon-every 1 --weapon-min-observations 2 --weapon-max-gap-seconds 0.5 `
  --output-root data\raw\local_weapon\keyframes `
  --frame-path-root data\raw\local_weapon\keyframes `
  --jsonl data\raw\local_weapon\candidates.jsonl `
  --evidence-pre-seconds 1 --evidence-post-seconds 1 `
  --evidence-root data\raw\local_weapon\evidence `
  --relative-evidence-root data\raw\local_weapon\evidence
```

## Tests and limitations

The deterministic suite covers exact gun/knife mapping, invalid mappings,
missing weights, confirmation, spatially unrelated/intermittent detections,
episode deduplication, disabled behavior, contract packet validation, keyframe
creation, and evidence decoding.

No independently labelled weapon benchmark or calibrated operating threshold is
available. The apple false positive and sensitivity to knife resolution show
that this detector must not trigger autonomous safety actions. Real surveillance
accuracy, concealment/occlusion behavior, demographic/camera-domain effects,
and legitimate-object false positives require a permitted independent
evaluation dataset before deployment.
