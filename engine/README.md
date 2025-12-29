# Group Order AI

Schema-driven PDF parser for group food orders (Grubhub, EZCater, Sharebite, etc.) with:

- A Flask API for uploading PDFs and tracking async parsing jobs
- A lightweight worker that processes queued jobs from disk
- JSON outputs written to `data/outputs/<job_id>/...json`

This repository is API-first (no frontend UI).

## What This Project Does

Given one or more order PDFs:

1. Detects the platform (example: `grubhub`)
2. Loads the matching schema JSON (from `schema_registry/active` first, then `schemas/`)
3. Parses order-level fields + individual line items
4. Saves a normalized JSON output file per PDF

## Repository Layout

- `src/api/` Flask app + routes
- `src/services/` job store, worker, orchestrator pipeline
- `src/parsing/` PDF text extraction + schema-driven parser
- `schemas/` shipped platform schemas (`grubhub.json`, `ezcater.json`, ...)
- `schema_registry/` optional overrides (active schemas + history)
- `data/` runtime folders (uploads, jobs, outputs)

## Prerequisites

- Python `>=3.13`
- Poetry `>=2.x`

## Setup

From the project root:

```bash
poetry install
```

## Run (Developer Guide)

You typically run two processes:

- Flask API (foreground)
- Worker (background) that picks up queued jobs and writes outputs

### Windows (PowerShell)

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\dev_run.ps1
```

You should see:

- `Running on http://127.0.0.1:5000`

### macOS / Linux (bash)

```bash
chmod +x scripts/dev_run.sh
./scripts/dev_run.sh
```

### Verify The API Is Running

The root route `/` returns `404` (there is no UI). Use an API route:

```powershell
curl.exe -i http://127.0.0.1:5000/api/jobs/abc
```

Expected response:

- `404` with JSON `{ "error": "Job not found: abc" }`

Note: in PowerShell, `curl` is an alias for `Invoke-WebRequest`. Use `curl.exe`.

## API Reference

Base URL: `http://127.0.0.1:5000`

### `POST /api/parse`

Upload one or more PDFs.

- Content-Type: `multipart/form-data`
- Field name: `files` (repeatable)

Example (Windows / PowerShell):

```powershell
$pdf = "C:\full\path\to\order.pdf"
curl.exe -s -X POST http://127.0.0.1:5000/api/parse -F "files=@$pdf"
```

Response:

```json
{ "job_id": "...", "status": "queued" }
```

Where files are stored:

- Uploaded PDFs: `data/uploads/<job_id>/...`
- Job JSON: `data/jobs/<job_id>.json`
- Output JSON(s): `data/outputs/<job_id>/...json`

### `GET /api/jobs/<job_id>`

Poll job status and retrieve parsing results.

```powershell
$jobId = "<job_id>"
curl.exe -s http://127.0.0.1:5000/api/jobs/$jobId
```

Statuses:

- `queued` → waiting for worker
- `running` → worker is parsing
- `completed` → results attached under `result.files[]`
- `failed` → see `error`
- `needs_feedback` → feedback submitted as incorrect

### `POST /api/feedback`

Store correctness feedback against a job.

```powershell
curl.exe -s -X POST http://127.0.0.1:5000/api/feedback `
  -H "Content-Type: application/json" `
  -d '{ "job_id": "<job_id>", "is_correct": false, "reason": "Wrong client name" }'
```

## How Parsing Works (Code Map)

- API upload endpoint: `src/api/routes.py:14`
- Worker loop: `src/services/worker.py:52`
- Main pipeline: `src/services/orchestrator.py:13`
- Platform detection: `src/parsing/platform_detect.py:10`
- Schema loading (active overrides first): `src/registry/repo.py:21`
- Parser implementation: `src/parsing/parser.py:161`

## Schemas

Shipped schemas live in `schemas/`.

At runtime, schema lookup prefers:

1. `schema_registry/active/<platform_id>.json` (if present)
2. `schemas/<platform_id>.json`

Schema docs: `schemas/SCHEMA_GUIDE.md`

## Tests

```bash
poetry run pytest -q
```

## Troubleshooting

### Nothing loads in the browser

This project is API-only. Use `/api/...` endpoints.

### Jobs stay `queued`

The worker is not running. Start via `scripts/dev_run.ps1` / `scripts/dev_run.sh` or run it directly:

```bash
poetry run python scripts/run_worker.py
```

### Platform is detected but fields are wrong

Update the corresponding schema in `schemas/<platform_id>.json` or create an override in
`schema_registry/active/<platform_id>.json`.

