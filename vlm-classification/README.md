# RazorBill — Local VLM Classification & Summarization

**Owner**: Person 2  
**Detailed Guide**: [`../docs/PERSON_2_VLM_CLASSIFICATION.md`](../docs/PERSON_2_VLM_CLASSIFICATION.md)  
**Contract Reference**: [`../SHARED_CONTRACTS.md`](../SHARED_CONTRACTS.md)

---

## Overview

The `vlm-classification/` module consumes candidate event packets, runs local Vision-Language Model (VLM) inference on evidence frames, classifies events into one of the 7 standardized categories, generates a concise 1–2 sentence factual summary, records inference latency, and transmits the **Classified Incident Record** to the backend API.

---

## Planned Directory Structure

```
vlm-classification/
├── README.md
├── requirements.txt
├── src/
│   ├── worker.py          # Asynchronous queue consumer
│   ├── vlm_engine.py      # Local model loader and inference wrapper
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
- Recommended lightweight open models:
  - `SmolVLM-500M` or `SmolVLM-Instruct`
  - `Moondream2`
  - `Qwen2-VL-2B-Instruct` (with 4-bit quantization via `bitsandbytes` or `llama.cpp`)
  - Local Ollama running `llava` or `llama3.2-vision`

---

## Core Engineering Directives

1. **Allowed Categories Only**: Classifications must map strictly to: `person_down`, `fighting`, `tailgating`, `crowd_incident`, `suspicious_activity`, `other`, `unknown`.
2. **Real Latency Tracking**: Measure and record actual inference duration in `processing_ms`. Never invent numbers.
3. **Decoupled Processing**: The VLM worker must consume asynchronously from an in-memory queue or filesystem inbox so it never delays video ingestion.
4. **Mock Stub Ready**: Provide `mock_vlm.py` by Hour 6 so Person 3 and Person 4 can test end-to-end event propagation before local model weights are finalized.

