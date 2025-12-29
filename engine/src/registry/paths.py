from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RegistryPaths:
    base_dir: Path

    @property
    def active_dir(self) -> Path:
        return self.base_dir / "active"

    @property
    def history_dir(self) -> Path:
        return self.base_dir / "history"

    def ensure(self) -> None:
        self.active_dir.mkdir(parents=True, exist_ok=True)
        self.history_dir.mkdir(parents=True, exist_ok=True)
