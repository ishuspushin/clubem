from __future__ import annotations

from typing import Any, Dict, Optional

from domain.errors import PlatformDetectionError, SchemaNotFoundError
from export import export_to_json
from parsing.parser import UniversalParser
from parsing.platform_detect import detect_platform
from parsing.text_extract import TextExtractor
from registry.repo import SchemaRepository


class Orchestrator:
    """
    Main pipeline:
    - detect platform from PDF
    - load schema (registry active first, fallback shipped schemas/)
    - parse -> ParsedOrder
    - persist JSON output to data/outputs/<job_id>/
    """

    def __init__(
        self,
        *,
        shipped_schemas_dir: str = "schemas",
        registry_dir: str = "schema_registry",
    ) -> None:
        self.shipped_schemas_dir = shipped_schemas_dir
        self.repo = SchemaRepository(registry_dir=registry_dir, shipped_schemas_dir=shipped_schemas_dir)

    def parse_one_pdf(
        self,
        *,
        pdf_path: str,
        output_dir: str,
        forced_platform: Optional[str] = None,
    ) -> Dict[str, Any]:
        platform_id = forced_platform
        if not platform_id:
            platform_id = detect_platform(pdf_path, schemas_dir=self.shipped_schemas_dir)
        if not platform_id:
            raise PlatformDetectionError(f"Could not detect platform for: {pdf_path}")

        schema = self.repo.get_schema(platform_id)
        if not schema:
            raise SchemaNotFoundError(f"No schema found for platform: {platform_id}")

        parser = UniversalParser(schema)
        parsed = parser.parse(pdf_path)

        json_path = export_to_json(parsed, output_dir)
        return {
            "pdf_path": pdf_path,
            "platform_id": platform_id,
            "output_json_path": json_path,
            "output": parsed.to_dict(),
        }

    def extract_pdf_text_for_llm(self, pdf_path: str) -> Dict[str, Any]:
        combined, pages = TextExtractor.extract_all_text(pdf_path)
        return {"combined_text": combined, "pages_text": pages}
