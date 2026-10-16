# CP5 Person 1 incident-candidate validation

## Scope and data handling

Five organizer-provided local AVI clips were processed from `E:\honeymindproject\references`. They and every derived annotated frame, keyframe, and report remain ignored and uncommitted because redistribution permission is unverified. The figures below are operational measurements, not ground-truth detection, tracking, or incident-classification accuracy.

Both configurations use YOLO11n COCO-person detection and ByteTrack on the RTX 4050. The **conservative** configuration requires one second of a close/high-motion pair; the **interaction-review** configuration uses the same proximity/motion thresholds but zero persistence, so it can surface a first review candidate. Neither includes a weapon model. The standard person model is not treated as a weapon detector.

| Video | Frames | Person frames | Person detections | Distinct IDs | Continuity hits | Conservative candidates | Interaction-review candidates / timestamp(s) |
|---|---:|---:|---:|---:|---:|---:|---|
| `v001_converted 3.avi` | 193 | 193 | 1,137 | 42 | 1,017 | 0 | 1 `fighting_candidate` / 0.033 s |
| `v003_converted 3.avi` | 89 | 89 | 326 | 19 | 294 | 0 | 1 `fighting_candidate` / 0.033 s |
| `v006_converted 3.avi` | 175 | 175 | 973 | 47 | 887 | 0 | 1 `fighting_candidate` / 0.033 s |
| `v026_converted 3.avi` | 291 | 14 | 14 | 1 | 10 | 0 | 0 |
| `w001_converted 3.avi` | 154 | 154 | 280 | 5 | 269 | 0 | 1 `fighting_candidate` / 5.067 s |

The final interaction-review rerun produced four packets, zero packet-schema errors, zero duplicate event IDs, and four existing/OpenCV-readable keyframes. The conservative run produced no packets. All output paths were unique per video/configuration to avoid cross-video keyframe overwrites.

## Performance

| Video | Conservative FPS / inference ms / marker ms | Interaction-review FPS / inference ms / marker ms |
|---|---|---|
| `v001` | 5.55 / 55.16 / 120.80 | 5.88 / 46.54 / 117.67 |
| `v003` | 9.66 / 21.11 / 79.73 | 9.09 / 21.94 / 85.23 |
| `v006` | 8.06 / 31.26 / 89.87 | 10.43 / 24.84 / 68.72 |
| `v026` | 7.89 / 30.98 / 92.90 | 10.64 / 21.27 / 70.45 |
| `w001` | 7.51 / 33.28 / 96.84 | 10.47 / 23.72 / 69.34 |

GPU inference was synchronized. End-to-end FPS also includes decoding, behavioral processing, and any event/keyframe work; values vary between sequential runs and are not a benchmark of incident accuracy.

## Observations and fixes

- The conservative rule missed review opportunities in the crowded clips because no identical close/high-motion pairing persisted for one second. This is a recall limitation, not evidence that no interaction occurred.
- The zero-persistence review mode initially emitted one candidate per qualifying pair (19 on `v001`, 18 on `v006`). The rule now aggregates all qualifying pairs in a continuous scene into one `fighting_candidate`; the final rerun emitted one candidate for each of `v001`, `v003`, `v006`, and `w001`.
- Three final review cues occur at 0.033 s, immediately after tracking starts. They are useful inspection prompts but may reflect first-frame track motion/association effects, so they must not be interpreted as confirmed early incidents.
- Timestamp-only event IDs collided for simultaneous pairs. Event IDs now include a stable condition-key digest; a regression test covers both interaction episodes and simultaneous weapon flags.
- No reference-video frame met the configured sustained horizontal-box criterion, so no `person_down_candidate` was emitted. Unit tests verify the rule with a synthetic horizontal box; this is not fall-detection validation. `v003` should be reviewed by Person 2 rather than relabelled from this absence.
- No knife/firearm candidate was tested: no specialized weapon model or reviewed weights were supplied. Embedded video text or visual impressions were not used as weapon labels.

## Person 2 integration

Use the portable original fixture at `demo_assets/person1/sample_candidate.jsonl` for checkout-independent integration. For local authorized runs, consume packet JSONL line by line, validate the shared packet shape, resolve `frame_path` relative to the repository root, confirm the file exists, and enqueue it asynchronously. `trigger` is an unconfirmed cue; do not map it directly to a final category or invent confidence.

```python
from pathlib import Path
import json
from datasets_incident_detection.contracts import validate_candidate_packet

repo_root = Path.cwd().resolve()
for line in Path("reports/cp5/interaction_review/v001_converted_3.jsonl").read_text().splitlines():
    packet = json.loads(line)
    assert validate_candidate_packet(packet) == []
    keyframe = (repo_root / packet["frame_path"]).resolve()
    assert keyframe.is_relative_to(repo_root) and keyframe.is_file()
    # Hand packet and keyframe to Person 2's bounded asynchronous consumer.
```

Do not commit or transfer the local organizer output files without written redistribution permission.
