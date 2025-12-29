from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List, Optional


class SchemaLoader:
    """Loads and manages platform schemas from a directory."""

    def __init__(self, schemas_dir: Optional[str] = None) -> None:
        """
        Args:
            schemas_dir: Directory containing JSON schema files.
                        If None, defaults to ./schemas at project root.
        """
        if schemas_dir is None:
            # Default: project root "schemas" folder (works for local dev + poetry run)
            schemas_dir = str(Path.cwd() / "schemas")

        self.schemas_dir = Path(schemas_dir)
        self.schemas: Dict[str, dict] = {}
        self._load_all_schemas()

    def _load_all_schemas(self) -> None:
        if not self.schemas_dir.exists():
            return

        for schema_file in self.schemas_dir.glob("*.json"):
            try:
                with open(schema_file, "r", encoding="utf-8") as f:
                    schema = json.load(f)

                platform_id = schema.get("platform_info", {}).get("platform_id", schema_file.stem)
                self.schemas[platform_id] = schema

            except (json.JSONDecodeError, KeyError):
                # Keep running even if one schema is malformed
                continue

    def get_schema(self, platform_id: str) -> Optional[dict]:
        return self.schemas.get(platform_id)

    def list_platforms(self) -> List[str]:
        return list(self.schemas.keys())

    def detect_platform_from_text(self, text: str) -> Optional[str]:
        """Detect platform from extracted PDF text using schemas' detection rules."""
        best_match = None
        best_score = 0

        for platform_id, schema in self.schemas.items():
            detection = schema.get("detection", {})
            patterns = detection.get("patterns", [])
            min_matches = detection.get("min_matches", 1)

            score = 0
            for pattern in patterns:
                flags = re.IGNORECASE if str(detection.get("flags", "")).lower() == "i" else 0
                if re.search(pattern, text, flags):
                    score += 1

            if score >= min_matches and score > best_score:
                best_score = score
                best_match = platform_id

        return best_match
