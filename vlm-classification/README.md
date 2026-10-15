# Person 2 — Local VLM classification

Consumes a Person 1 candidate packet, analyzes up to three supplied frame paths using a replaceable local vision adapter, and returns the incident fields in [`../SHARED_CONTRACTS.md`](../SHARED_CONTRACTS.md). A deterministic stub is the default so integration does not require a running model. The optional Ollama adapter uses only Python's standard library.

## Architecture

```text
Person 1 packet → validate/select frames → adapter (stub or local Ollama) → defensive parse/category allowlist → incident record → optional Person 3 POST
```

`classify_candidate(candidate: dict) -> dict` is the synchronous boundary. Structurally invalid packets raise `CandidateError` before an incident exists. `BoundedClassifierWorker` wraps classification in a bounded thread pool. When full, `submit()`/`try_submit()` returns `None` immediately and increments `rejected_count`; Person 1 can count the drop and continue capture without handling an overload exception.

## Contracts

Input requires `event_id`, `camera_id`, `video_source_id`, `timestamp_seconds`, `frame_path`, `tracks`, `trigger`, and ISO-formatted `created_at`; `frame_paths` is optional. IDs must be non-empty strings and timestamps finite/non-negative. Tracks may be empty; each track must include integer `track_id`, non-empty string `class_name`, and four finite numeric `bbox_xyxy` coordinates. Extra track keys are allowed. Relative paths use the process working directory. The primary path is preferred, then additional paths; at most three existing files are sent to the model.

Output keys exactly match the classified incident fields in `SHARED_CONTRACTS.md`: `event_id`, `camera_id`, `timestamp_seconds`, `category`, `summary`, `confidence`, `confidence_type`, `frame_path`, `source`, `processing_ms`, `status`, `evidence_notes`, and `created_at`. Categories are allowlisted. Confidence is always null with type `unavailable`; no confidence score is requested. Unreadable frames or adapter failures return `unknown`/`failed`; malformed/unsupported model answers return `unknown`/`needs_review`; an explicit `unknown` answer is also marked `needs_review`. The stub returns `unknown`/`needs_review` with source `manual`.

## Runtime/model

The selected optional local runtime is Ollama, with model name `moondream` by default. The repository/environment did not have Ollama available at implementation time and machine hardware could not be queried, so model feasibility and inference are **unverified**. This is a configurable adapter, not a claim that this model is accurate on the project footage. Ollama’s model page describes Moondream as a 1.8B vision model and lists a 1.7 GB artifact; the v2 listing gives Apache 2.0 licensing. Verify the exact model/license for your intended use before distribution: [Ollama Moondream](https://ollama.com/library/moondream), [Moondream v2 details](https://ollama.com/library/moondream%3Av2).

The Ollama adapter sends images as base64 to the local `/api/chat` endpoint and requests JSON response format, while retaining defensive parsing. Requests use temperature 0 and a configurable timeout. A configurable total-image-size cap defaults to 16 MiB; it is checked before reading and also enforced during bounded reads. Exceeding it returns a `failed` incident for a structurally valid candidate. Configure it with `--max-image-bytes` or `VLM_MAX_TOTAL_IMAGE_BYTES`. Python code has no third-party package dependencies. Install Python 3.10 or newer; install and start Ollama separately only for VLM mode.

## Setup and run

From `vlm-classification/` on Windows PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Stub mode (no Ollama required):

```powershell
python classify.py examples/candidate.json --runtime stub
```

Ollama mode, after installing Ollama:

```powershell
ollama pull moondream
ollama serve
```

In another terminal, ensure the candidate's frame path points to a real image and run:

```powershell
python classify.py examples/candidate.json --runtime ollama --model moondream --timeout 60 --max-image-bytes 16777216
```

To send the resulting record to Person 3’s documented endpoint:

```powershell
python classify.py examples/candidate.json --runtime ollama --post --backend-url http://127.0.0.1:8000
```

`--post` is opt-in. `OLLAMA_MODEL`, `OLLAMA_BASE_URL`, `VLM_RUNTIME`, `VLM_TIMEOUT_SECONDS`, and `BACKEND_BASE_URL` environment variables can provide corresponding defaults. The backend endpoint is documented but not implemented in this repository yet.

`examples/candidate.json` and `examples/expected_stub_output.json` are a runnable stub example. The tiny PNG is only a fixture for interface testing, not event footage. In the expected output file, `processing_ms` and `created_at` are illustrative; actual values are measured/generated at runtime. No project footage is included.

## Async use

```python
from src.classifier import create_ollama_classifier
from src.worker import BoundedClassifierWorker

worker = BoundedClassifierWorker(create_ollama_classifier(), max_workers=1, max_pending=2)
try:
    future = worker.try_submit(candidate_packet)
    if future is None:
        dropped_candidate_count += 1
    else:
        future.add_done_callback(lambda done: print(done.result()))
finally:
    worker.shutdown(wait=True)
```

The queue capacity is `max_workers + max_pending`. The worker also exposes `rejected_count`. Ollama's network timeout limits each request. Python cannot forcibly terminate an already-running worker thread, so shut down cleanly and keep the worker count small.

## Tests

From `vlm-classification/`:

```powershell
python -m pytest tests -v
```

The suite covers invalid/non-finite inputs and track shapes, invalid input not being posted by the CLI, missing frames, malformed output, categories, overload, image-size limits, Ollama JSON request format, timeout, unavailable Ollama, and stub/VLM adapter paths. It uses temporary frame files and injected adapters; successful live inference requires a running local model and is not part of the automated suite.

## Files

- Added `src/classifier.py`, `src/ollama_adapter.py`, `src/client.py`, `src/worker.py`, and `src/__init__.py`.
- Added `classify.py`, `mock_vlm.py`, `examples/candidate.json`, `examples/expected_stub_output.json`, `examples/sample.png`, and `tests/test_classifier.py`.
- Updated this README and `../docs/PERSON_2_VLM_CLASSIFICATION.md`.

## Limitations and verification

- No local hardware details, GPU, Ollama binary/service, model weights, backend implementation, candidate producer, or sample footage were verified/present.
- Classification quality, latency, model loading time, accuracy, false positives, and misses have not been measured.
- Frame existence is checked, but image decoding/content validation is delegated to the runtime.
- The schema has no explicit error-detail field. Failure details are placed in `evidence_notes` while status is `failed`.
- The backend contract says POST/upsert by event ID; its actual response shape is not documented here, so the client accepts any JSON-object response.
- No confidence estimate is returned. Model-generated summaries may still be incorrect; validate on labelled footage before demo claims.
