from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .prompts import (
    build_schema_generation_prompt,
    build_schema_repair_prompt,
    load_all_schema_json_text,
    load_schema_guide,
)
from .validators import parse_json_strict, validate_min_schema_shape


@dataclass
class LLMConfig:
    # keep generic: your friend can wire providers later
    model_name: str = "gpt-4.1-mini"
    temperature: float = 0.0


class LLMNotConfiguredError(RuntimeError):
    pass


def _require_langchain() -> None:
    """
    Import-check only when needed, so the package can run parsing without LLM deps.
    """
    try:
        import langchain  # noqa: F401
    except Exception as e:
        raise LLMNotConfiguredError(
            "LangChain is not installed/configured. Add langchain + provider packages to Poetry."
        ) from e


def _call_llm(prompt: str, config: LLMConfig) -> str:
    """
    Minimal placeholder.
    Replace with LangChain chat model call when you integrate keys/providers.
    """
    _require_langchain()
    # Intentionally not implementing provider-specific code here to avoid runtime
    # failures without credentials. Wire this later (OpenAI/Azure/Anthropic/etc.).
    raise LLMNotConfiguredError(
        "LLM provider not wired yet. Implement _call_llm() using your chosen LangChain chat model."
    )


def generate_schema_from_pdf_text(
    *,
    pdf_filename: str,
    combined_pdf_text: str,
    schemas_dir: str = "schemas",
    schema_guide_path: str = "schemas/SCHEMA_GUIDE.md",
    platform_hint: Optional[str] = None,
    llm_config: Optional[LLMConfig] = None,
) -> dict:
    llm_config = llm_config or LLMConfig()

    guide_text = load_schema_guide(schema_guide_path)
    existing_schemas = load_all_schema_json_text(schemas_dir)

    prompt = build_schema_generation_prompt(
        pdf_filename=pdf_filename,
        combined_pdf_text=combined_pdf_text,
        schema_guide_text=guide_text,
        existing_schema_json_texts=existing_schemas,
        platform_hint=platform_hint,
    )

    raw = _call_llm(prompt, llm_config)
    schema = parse_json_strict(raw)

    ok, reason = validate_min_schema_shape(schema)
    if not ok:
        raise ValueError(f"Generated schema failed validation: {reason}")

    return schema


def repair_schema_from_feedback(
    *,
    pdf_filename: str,
    combined_pdf_text: str,
    platform_id: str,
    current_schema_text: str,
    user_feedback_reason: str,
    schemas_dir: str = "schemas",
    schema_guide_path: str = "schemas/SCHEMA_GUIDE.md",
    llm_config: Optional[LLMConfig] = None,
) -> dict:
    llm_config = llm_config or LLMConfig()

    guide_text = load_schema_guide(schema_guide_path)
    existing_schemas = load_all_schema_json_text(schemas_dir)

    prompt = build_schema_repair_prompt(
        pdf_filename=pdf_filename,
        combined_pdf_text=combined_pdf_text,
        schema_guide_text=guide_text,
        existing_schema_json_texts=existing_schemas,
        current_schema_text=current_schema_text,
        user_feedback_reason=user_feedback_reason,
        platform_id=platform_id,
    )

    raw = _call_llm(prompt, llm_config)
    schema = parse_json_strict(raw)

    # enforce platform id stays constant
    got_pid = (schema.get("platform_info", {}) or {}).get("platform_id")
    if got_pid != platform_id:
        raise ValueError("Repaired schema changed platform_info.platform_id; this is not allowed")

    ok, reason = validate_min_schema_shape(schema)
    if not ok:
        raise ValueError(f"Repaired schema failed validation: {reason}")

    return schema
