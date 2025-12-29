from __future__ import annotations

import io
import json
from pathlib import Path

import pytest

from grouporderai.api.app import create_app
from grouporderai.services.jobs import JobStore
from grouporderai.services.storage import FileStorage


@pytest.fixture()
def app(tmp_path: Path):
    # Ensure isolated folders per test run (no collisions on Windows)
    (tmp_path / "data").mkdir(parents=True, exist_ok=True)
    (tmp_path / "schema_registry").mkdir(parents=True, exist_ok=True)
    (tmp_path / "schemas").mkdir(parents=True, exist_ok=True)

    app = create_app()
    app.config["TESTING"] = True
    return app


def test_parse_creates_job_and_uploads_files(app, tmp_path: Path, monkeypatch):
    """
    POST /api/parse should:
    - create a job json file
    - write uploaded pdf bytes into data/uploads/<job_id>/
    """
    # Patch the module-level singletons used by routes.py
    import grouporderai.api.routes as routes

    routes._jobs = JobStore(base_dir=str(tmp_path / "data"))
    routes._storage = FileStorage(base_dir=str(tmp_path / "data"))

    client = app.test_client()

    data = {
        "files": [
            (io.BytesIO(b"%PDF-1.4 fake pdf bytes"), "sample1.pdf"),
            (io.BytesIO(b"%PDF-1.4 fake pdf bytes 2"), "sample2.pdf"),
        ]
    }

    resp = client.post("/api/parse", data=data, content_type="multipart/form-data")
    assert resp.status_code == 202

    payload = resp.get_json()
    assert "job_id" in payload
    job_id = payload["job_id"]

    # Job file exists
    job_file = (tmp_path / "data" / "jobs" / f"{job_id}.json")
    assert job_file.exists()

    job = json.loads(job_file.read_text(encoding="utf-8"))
    assert job["status"] == "queued"

    # Uploads exist
    upload_dir = tmp_path / "data" / "uploads" / job_id
    assert (upload_dir / "sample1.pdf").exists()
    assert (upload_dir / "sample2.pdf").exists()


def test_get_job_404_for_missing(app):
    client = app.test_client()
    resp = client.get("/api/jobs/not-a-real-job")
    assert resp.status_code == 404


def test_feedback_marks_needs_feedback(app, tmp_path: Path):
    import grouporderai.api.routes as routes

    routes._jobs = JobStore(base_dir=str(tmp_path / "data"))
    routes._storage = FileStorage(base_dir=str(tmp_path / "data"))

    client = app.test_client()

    job_id = routes._jobs.create_job(payload={"type": "parse", "file_count": 1})
    routes._jobs.update_job(job_id, status="completed", result={"files": []})

    resp = client.post(
        "/api/feedback",
        json={"job_id": job_id, "is_correct": False, "reason": "Wrong output"},
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["status"] == "needs_feedback"

    job = routes._jobs.get_job(job_id)
    assert job["status"] == "needs_feedback"
    assert job["result"]["feedback"]["is_correct"] is False
