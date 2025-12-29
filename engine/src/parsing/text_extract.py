from __future__ import annotations

import re
from typing import List, Tuple

import pdfplumber


class TextExtractor:
    """Utilities for extracting text from PDFs."""

    @staticmethod
    def extract_all_text(pdf_path: str) -> Tuple[str, List[str]]:
        """
        Extract text from all pages.

        Returns:
            (combined_text, list_of_page_texts)
        """
        pages_text: List[str] = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                pages_text.append(text)

        combined = "\n".join(pages_text)
        return combined, pages_text

    @staticmethod
    def dedupe_bold_text(text: str) -> str:
        """Remove duplicate characters from bold text rendering."""
        if not text or len(text) < 2:
            return text

        result: List[str] = []
        i = 0
        while i < len(text):
            result.append(text[i])
            if i + 1 < len(text) and text[i] == text[i + 1] and text[i].isalpha():
                i += 2
            else:
                i += 1
        return "".join(result)

    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """Normalize whitespace in text."""
        return re.sub(r"\s+", " ", text).strip()
