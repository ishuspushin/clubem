from __future__ import annotations

import time
from typing import Any, Dict, Optional

from .jobs import JobStore
from .storage import FileStorage
from .orchestrator import Orchestrator


class JobWorker:
    def __init__(
        self,
        *,
        job_store: Optional[JobStore] = None,
        storage: Optional[FileStorage] = None,
        orchestrator: Optional[Orchestrator] = None,
    ) -> None:
        self.jobs = job_store or JobStore(base_dir="data")
        self.storage = storage or FileStorage(base_dir="data")
        self.orchestrator = orchestrator or Orchestrator()

    def run_once(self) -> int:
        # Very small/simple: scan all job json files and pick queued ones
        job_files = sorted(self.jobs.paths.jobs_dir.glob("*.json"))
        processed = 0

        for fp in job_files:
            job = self.jobs.get_job(fp.stem)
            if job.get("status") != "queued":
                continue

            job_id = job["job_id"]
            self.jobs.update_job(job_id, status="running")

            try:
                uploads = self.storage.list_job_uploads(job_id)
                out_dir = str(self.storage.output_dir(job_id))

                results = []
                for pdf in uploads:
                    results.append(self.orchestrator.parse_one_pdf(pdf_path=str(pdf), output_dir=out_dir))

                self.jobs.update_job(job_id, status="completed", result={"files": results})
            except Exception as e:
                self.jobs.update_job(job_id, status="failed", error=str(e))

            processed += 1

        return processed

    def run_forever(self, poll_seconds: float = 1.0) -> None:
        while True:
            self.run_once()
            time.sleep(poll_seconds)
