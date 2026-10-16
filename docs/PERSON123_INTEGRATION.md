# Person 1 → Person 2 → Person 3 local integration

## Status

The local integration branch imports only Person 2's VLM package and Person 3's
FastAPI/SQLite package. Existing CP10–CP13 Person 1 modules/configuration remain
unchanged. `SHARED_CONTRACTS.md` is unchanged.

On 2026-10-16, a real Person 1 CP13 temporal candidate was resolved from its
repository-relative keyframe, classified by the deterministic fallback because
no Ollama model is installed, posted to a live local FastAPI process, persisted
to an ignored SQLite database, retrieved through list/by-ID endpoints, and
returned by `Summarize incidents from the last 2 hours.` This verifies transport
and persistence, not Moondream inference.

Regression status on this Windows host: Person 1 suite 61 passed; Person 2 suite
23 passed; backend suite 94 passed with three symlink tests deselected after the
full backend run showed `WinError 1314` while attempting to create symlinks.
Those three tests require Windows Developer Mode or symlink privilege; their
security assertions did not execute in this account. The remaining backend
tests passed, with one upstream FastAPI deprecation warning.

## Model prerequisite

`ollama list` returned no installed models. Do not claim real VLM inference
until the following user-approved local download completes:

```powershell
ollama serve
ollama pull moondream
ollama list
```

The VLM adapter sends `stream:false`, `format:"json"`, a deterministic
temperature, and image bytes only to local Ollama. It preserves Person 1
`event_id`, `camera_id`, `timestamp_seconds`, and canonical `frame_path`.
`--frame-root` resolves repository-relative and Windows paths for local reads
without rewriting the stored contract reference. Missing frames, bad JSON, and
Ollama errors produce explicit `failed`/`needs_review` records.

## Run the local demo

Open one PowerShell terminal for the API:

```powershell
Set-Location E:\honeymindproject\RazorBill
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
$env:RAZORBILL_DB_PATH = "$PWD\data\raw\person123_demo.sqlite3"
.\.venv\Scripts\python.exe -m uvicorn backend.src.main:app --host 127.0.0.1 --port 8000
```

In a second terminal, use fallback mode when Moondream is unavailable:

```powershell
Set-Location E:\honeymindproject\RazorBill\vlm-classification
..\.venv\Scripts\python.exe classify.py `
  E:\honeymindproject\RazorBill\data\raw\person1_handoff\fighting\candidates.jsonl `
  --runtime stub --frame-root E:\honeymindproject\RazorBill `
  --post --backend-url http://127.0.0.1:8000
```

After `ollama pull moondream` succeeds, replace `--runtime stub` with:

```powershell
--runtime ollama --model moondream --ollama-url http://127.0.0.1:11434
```

Retrieve persisted incidents and query a validated relative-time filter:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/incidents
Invoke-RestMethod http://127.0.0.1:8000/api/incidents/<event_id>
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/query `
  -ContentType application/json -Body '{"question":"Summarize incidents from the last 2 hours."}'
```

## RWF-2000 held-out evaluation

No RWF media was present when this was prepared. Once independently acquired
and verified, point only to the untouched original held-out split with sibling
`Fight/` and `NonFight/` directories. The command never falls back to a train
or development split:

```powershell
Set-Location E:\honeymindproject\RazorBill
.\.venv\Scripts\python.exe tools\run_rwf2000_evaluation.py `
  --test-root data\raw\rwf2000\test `
  --temporal-model E:\honeymindproject\model_cache\archit11-fight-nofight `
  --camera-config video_pipeline\temporal_fighting_review.json `
  --output-root data\raw\rwf2000\evaluation_heldout --device 0
```

It writes ignored JSON with separate clip-level VideoMAE and final temporal
candidate confusion matrices, precision, recall, F1, accuracy, false-positive
rate, per-clip candidate counts, and processing metrics. Do not select a
threshold from this held-out split.

## Limitations

Real Moondream inference is pending local model installation. The successful
integration run used the documented deterministic fallback and must not be
described as VLM output. The backend stores accessible path references but its
default evidence-serving route is rooted at `data/frames`; CP13 `data/raw`
handoff files remain local inspection inputs unless a deployment-owned evidence
root is configured.
