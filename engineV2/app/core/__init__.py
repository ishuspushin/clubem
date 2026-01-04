"""
Core Module - Configuration, PDF processing, and prompt management.
"""

from .config import Config
from .pdf_processor import PDFProcessor
from .prompts import PromptManager, PromptTemplate

__all__ = [
    'Config',
    'PDFProcessor',
    'PromptManager',
    'PromptTemplate'
]
