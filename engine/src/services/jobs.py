from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from domain.errors import JobNotFoundError


@dataclass(frozen=True)
class JobPaths:
    base_dir: Path

    @property
    def jobs_dir(self) -> Path:
        return self.base_dir / "jobs"

    def ensure(self) -> None:
        self.jobs_dir.mkdir(parents=True, exist_ok=True)

    def job_file(self, job_id: str) -> Path:
        return self.jobs_dir / f"{job_id}.json"


class JobStore:
    """
    Folder-based job store.

    Each job is a single JSON file at: data/jobs/<job_id>.json
    """

    def __init__(self, base_dir: str = "data") -> None:
        self.paths = JobPaths(Path(base_dir))
        self.paths.ensure()

    def create_job(self, payload: Dict[str, Any]) -> str:
        job_id = str(uuid.uuid4())
        now = int(time.time())

        job = {
            "job_id": job_id,
            "status": "queued",  # queued|running|completed|failed|needs_feedback
            "created_at": now,
            "updated_at": now,
            "payload": payload,
            "result": None,
            "error": None,
        }

        self.paths.job_file(job_id).write_text(json.dumps(job, indent=2), encoding="utf-8")
        return job_id

    def get_job(self, job_id: str) -> Dict[str, Any]:
        fp = self.paths.job_file(job_id)
        if not fp.exists():
            raise JobNotFoundError(f"Job not found: {job_id}")
        return json.loads(fp.read_text(encoding="utf-8"))

    def update_job(
        self,
        job_id: str,
        *,
        status: Optional[str] = None,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
    ) -> Dict[str, Any]:
        job = self.get_job(job_id)
        now = int(time.time())

        if status is not None:
            job["status"] = status
        if result is not None:
            job["result"] = result
        if error is not None:
            job["error"] = error

        job["updated_at"] = now
        self.paths.job_file(job_id).write_text(json.dumps(job, indent=2), encoding="utf-8")
        return job
