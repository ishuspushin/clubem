from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from domain.errors import SchemaInvalidError, SchemaNotFoundError
from .filesystem import FileSchemaRegistry


class SchemaRepository:
    def __init__(
        self,
        *,
        registry_dir: str = "schema_registry",
        shipped_schemas_dir: str = "schemas",
    ) -> None:
        self.registry = FileSchemaRegistry(registry_dir)
        self.shipped_schemas_dir = Path(shipped_schemas_dir)

    def get_schema(self, platform_id: str) -> Dict[str, Any]:
        # 1) Prefer active registry schema
        if self.registry.exists(platform_id):
            return self.registry.get_schema_json(platform_id)

        # 2) Fallback to shipped schema file
        shipped_path = self.shipped_schemas_dir / f"{platform_id}.json"
        if not shipped_path.exists():
            raise SchemaNotFoundError(f"No schema found for platform: {platform_id}")

        try:
            return json.loads(shipped_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise SchemaInvalidError(f"Shipped schema is not valid JSON: {platform_id}") from e

    def upsert_schema(self, schema: Dict[str, Any]) -> str:
        platform_id, _ = self.registry.upsert_active_schema(schema, create_history=True)
        return platform_id
