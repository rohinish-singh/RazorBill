# CP3 acquisition log and local recording plan

## Official-source decisions — 2026-10-15

| Dataset | Official source / terms | Decision | Local path / artifacts |
|---|---|---|---|
| [UR Fall Detection](https://fenix.ur.edu.pl/~mkepski/ds/uf.html) | Official page states CC BY-NC-SA 4.0 and intended non-commercial academic use. It exposes individual RGB, depth, synchronization, and accelerometer archives for 30 fall and 40 ADL sequences. | **Blocked pending sponsor/intended-use confirmation.** The hackathon’s commercial status cannot be assumed. If approved, start with fall-01-cam0-rgb.zip, adl-01-cam0-rgb.zip, each sequence’s data.csv synchronization file, and acc.csv; log SHA-256 and archive-test results. | Reserved: data/raw/ur_fall/; no files downloaded. |
| [Camera Occlusion Detection v1, version 5](https://universe.roboflow.com/voam/camera-occlusion-detection-v1) | Publisher page declares MIT, VOAM, 1,879 images for dataset version 5, but download/export requires a Roboflow sign-in/API workflow. | **Blocked pending account/export-permission verification.** Do not use hosted inference/API keys or scrape previews. | Reserved: data/raw/camera_occlusion_v1/; no files downloaded. |
| [RWF-2000](https://github.com/mchengny/RWF2000-Video-Database-for-Violence-Detection) | Author repository describes the data but official videos are unavailable from the site. | **Blocked.** Request availability/terms from maintainers; do not use mirrors. | Reserved: data/raw/rwf_2000/; no files downloaded. |
| Le2i | The formerly cited official activity page was unavailable during CP3 audit and no authoritative terms were recovered. | **Blocked: source/terms unverified.** | Reserved: data/raw/le2i/; no files downloaded. |

No raw datasets or videos are committed. Each approved download must retain original URL, terms snapshot, date, filenames, SHA-256, archive integrity result, supplied split/source group, and annotations in its manifest; then run datasets_incident_detection validate --check-files and split.

## Consented local staged-recording plan

Obtain written consent and a local usage/retention statement before recording. Use a fixed camera and save no faces beyond the agreed scope.

1. **Zone entry:** one person crosses a marked polygon then leaves; negative: walks near boundary without footpoint entry.
2. **Loitering:** person remains in zone beyond configured dwell; negatives: brief passage and occlusion/track loss.
3. **Crowd gathering:** 3+ consented people persist in zone; negatives: people pass through at staggered times.
4. **Camera-facing:** optional and only as neutral orientation data; do not infer identity, intent, or suspicion.
5. **Health controls:** lens cover, normal lighting change, autofocus/blur, static scene, and source stop—label these as observable conditions, never sabotage.

For every clip record consent reference, camera/source group, start/end intervals, conditions, and SHA-256. Split only by recording session/source group.
