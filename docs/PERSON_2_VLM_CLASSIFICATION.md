# Person 2 — Local VLM Event Understanding and Classification

## Mission and boundary

Person 2 consumes Person 1 candidate packets, analyzes one or a small set of saved frames, and produces the classified incident record defined in `SHARED_CONTRACTS.md`. Inference is replaceable and runs behind a bounded asynchronous worker. Person 2 does not own capture/tracking, persistence/API implementation, or the frontend.

## Implemented architecture

`candidate packet → validation/frame selection → stub or Ollama adapter → JSON parsing and category allowlist → shared incident record → optional backend POST`

Public synchronous interface: `CandidateClassifier.classify_candidate(candidate: dict) -> dict`. Structurally invalid candidates raise `CandidateError` and do not produce an incident. For asynchronous integration, use `BoundedClassifierWorker.try_submit`; it returns a Future or `None` immediately when full, without raising an overload exception. Default is one worker and four pending slots. Rejected submissions are counted in `rejected_count`; the capture loop should report the count and continue. `src.client.post_incident` validates the whole incident before POSTing to `/api/incidents`.

## Input contract

Required: `event_id`, `camera_id`, `video_source_id`, `timestamp_seconds`, `frame_path`, `tracks`, `trigger`, and ISO-formatted `created_at`; `frame_paths` may be omitted. IDs must be non-empty strings; timestamps must be finite and non-negative. Tracks may be empty; each track must contain integer `track_id`, non-empty string `class_name`, and four finite numeric `bbox_xyxy` values. Additional track keys are accepted. The primary frame path is tried first, then `frame_paths`; up to three existing paths are used. Relative paths are resolved from the process working directory.

## Output contract

The returned object has exactly these shared fields: `event_id`, `camera_id`, `timestamp_seconds`, `category`, `summary`, `confidence`, `confidence_type`, `frame_path`, `source`, `processing_ms`, `status`, `evidence_notes`, `created_at`.

Categories are restricted to `person_down`, `fighting`, `tailgating`, `crowd_incident`, `suspicious_activity`, `other`, `unknown`. `confidence` remains null and `confidence_type` is `unavailable`. VLM-backed successful outputs use source `vlm`. Stub outputs use source `manual`, category `unknown`, and status `needs_review`. Missing frame/adapter errors use `unknown`/`failed`; malformed or unsupported model responses use `unknown`/`needs_review`. Durations use a monotonic clock. Summaries ask for visible evidence only and do not infer intent.

## Selected runtime and model

Optional runtime: local Ollama using its HTTP chat API. Default model name: `moondream`. It was selected as a simple local-serving adapter option for the hackathon; it has not been verified on this machine or against the project footage. Ollama lists the Moondream 1.8B vision model and a 1.7 GB artifact, and the v2 listing indicates Apache 2.0 licensing ([model listing](https://ollama.com/library/moondream), [v2 listing](https://ollama.com/library/moondream%3Av2)). Check the upstream listing and intended-use license before distribution. Hardware queries were unavailable, and Ollama was not installed/discoverable here, so model practicality is unverified. Do not report performance/accuracy without evaluation.

The Python module uses only the standard library. Python 3.10+ is required by its type syntax. Ollama is an external optional installation; no cloud service is used. Its API request asks for JSON format and the response still passes through the defensive parser. Total image input defaults to a configurable 16 MiB cap (`--max-image-bytes` or `VLM_MAX_TOTAL_IMAGE_BYTES`); exceeding the limit returns an explicit `failed` record for a valid candidate.

## Setup and commands

From `vlm-classification/` in PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pytest tests -v
```

Stub run:

```powershell
python classify.py examples/candidate.json --runtime stub
```

Local VLM run after installing Ollama:

```powershell
ollama pull moondream
ollama serve
python classify.py examples/candidate.json --runtime ollama --model moondream --timeout 60 --max-image-bytes 16777216
```

The included tiny `examples/sample.png` fixture makes the stub command runnable; it is not event footage. Add `--post --backend-url http://127.0.0.1:8000` to submit to the documented Person 3 route. Backend code is not present in this repository. Model/runtime settings may also be supplied using `OLLAMA_MODEL`, `OLLAMA_BASE_URL`, `VLM_RUNTIME`, and `VLM_TIMEOUT_SECONDS`.

## Tests and verification

`tests/test_classifier.py` covers valid candidate/VLM output, invalid/missing event IDs, non-finite timestamps, invalid track shapes, missing frames, malformed JSON, invalid categories, invalid input not being posted by the CLI, backend-client validation, oversized image failure, JSON request mode, unavailable Ollama, timeout, non-raising bounded overload, ambiguous output, and deterministic stub mode. Tests use temporary files and fake adapters except for an unavailable-service probe against localhost port 1. Live successful Ollama classification is manual and is not claimed as verified.

At implementation time, repository inspection found no prior Person 2 source code to reuse. The current test run used Python 3.14.8 and pytest 9.1.1 on Windows; 20 tests and 11 parameterized subtests passed. The sandbox's default `python` resolves to a Windows Store alias, so the verified run placed the installed Python directory first on `PATH` and pointed `TEMP`/`TMP` to the writable module directory. Ollama and NVIDIA utilities were not found; model inference and hardware feasibility remain unverified. No latency or accuracy values have been measured.

## Files

Added module code at `vlm-classification/src/{classifier,ollama_adapter,client,worker}.py` plus `src/__init__.py`; added `classify.py`, `mock_vlm.py`, `examples/candidate.json`, `examples/expected_stub_output.json`, `examples/sample.png`, and `tests/test_classifier.py`. Updated `vlm-classification/README.md`. No shared contract or other team module was changed.

## Limitations

- Runtime/hardware/model behavior on this machine is unverified.
- Classification accuracy and latency have not been evaluated.
- Frame files are checked for existence but not decoded before submission.
- Backend server and actual POST response are not available for integration verification.
- The shared incident schema has no dedicated error field; failure detail is returned in `evidence_notes`.
- The bounded worker prevents unlimited submissions and counts rejected candidates; Person 1 still needs to call `try_submit()` and report that count in its own metrics.
