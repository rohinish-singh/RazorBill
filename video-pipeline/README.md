# RazorBill — Video Pipeline

**Owner**: Person 1  
**Detailed Guide**: [`../docs/PERSON_1_VIDEO_PIPELINE.md`](../docs/PERSON_1_VIDEO_PIPELINE.md)  
**Contract Reference**: [`../SHARED_CONTRACTS.md`](../SHARED_CONTRACTS.md)

---

## Overview

The `video-pipeline/` module handles video ingestion (pre-recorded clips and simulated live streams), frame sampling, object detection and tracking, anomaly trigger evaluation, and evidence frame extraction. When an anomaly is detected, it packages a **Candidate Event Packet** and pushes it to a non-blocking queue.

---

## Planned Directory Structure

```
video-pipeline/
├── README.md
├── requirements.txt
├── src/
│   ├── ingestion.py       # Video capture and frame sampling loop
│   ├── detection.py       # Object detection & bounding box tracking
│   ├── heuristics.py      # Rule triggers (aspect ratio drop, convergence)
│   ├── evidence.py        # Frame exporter and path generator
│   └── queue_producer.py  # Bounded queue worker and drop counter
├── tests/
│   └── test_heuristics.py # Unit tests on trigger heuristics
└── mock_emitter.py        # Hour 6 mock candidate generator for integration
```

---

## Quickstart & Environment

```bash
# From repository root or video-pipeline/
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Key Dependencies
- `opencv-python-headless`
- `numpy`
- `pydantic`

---

## Core Engineering Directives

1. **Non-Blocking Execution**: The video capture loop must push candidate packets to a bounded queue (`maxsize=50`). Never block frame capture waiting for downstream inference.
2. **Distinct Timestamps**: Record source video offset (`timestamp_seconds`) distinctly from wall-clock time (`created_at`).
3. **Evidence Storage**: Save JPEG frames into `../data/evidence/` with unique names (`evt_<id>_key.jpg`). Store file paths only, never raw image bytes in data structures.
4. **Mock Stub Ready**: Provide `mock_emitter.py` early so Person 2, Person 3, and Person 4 can develop without waiting for detector calibration.

