from __future__ import annotations

import json
from typing import Any, Dict, Tuple


REQUIRED_TOP_LEVEL_KEYS = ["platform_info", "detection", "extraction_rules", "output_mapping"]


def parse_json_strict(text: str) -> Dict[str, Any]:
    """
    Parse LLM output as JSON, raising ValueError with a clean message.
    """
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM output was not valid JSON: {e}") from e


def validate_min_schema_shape(schema: Dict[str, Any]) -> Tuple[bool, str]:
    for k in REQUIRED_TOP_LEVEL_KEYS:
        if k not in schema:
            return False, f"Missing required top-level key: {k}"

    platform_id = (schema.get("platform_info", {}) or {}).get("platform_id")
    if not platform_id or not isinstance(platform_id, str):
        return False, "platform_info.platform_id must be a non-empty string"

    patterns = (schema.get("detection", {}) or {}).get("patterns", [])
    if not isinstance(patterns, list) or not patterns:
        return False, "detection.patterns must be a non-empty list"

    return True, "ok"
