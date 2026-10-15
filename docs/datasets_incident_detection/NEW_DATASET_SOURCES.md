# CP2 dataset-source audit

| Source | Official access / terms observed | Actual relevance | Acquisition decision |
|---|---|---|---|
| [Camera Occlusion Detection v1](https://universe.roboflow.com/voam/camera-occlusion-detection-v1) | Official Roboflow page identifies VOAM, 773 preview images / 5 dataset versions and an MIT license. It advertises a hosted API requiring an API key; export/download workflow and redistribution conditions were not independently exercised. | Classes include Normal, Human/Object/Weather Occlusion and Sensor Failure; useful for image-level obstruction exploration, not frozen-feed temporal evaluation. | **Not downloaded.** Record MIT as publisher-declared; verify export terms and account/access workflow before use. |
| [CUHK Avenue](https://www.cse.cuhk.edu.hk/~leojia/projects/detectabnormal/dataset.html) | Official page offers 16 train and 21 test clips plus rectangle ground truth, but the reviewed page states no explicit license/usage terms. | General anomaly/stable-scene stress data; not labelled for camera obstruction/darkness/freeze. | **Blocked:** terms unverified; do not download. |
| [AI City Challenge 2024 Track 1](https://www.aicitychallenge.org/2024-data-and-evaluation/) | Official page requires a dataset request form; clicking download accepts a data license agreement. Track 1 is 1080p/30fps synthetic multi-camera people tracking. | Useful for tracking/crowd/zone integration, not camera-health labels; potentially large. | **Blocked:** registration and license acceptance required. Do not bypass. |

Existing CP1 catalogs remain unchanged: RWF-2000/UR Fall/Le2i are unverified and unacquired; local staged material needs consent; UCF-Crime remains deferred. No third-party mirror was used. No source was downloaded in CP2.

The repository includes a local synthetic-camera-health catalog and generator. CP2 generated and validated eight deterministic AVI fixtures with interval annotations locally; generated data is ignored under `data/raw/`.
