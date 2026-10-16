# CP10 — Real temporal fighting review

## Scope and integrity boundary

CP10 adds an optional local temporal fighting-review path for Person 1. It does
not change `SHARED_CONTRACTS.md`, Person 2/3/4 code, CP7–CP9 defaults, or
candidate packet fields. Model scores are raw softmax outputs, not calibrated
incident probabilities. A qualifying output always creates a `needs_review`
candidate only.

All checkpoints, organizer clips, keyframes, JSONL outputs, and evidence MP4s
used below are outside Git. The five organizer clips in
`E:\honeymindproject\references` have no independently supplied labels or
redistribution confirmation, so they are local qualitative examples only.

## Checkpoint audit

Selected checkpoint: `archit11/videomae-base-finetuned-fight-nofight-subset2`.

- The model card declares CC BY-NC 4.0, reports a VideoMAE-base fine-tune on
  the Acts of Aggression CCTV dataset, and explicitly calls the checkpoint
  experimental.
- Its downloaded `config.json` supplies and the runtime verified the mapping
  `0=Fight`, `1=No Fight`; it declares 16 frames and 224-pixel input.
- It loaded under Transformers 4.37.0 with zero missing, unexpected, or
  mismatched keys. The adapter fails closed for any checkpoint with a loading
  mismatch or a mapping other than the audited one.
- It is suitable only for provisional local, non-commercial review under the
  model card's declared terms. Its training-data provenance and performance on
  this project's camera domains remain unverified.

Rejected alternatives:

- `HappyGook/videomae-violence-detector` declares MIT and binary
  violent/non-violent output, but its downloaded configuration had no embedded
  class mapping. Under the model-card-stated Transformers 4.37 runtime, its
  attention checkpoint produced 24 missing and 36 unexpected keys. It is
  explicitly rejected by the adapter; previously observed scores from that
  mismatched load are invalid and not reported as model performance.
- Generic VideoMAE/X3D/Kinetics models are not fighting recognizers. They remain
  unsuitable for assigning a fighting category without a task-specific model.
- Intel's MIT fight-and-violence package is an OpenVINO Qwen2-VL prompted VLM,
  not a compact temporal action classifier; it also adds a separate runtime
  stack. It was not integrated.

## Implementation

`VideoMAEViolenceModel` in `video_pipeline/action.py` performs the
checkpoint-specific path:

1. OpenCV BGR frames are copied to RGB.
2. The checkpoint processor applies its declared resize/center crop to 224,
   rescale, ImageNet normalization, and tensor layout.
3. `SlidingWindowActionAdapter` supplies exactly 16 frames per overlapping
   window. The selected full-rate configuration uses stride 8.
4. The model returns both class scores, label, model ID, and window start/end
   times. The pipeline records temporal latency separately.
5. `temporal_fighting_candidate` only considers the configured `fight`
   label and threshold. A completed no-fight window resets an episode; a stride
   gap does not. This prevents every overlap from emitting an alert while also
   avoiding a false reset between scheduled windows.
6. Existing candidate cooldown/deduplication, keyframe writing, and bounded
   CP9 evidence sidecars apply without a packet-schema change. No tracking
   motion cue is required for a temporal cue, but current tracks are retained
   as context when present.

Use `video_pipeline/temporal_fighting_review.json` for the conservative
0.75 raw-score review threshold. It is a configuration choice, not calibration.

## Actual inference and qualitative outputs

Hardware: NVIDIA GeForce RTX 4050 Laptop GPU, 6141 MiB reported VRAM; CUDA
PyTorch 2.10.0+cu128; Transformers 4.37.0.

One full-video, uniformly sampled 16-frame window was run on each local
organizer clip. These are raw model outputs, not labels or accuracy results:

| Clip | Raw top label / score | Inference latency |
| --- | --- | ---: |
| `v001_converted 3.avi` | Fight / 0.9384 | 924.12 ms |
| `v003_converted 3.avi` | Fight / 0.7582 | 659.33 ms |
| `v006_converted 3.avi` | Fight / 0.9586 | 658.63 ms |
| `v026_converted 3.avi` | Fight / 0.8802 | 643.26 ms |
| `w001_converted 3.avi` | Fight / 0.9462 | 651.24 ms |

The batch reached 609.10 MiB allocated and 768.0 MiB reserved CUDA memory.
A full detector + pose + temporal run on `v001` used 193 sampled frames and
23 temporal windows:

- 1,137 YOLO person detections; 1,479 pose observations and 1,007 pose-track
  matches.
- Eight windows had `fight` as their top label, but their score range was
  only 0.501–0.662. None met the 0.75 threshold, so the correct result was
  zero temporal candidate packets, zero keyframes, and zero evidence clips.
- End-to-end sampled throughput was 4.94 FPS. Detector mean latency was
  28.24 ms/frame; temporal processing totalled 15.225 s, or 661.97 ms per
  scheduled window. Combined peak memory was 666.26 MiB allocated and
  716.0 MiB reserved.

The disagreement between a uniformly sampled whole-clip score and sliding
window scores demonstrates why neither is a clip-level incident decision.
No threshold was lowered to manufacture an alert.

## Dataset evaluation status

No accessible fighting/non-fighting benchmark with verified acquisition terms
was obtained during CP10. RWF-2000 media remains unavailable from its official
repository; the Acts of Aggression training dataset linked by the selected
checkpoint does not establish a redistribution or evaluation grant for this
workspace. No unapproved mirror was used.

Therefore independently labelled evaluation counts are **0 positive / 0
negative**. Confusion matrix, precision, recall, F1, and false-positive rate are
not available and are intentionally not fabricated. The organizer clips cannot
supply those metrics.

## Tests and reproduction

The test suite adds coverage for BGR→RGB copying, numeric CUDA-device
translation, exact temporal windows/stride, positive-window deduplication,
stride-gap handling, contract-compatible temporal candidates, keyframe output,
and evidence sidecars.

```powershell
# Optional local dependency, matching the selected checkpoint's declared runtime
.\.venv\Scripts\python.exe -m pip install -e '.[temporal-action]'

# Model files must live outside the repository and are not committed.
.\.venv\Scripts\python.exe -m video_pipeline <local-video> `
  --camera-config video_pipeline\temporal_fighting_review.json `
  --sample-every 1 --device 0 `
  --temporal-fighting-model E:\path\to\archit11-fight-nofight `
  --temporal-window-frames 16 --temporal-stride-frames 8 `
  --output-root data\raw\local_temporal\keyframes `
  --frame-path-root data\raw\local_temporal\keyframes `
  --jsonl data\raw\local_temporal\candidates.jsonl `
  --evidence-pre-seconds 1 --evidence-post-seconds 1 `
  --evidence-root data\raw\local_temporal\evidence `
  --relative-evidence-root data\raw\local_temporal\evidence

.\.venv\Scripts\python.exe -m pytest -q
```

## Remaining limitations

- The checkpoint's model-card terms are non-commercial and its author warns it
  is experimental. Obtain a compatible license and independently evaluate before
  deployment.
- No independent labelled benchmark, immutable split, or ground-truth accuracy
  result exists yet. A permitted dataset must be acquired before selection,
  calibration, or threshold claims.
- The temporal score is not calibrated and must not be surfaced as a likelihood
  of violence. VLM/human review remains mandatory.
- CPU fallback is implemented through the same PyTorch adapter but was not
  benchmarked. At roughly 0.66 s per GPU window, full-rate sliding inference
  materially reduces end-to-end throughput; increasing temporal stride reduces
  latency pressure but may miss short events and has not been accuracy-tested.
