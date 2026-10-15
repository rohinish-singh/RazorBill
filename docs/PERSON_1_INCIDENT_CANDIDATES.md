# Person 1 incident candidates

## Scope

Person 1 creates conservative, review-only candidates. It does not make a legal, safety, or identity determination. The authoritative Person 1 → Person 2 packet remains unchanged; internal cue evidence is intentionally not added as unsupported packet fields.

## Available candidate sources

| Trigger | Internal category | Signal | Limitation |
|---|---|---|---|
| `person_down_candidate` | `person_down` | A person box is sufficiently horizontal for a sustained interval. | Bounding-box geometry can be caused by camera angle, crouching, occlusion, or detection error. |
| `fighting_candidate` | `fighting` | Two tracked people are close together and show sustained high image-plane motion. | Proximity/motion is not proof of fighting. |
| `weapon_knife_candidate` | `other` | Explicit `knife` output from a supplied specialized detector. | Requires a reviewed model, class mapping, and human review. |
| `weapon_firearm_candidate` | `other` | Explicit `firearm` output from a supplied specialized detector. | Requires a reviewed model, class mapping, and human review. |
| Existing zone/crowd/health triggers | Existing categories | Behavioral or camera-health rules. | See marker definitions and camera configuration. |

All generated events have `status: needs_review`. Person 2 is responsible for asynchronous visual-language review and category confirmation.

## Local review command

This command enables only geometry/motion cues. It is appropriate for local inspection of approved footage; it does not establish accuracy or ground truth.

```powershell
.\.venv\Scripts\python -m video_pipeline <local-video> --camera-config video_pipeline\incident_candidate_demo.json --sample-every 1 --device 0 --output-root data\frames --frame-path-root data/frames --jsonl reports\incident_candidates.jsonl
```

`interaction_motion_review_demo.json` is deliberately a separate, local-review configuration: it sets fight persistence to zero and disables the person-down geometry cue. It can surface a first-frame proximity/motion candidate for inspector review, but must not be presented as a calibrated fight detector or used as a production configuration.

## Specialized weapon detector

Standard COCO YOLO11n is a person detector in this pipeline and must not be treated as a knife/firearm detector. A weapon candidate requires a separately obtained model whose license permits the intended use and whose class IDs are explicitly mapped:

```powershell
.\.venv\Scripts\python -m video_pipeline <local-video> --camera-config video_pipeline\incident_candidate_demo.json --device 0 --object-model <reviewed-weapon-model.pt> --object-label 0=knife --object-label 1=firearm --output-root data\frames --frame-path-root data/frames --jsonl reports\incident_candidates.jsonl
```

The program rejects an object model without explicit `--object-label` mappings, and accepts only `knife` or `firearm`. Do not use unreviewed weights, assume generic COCO classes identify weapons, or publish restricted test footage.
