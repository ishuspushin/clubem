
from __future__ import annotations

from typing import List, Optional

from .schema_loader import SchemaLoader
from .text_extract import TextExtractor


def detect_platform(pdf_path: str, *, schemas_dir: str = "schemas") -> Optional[str]:
    loader = SchemaLoader(schemas_dir=schemas_dir)
    combined_text, _pages_text = TextExtractor.extract_all_text(pdf_path)
    return loader.detect_platform_from_text(combined_text)


def list_platforms(*, schemas_dir: str = "schemas") -> List[str]:
    loader = SchemaLoader(schemas_dir=schemas_dir)
    return loader.list_platforms()
