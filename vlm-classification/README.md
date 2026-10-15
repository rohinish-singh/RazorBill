# RazorBill — Local VLM Classification & Summarization

**Owner**: Person 2  
**Detailed Guide**: [`../docs/PERSON_2_VLM_CLASSIFICATION.md`](../docs/PERSON_2_VLM_CLASSIFICATION.md)  
**Contract Reference**: [`../SHARED_CONTRACTS.md`](../SHARED_CONTRACTS.md)  
**Reference Repository**: [Devnil434/Eagle](https://github.com/Devnil434/Eagle)

---

## Overview

The `vlm-classification/` module consumes candidate event packets, runs local Vision-Language Model (VLM) inference on evidence keyframes, classifies events into one of the 7 standardized categories, generates a concise 1–2 sentence evidence-based summary, records inference latency, and transmits the **Classified Incident Record** to the backend API (`POST /api/incidents`).

---

## Planned Directory Structure

```
vlm-classification/
├── README.md
├── requirements.txt
├── src/
│   ├── worker.py          # Asynchronous queue consumer
│   ├── vlm_engine.py      # Local model loader and inference wrapper (inspect Eagle)
│   ├── prompts.py         # Structured output prompts and few-shot templates
│   ├── validator.py       # JSON schema and category validation
│   └── client.py          # HTTP client posting to backend /api/incidents
├── tests/
│   └── test_validator.py  # Validation test suite
└── mock_vlm.py            # Hour 6 mock VLM for early integration
```

---

## Quickstart & Environment

```bash
# Setup virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Local Model Guidance
- **Strict Constraint**: No paid cloud inference APIs. All models must run locally.
- Inspect Eagle's VLM/reasoning implementation and check hardware (GPU/VRAM/RAM) first.
- Recommended lightweight open models:
  - `SmolVLM-500M` or `SmolVLM-Instruct`
  - `Moondream2`
  - `Qwen2-VL-2B-Instruct`
  - Local Ollama running `llava` or `llama3.2-vision`

---

## Classified Incident Format

```json
{
  "event_id": "evt_unique_id",
  "camera_id": "CAM_01",
  "timestamp_seconds": 134.5,
  "category": "person_down",
  "summary": "A person appears to be lying on the floor near the entrance.",
  "confidence": null,
  "confidence_type": "unavailable",
  "frame_path": "data/frames/CAM_01/evt_unique_id.jpg",
  "source": "vlm",
  "processing_ms": 740,
  "status": "classified",
  "evidence_notes": "Visible posture is consistent with a person on the floor.",
  "created_at": "2026-10-15T10:00:01Z"
}
```

---

## Core Engineering Directives

1. **Allowed Categories Only**: Classifications must map strictly to: `person_down`, `fighting`, `tailgating`, `crowd_incident`, `suspicious_activity`, `other`, `unknown`.
2. **Confidence Safety**: Never ask a generative model to invent a probability. Set `confidence` to `null` unless a real score exists; `confidence_type`: `"unavailable"` or documented score semantics.
3. **Real Latency Tracking**: Measure and record actual inference duration in `processing_ms`. Never invent numbers.
4. **Decoupled Processing**: The VLM worker must consume asynchronously so it never stalls capture or detection loops.
