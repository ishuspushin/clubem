from __future__ import annotations

import shutil
from pathlib import Path
from typing import Iterable, List, Tuple


class FileStorage:
    """
    Simple file storage under data/uploads and data/outputs.
    """

    def __init__(self, base_dir: str = "data") -> None:
        self.base_dir = Path(base_dir)
        self.uploads_dir = self.base_dir / "uploads"
        self.outputs_dir = self.base_dir / "outputs"
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.outputs_dir.mkdir(parents=True, exist_ok=True)

    def save_upload(self, job_id: str, filename: str, src_path: Path) -> Path:
        job_dir = self.uploads_dir / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        dest = job_dir / filename
        shutil.copyfile(src_path, dest)
        return dest

    def save_upload_bytes(self, job_id: str, filename: str, data: bytes) -> Path:
        job_dir = self.uploads_dir / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        dest = job_dir / filename
        dest.write_bytes(data)
        return dest

    def output_dir(self, job_id: str) -> Path:
        d = self.outputs_dir / job_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    def list_job_uploads(self, job_id: str) -> List[Path]:
        job_dir = self.uploads_dir / job_id
        if not job_dir.exists():
            return []
        return sorted([p for p in job_dir.iterdir() if p.is_file()])

    def delete_job_files(self, job_id: str) -> None:
        """
        Deletes all uploads and outputs associated with a job.
        """
        upload_dir = self.uploads_dir / job_id
        if upload_dir.exists():
            shutil.rmtree(upload_dir)
        
        output_dir = self.outputs_dir / job_id
        if output_dir.exists():
            shutil.rmtree(output_dir)
