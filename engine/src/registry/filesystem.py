from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from domain.errors import SchemaInvalidError, SchemaNotFoundError
from .paths import RegistryPaths


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(text, encoding="utf-8")
    tmp_path.replace(path)


def _validate_schema_min(schema: Dict[str, Any]) -> None:
    if not isinstance(schema, dict):
        raise SchemaInvalidError("Schema must be a JSON object")
    if "platform_info" not in schema:
        raise SchemaInvalidError("Schema missing platform_info")
    pid = (schema.get("platform_info", {}) or {}).get("platform_id")
    if not pid or not isinstance(pid, str):
        raise SchemaInvalidError("schema.platform_info.platform_id must be a non-empty string")


class FileSchemaRegistry:
    """
    Folder-based schema registry.

    - active schema path:  <base>/active/<platform_id>.json
    - history path:        <base>/history/<platform_id>/<ts>.json
    """

    def __init__(self, base_dir: str = "schema_registry") -> None:
        self.paths = RegistryPaths(Path(base_dir))
        self.paths.ensure()

    def active_schema_path(self, platform_id: str) -> Path:
        return self.paths.active_dir / f"{platform_id}.json"

    def history_schema_path(self, platform_id: str, ts: Optional[int] = None) -> Path:
        ts = ts or int(time.time())
        return self.paths.history_dir / platform_id / f"{ts}.json"

    def exists(self, platform_id: str) -> bool:
        return self.active_schema_path(platform_id).exists()

    def get_schema_text(self, platform_id: str) -> str:
        path = self.active_schema_path(platform_id)
        if not path.exists():
            raise SchemaNotFoundError(f"No active schema for platform: {platform_id}")
        return path.read_text(encoding="utf-8")

    def get_schema_json(self, platform_id: str) -> Dict[str, Any]:
        raw = self.get_schema_text(platform_id)
        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            raise SchemaInvalidError(f"Active schema is not valid JSON: {platform_id}") from e

    def upsert_active_schema(
        self,
        schema: Dict[str, Any],
        *,
        create_history: bool = True,
    ) -> Tuple[str, Path]:
        """
        Save schema as active, optionally archiving previous active version.

        Returns:
            (platform_id, active_path)
        """
        _validate_schema_min(schema)

        platform_id = (schema.get("platform_info", {}) or {}).get("platform_id")
        assert isinstance(platform_id, str)

        active_path = self.active_schema_path(platform_id)

        if create_history and active_path.exists():
            old_text = active_path.read_text(encoding="utf-8")
            hist_path = self.history_schema_path(platform_id)
            _atomic_write_text(hist_path, old_text)

        text = json.dumps(schema, indent=2, ensure_ascii=False)
        _atomic_write_text(active_path, text)
        return platform_id, active_path

    def replace_active_schema_from_text(
        self,
        platform_id: str,
        new_schema_text: str,
        *,
        create_history: bool = True,
    ) -> Path:
        try:
            schema = json.loads(new_schema_text)
        except json.JSONDecodeError as e:
            raise SchemaInvalidError("New schema text is not valid JSON") from e

        schema_pid = (schema.get("platform_info", {}) or {}).get("platform_id")
        if schema_pid != platform_id:
            raise SchemaInvalidError("platform_id mismatch while replacing schema")

        _, active_path = self.upsert_active_schema(schema, create_history=create_history)
        return active_path
