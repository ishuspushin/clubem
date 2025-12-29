from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def load_schema_guide(schema_guide_path: str) -> str:
    p = Path(schema_guide_path)
    return p.read_text(encoding="utf-8") if p.exists() else ""


def load_all_schema_json_text(schemas_dir: str) -> List[Tuple[str, str]]:
    """
    Returns list of (filename, json_text).
    Keeps raw JSON text for best LLM grounding.
    """
    base = Path(schemas_dir)
    if not base.exists():
        return []

    items: List[Tuple[str, str]] = []
    for fp in sorted(base.glob("*.json")):
        try:
            raw = fp.read_text(encoding="utf-8")
            # Validate JSON so we don't feed broken examples
            json.loads(raw)
            items.append((fp.name, raw))
        except Exception:
            continue
    return items


def build_schema_generation_prompt(
    *,
    pdf_filename: str,
    combined_pdf_text: str,
    schema_guide_text: str,
    existing_schema_json_texts: List[Tuple[str, str]],
    platform_hint: Optional[str] = None,
) -> str:
    schema_examples_block = "\n\n".join(
        [f"--- FILE: {name} ---\n{txt}" for name, txt in existing_schema_json_texts]
    )

    return (
        "You are an expert information extraction engineer.\n"
        "Goal: Create a NEW platform JSON schema for a group order PDF parser.\n\n"
        "STRICT OUTPUT RULES:\n"
        "1) Output ONLY valid JSON (no markdown, no comments).\n"
        "2) The JSON must follow the schema style described in SCHEMA_GUIDE.\n"
        "3) Include: platform_info, detection, extraction_rules, output_mapping.\n"
        "4) detection.patterns should be robust and platform-specific.\n"
        "5) Prefer regex patterns that work on extracted text (not visual layout).\n\n"
        f"Platform hint (may be unknown): {platform_hint or 'unknown'}\n"
        f"PDF filename: {pdf_filename}\n\n"
        "===== SCHEMA GUIDE (REFERENCE) =====\n"
        f"{schema_guide_text}\n\n"
        "===== EXISTING SCHEMAS (REFERENCE) =====\n"
        f"{schema_examples_block}\n\n"
        "===== PDF TEXT (INPUT) =====\n"
        f"{combined_pdf_text}\n"
    )


def build_schema_repair_prompt(
    *,
    pdf_filename: str,
    combined_pdf_text: str,
    schema_guide_text: str,
    existing_schema_json_texts: List[Tuple[str, str]],
    current_schema_text: str,
    user_feedback_reason: str,
    platform_id: str,
) -> str:
    schema_examples_block = "\n\n".join(
        [f"--- FILE: {name} ---\n{txt}" for name, txt in existing_schema_json_texts]
    )

    return (
        "You are an expert information extraction engineer.\n"
        "Goal: FIX the CURRENT platform JSON schema so parsing improves.\n\n"
        "STRICT OUTPUT RULES:\n"
        "1) Output ONLY valid JSON (no markdown, no comments).\n"
        "2) Keep platform_info.platform_id EXACTLY as provided.\n"
        "3) Apply the user's feedback reason to adjust detection/extraction/output_mapping.\n"
        "4) Do not remove important fields; improve patterns and rules.\n\n"
        f"Platform id: {platform_id}\n"
        f"PDF filename: {pdf_filename}\n"
        f"User feedback reason: {user_feedback_reason}\n\n"
        "===== SCHEMA GUIDE (REFERENCE) =====\n"
        f"{schema_guide_text}\n\n"
        "===== EXISTING SCHEMAS (REFERENCE) =====\n"
        f"{schema_examples_block}\n\n"
        "===== CURRENT SCHEMA (TO FIX) =====\n"
        f"{current_schema_text}\n\n"
        "===== PDF TEXT (INPUT) =====\n"
        f"{combined_pdf_text}\n"
    )
