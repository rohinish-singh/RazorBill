# Person 1 portable fixture for Person 2

`sample_candidate.jsonl` contains one exact Person 1 → Person 2 candidate packet. Its `frame_path` resolves from the repository root to `synthetic_review_keyframe.ppm`, an original 8×8 PPM image created solely to test path handling. It contains no human footage and is not evidence of fighting, a weapon, or any real incident.

## Consume

1. Read the JSONL one line at a time.
2. Validate each object with `datasets_incident_detection.contracts.validate_candidate_packet`.
3. Resolve `frame_path` relative to the cloned repository root; do not accept absolute paths or paths escaping that root.
4. Treat `trigger` as a review cue, enqueue the keyframe asynchronously, and let Person 2 determine whether a supported category can be assigned.

Example:

```python
from pathlib import Path
import json

repo_root = Path.cwd()
packet = json.loads((repo_root / "demo_assets/person1/sample_candidate.jsonl").read_text().splitlines()[0])
keyframe = (repo_root / packet["frame_path"]).resolve()
assert keyframe.is_file() and keyframe.is_relative_to(repo_root.resolve())
```

The CP5 organizer-video reports, JSONL packets, and keyframes stay in ignored `reports/` and `data/frames/` because redistribution permission was not provided.
