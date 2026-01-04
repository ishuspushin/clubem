"""
PDF Processing utilities with multiple extraction strategies.
Applies: Strategy Pattern, Error handling, Multi-library support
"""

import os
from typing import Optional, List, Dict, Any, Union
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)

# PDF processing libraries
try:
    import pypdf
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False
    logger.warning("pypdf not available")

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    logger.info("PyMuPDF not available, using pypdf instead (this is fine)")


try:
    from pdf2image import convert_from_path
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False


class ExtractionMethod(Enum):
    """PDF text extraction methods."""
    PYPDF = "pypdf"
    PYMUPDF = "pymupdf"
    OCR = "ocr"
    AUTO = "auto"


@dataclass
class ExtractionResult:
    """Result from PDF extraction."""
    success: bool
    text: str
    method: ExtractionMethod
    page_count: int = 0
    file_size: int = 0
    error: Optional[str] = None
    metadata: Dict[str, Any] = None


class PDFExtractionStrategy:
    """
    Base strategy for PDF text extraction.
    
    Design Pattern: Strategy Pattern
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def extract(self, pdf_path: Path) -> ExtractionResult:
        """
        Extract text from PDF.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            ExtractionResult
        """
        raise NotImplementedError
    
    def is_available(self) -> bool:
        """Check if this strategy is available."""
        raise NotImplementedError


class PyPDFStrategy(PDFExtractionStrategy):
    """PyPDF-based extraction strategy."""
    
    def is_available(self) -> bool:
        return PYPDF_AVAILABLE
    
    def extract(self, pdf_path: Path) -> ExtractionResult:
        """Extract text using PyPDF."""
        try:
            if not self.is_available():
                raise ImportError("PyPDF library not available")
            
            self.logger.info(f"Extracting with PyPDF: {pdf_path.name}")
            
            with open(pdf_path, 'rb') as file:
                reader = pypdf.PdfReader(file)
                page_count = len(reader.pages)
                
                # Extract text from all pages
                text_parts = []
                for page_num, page in enumerate(reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(page_text)
                    except Exception as e:
                        self.logger.warning(f"Page {page_num} extraction failed: {e}")
                
                full_text = "\n\n".join(text_parts)
                
                # Get metadata
                metadata = {}
                if reader.metadata:
                    metadata = {
                        key: str(value) for key, value in reader.metadata.items()
                    }
                
                return ExtractionResult(
                    success=True,
                    text=full_text,
                    method=ExtractionMethod.PYPDF,
                    page_count=page_count,
                    file_size=pdf_path.stat().st_size,
                    metadata=metadata
                )
                
        except Exception as e:
            self.logger.error(f"PyPDF extraction failed: {e}", exc_info=True)
            return ExtractionResult(
                success=False,
                text="",
                method=ExtractionMethod.PYPDF,
                error=str(e)
            )


class PyMuPDFStrategy(PDFExtractionStrategy):
    """PyMuPDF (fitz) based extraction strategy."""
    
    def is_available(self) -> bool:
        return PYMUPDF_AVAILABLE
    
    def extract(self, pdf_path: Path) -> ExtractionResult:
        """Extract text using PyMuPDF."""
        try:
            if not self.is_available():
                raise ImportError("PyMuPDF library not available")
            
            self.logger.info(f"Extracting with PyMuPDF: {pdf_path.name}")
            
            doc = fitz.open(pdf_path)
            page_count = len(doc)
            
            # Extract text from all pages
            text_parts = []
            for page_num in range(page_count):
                try:
                    page = doc[page_num]
                    page_text = page.get_text()
                    if page_text:
                        text_parts.append(page_text)
                except Exception as e:
                    self.logger.warning(f"Page {page_num} extraction failed: {e}")
            
            full_text = "\n\n".join(text_parts)
            
            # Get metadata
            metadata = doc.metadata if doc.metadata else {}
            
            doc.close()
            
            return ExtractionResult(
                success=True,
                text=full_text,
                method=ExtractionMethod.PYMUPDF,
                page_count=page_count,
                file_size=pdf_path.stat().st_size,
                metadata=metadata
            )
            
        except Exception as e:
            self.logger.error(f"PyMuPDF extraction failed: {e}", exc_info=True)
            return ExtractionResult(
                success=False,
                text="",
                method=ExtractionMethod.PYMUPDF,
                error=str(e)
            )


class OCRStrategy(PDFExtractionStrategy):
    """OCR-based extraction strategy for scanned PDFs."""
    
    def is_available(self) -> bool:
        return OCR_AVAILABLE
    
    def extract(self, pdf_path: Path) -> ExtractionResult:
        """Extract text using OCR."""
        try:
            if not self.is_available():
                raise ImportError("OCR libraries not available")
            
            self.logger.info(f"Extracting with OCR: {pdf_path.name}")
            
            # Convert PDF to images
            images = convert_from_path(pdf_path)
            page_count = len(images)
            
            # Extract text from each image
            text_parts = []
            for page_num, image in enumerate(images):
                try:
                    page_text = pytesseract.image_to_string(image)
                    if page_text:
                        text_parts.append(page_text)
                except Exception as e:
                    self.logger.warning(f"OCR page {page_num} failed: {e}")
            
            full_text = "\n\n".join(text_parts)
            
            return ExtractionResult(
                success=True,
                text=full_text,
                method=ExtractionMethod.OCR,
                page_count=page_count,
                file_size=pdf_path.stat().st_size
            )
            
        except Exception as e:
            self.logger.error(f"OCR extraction failed: {e}", exc_info=True)
            return ExtractionResult(
                success=False,
                text="",
                method=ExtractionMethod.OCR,
                error=str(e)
            )


class PDFProcessor:
    """
    Main PDF processor with fallback strategies.
    
    Design Pattern: Strategy Pattern, Chain of Responsibility
    OOP: Composition, Polymorphism
    """
    
    def __init__(self, preferred_method: ExtractionMethod = ExtractionMethod.AUTO):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.preferred_method = preferred_method
        
        # Initialize strategies (hash map for O(1) lookup)
        self._strategies: Dict[ExtractionMethod, PDFExtractionStrategy] = {
            ExtractionMethod.PYPDF: PyPDFStrategy(),
            ExtractionMethod.PYMUPDF: PyMuPDFStrategy(),
            ExtractionMethod.OCR: OCRStrategy()
        }
        
        # Determine strategy order
        self._strategy_order = self._determine_strategy_order()
        
        self.logger.info(
            f"PDFProcessor initialized with strategy order: "
            f"{[s.value for s in self._strategy_order]}"
        )
    
    def _determine_strategy_order(self) -> List[ExtractionMethod]:
        """
        Determine extraction strategy order based on availability.
        
        Returns:
            List of extraction methods in priority order
        """
        if self.preferred_method != ExtractionMethod.AUTO:
            # Use only preferred method
            return [self.preferred_method]
        
        # Auto mode: try fastest to slowest
        order = []
        
        # 1. Try PyMuPDF first (fastest and most reliable)
        if self._strategies[ExtractionMethod.PYMUPDF].is_available():
            order.append(ExtractionMethod.PYMUPDF)
        
        # 2. Try PyPDF as fallback
        if self._strategies[ExtractionMethod.PYPDF].is_available():
            order.append(ExtractionMethod.PYPDF)
        
        # 3. Try OCR as last resort (slowest)
        if self._strategies[ExtractionMethod.OCR].is_available():
            order.append(ExtractionMethod.OCR)
        
        if not order:
            raise RuntimeError("No PDF extraction libraries available!")
        
        return order
    
    def extract_text(
        self,
        pdf_path: Union[str, Path],
        fallback: bool = True
    ) -> str:
        """
        Extract text from PDF with automatic fallback.
        
        Args:
            pdf_path: Path to PDF file
            fallback: Enable fallback to other methods
            
        Returns:
            Extracted text
        """
        try:
            pdf_path = Path(pdf_path)
            
            if not pdf_path.exists():
                raise FileNotFoundError(f"PDF file not found: {pdf_path}")
            
            if not pdf_path.suffix.lower() == '.pdf':
                raise ValueError(f"File is not a PDF: {pdf_path}")
            
            self.logger.info(f"Extracting text from: {pdf_path.name}")
            
            # Try strategies in order
            for method in self._strategy_order:
                strategy = self._strategies[method]
                
                if not strategy.is_available():
                    continue
                
                result = strategy.extract(pdf_path)
                
                if result.success and result.text.strip():
                    self.logger.info(
                        f"Successfully extracted {len(result.text)} chars "
                        f"using {method.value}"
                    )
                    return result.text
                
                if not fallback:
                    # Don't try other methods
                    break
            
            # All strategies failed
            raise RuntimeError("All extraction strategies failed")
            
        except FileNotFoundError as e:
            self.logger.error(f"File not found: {e}")
            raise
        except ValueError as e:
            self.logger.error(f"Invalid file: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Extraction failed: {e}", exc_info=True)
            raise
    
    def extract_with_details(
        self,
        pdf_path: Union[str, Path]
    ) -> ExtractionResult:
        """
        Extract text with detailed result information.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            ExtractionResult with details
        """
        try:
            pdf_path = Path(pdf_path)
            
            # Try strategies in order
            for method in self._strategy_order:
                strategy = self._strategies[method]
                
                if not strategy.is_available():
                    continue
                
                result = strategy.extract(pdf_path)
                
                if result.success and result.text.strip():
                    return result
            
            # All strategies failed
            return ExtractionResult(
                success=False,
                text="",
                method=ExtractionMethod.AUTO,
                error="All extraction strategies failed"
            )
            
        except Exception as e:
            return ExtractionResult(
                success=False,
                text="",
                method=ExtractionMethod.AUTO,
                error=str(e)
            )
    
    def batch_extract(
        self,
        pdf_paths: List[Union[str, Path]]
    ) -> List[str]:
        """
        Extract text from multiple PDFs.
        
        Args:
            pdf_paths: List of PDF file paths
            
        Returns:
            List of extracted texts
        """
        try:
            texts = []
            
            for i, pdf_path in enumerate(pdf_paths):
                self.logger.info(f"Processing PDF {i+1}/{len(pdf_paths)}")
                try:
                    text = self.extract_text(pdf_path)
                    texts.append(text)
                except Exception as e:
                    self.logger.error(f"Failed to extract {pdf_path}: {e}")
                    texts.append("")  # Empty text for failed extraction
            
            return texts
            
        except Exception as e:
            self.logger.error(f"Batch extraction failed: {e}", exc_info=True)
            return []
    
    def validate_pdf(self, pdf_path: Union[str, Path]) -> tuple[bool, Optional[str]]:
        """
        Validate if file is a valid PDF.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            pdf_path = Path(pdf_path)
            
            # Check file exists
            if not pdf_path.exists():
                return False, "File does not exist"
            
            # Check file extension
            if pdf_path.suffix.lower() != '.pdf':
                return False, "File is not a PDF"
            
            # Check file size (not empty, not too large)
            file_size = pdf_path.stat().st_size
            if file_size == 0:
                return False, "PDF file is empty"
            
            if file_size > 50 * 1024 * 1024:  # 50 MB
                return False, "PDF file too large (>50MB)"
            
            # Try to open with PyMuPDF
            if PYMUPDF_AVAILABLE:
                try:
                    doc = fitz.open(pdf_path)
                    page_count = len(doc)
                    doc.close()
                    
                    if page_count == 0:
                        return False, "PDF has no pages"
                    
                except Exception as e:
                    return False, f"PDF is corrupted: {str(e)}"
            
            return True, None
            
        except Exception as e:
            return False, str(e)
    
    def get_pdf_info(self, pdf_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Get PDF metadata and information.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary with PDF info
        """
        try:
            pdf_path = Path(pdf_path)
            
            info = {
                'filename': pdf_path.name,
                'file_size': pdf_path.stat().st_size,
                'page_count': 0,
                'metadata': {}
            }
            
            if PYMUPDF_AVAILABLE:
                try:
                    doc = fitz.open(pdf_path)
                    info['page_count'] = len(doc)
                    info['metadata'] = doc.metadata if doc.metadata else {}
                    doc.close()
                except Exception as e:
                    self.logger.warning(f"Failed to get PDF info: {e}")
            
            return info
            
        except Exception as e:
            self.logger.error(f"Failed to get PDF info: {e}")
            return {}
