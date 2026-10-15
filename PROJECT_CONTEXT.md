# Dataset incident detection checkpoint ledger

## CP0 carry-forward

See `docs/datasets_incident_detection/CP0_ARTIFACT_HANDOFF.md` for the location and preservation plan of the pre-repository CP0 artifacts. Their recommendations are internal proposals; `SHARED_CONTRACTS.md` remains authoritative.

## CP1

Status: complete pending team review. CP1 adds only offline dataset/contract/evaluation tooling and no raw data, weights, models, or teammate-owned pipeline code.

## CP2

Status: complete pending review. Added the standalone behavioral marker engine, synthetic-data generator source, a synthetic catalog, and CP2 documentation. No external dataset or model was downloaded; camera-health mapping remains an internal compatibility proposal using the shared `other` category.

## CP3

Status: complete pending review. Person 1 owns the new local video file pipeline. It is contract-compatible and measured on CPU-only YOLO11n smoke inputs; GPU inference, real person-track evaluation, and external dataset acquisition remain blocked as documented.

## CP4

Status: local checkpoint pending review. CUDA inference and a real staged-video restricted-zone candidate were verified locally; generated media remains ignored pending sharing authorization. Person 1 added conservative continuous-alert suppression, configurable relative keyframe paths, and metrics for detection/track observations without changing the shared contract.

## Person 1 incident candidates

Status: local implementation pending review. Person 1 now has opt-in review cues for person-down and close/high-motion interactions, and accepts explicit knife/firearm flags only from a separately supplied specialized detector. No external weapon model, unverified reference footage, or shared-contract change was added.

## CP5

Status: local validation complete pending review. Five organizer clips were tested locally under conservative and interaction-review configurations; results and limitations are documented without committing footage. Person 2 has an original, portable contract fixture and keyframe for integration testing.

## CP6

Status: benchmark readiness complete; acquisition blocked pending intended-use confirmation. UR Fall's official page identifies CC BY-NC-SA 4.0 non-commercial academic use, but the hackathon's organizer/sponsor classification is undocumented. No external media was downloaded or benchmark metric fabricated. A clip-level candidate evaluator is ready for an approved, independently sourced run.

## CP7

Status: local-only UR Fall subset benchmark complete under the user's provisional non-commercial-use assumption. The frozen person-down baseline missed both selected positive clips (TP=0, FN=2); a separately held-out two-clip persistence experiment is documented as exploratory only. No dataset media, derived artifact, model weight, or shared-contract change is committed.

## CP8

Status: local Person 1 recall investigation complete. Track-level diagnostics found posture-box fluctuation rather than qualifying track-ID fragmentation. An opt-in same-ID gap tolerance preserves conservative defaults and produced a review candidate on the tiny held-out pair; it is documented as non-generalizable and never as automatic fall classification.

## CP9

Status: local Person 1 pose/evidence extension complete pending review. YOLO11n-pose ran locally on the CP8 development fall clip and emitted one contract-valid, pose-geometry review candidate with a decodable bounded evidence clip. Conservative bounding-box defaults remain unchanged. The temporal-action adapter is present, but a real VideoMAE checkpoint could not be acquired in this environment, and generic Kinetics labels are not incident labels; no fighting/fall claim is made from it.
