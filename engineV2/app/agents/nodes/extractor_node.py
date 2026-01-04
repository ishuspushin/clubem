"""
Extractor Node - Uses Gemini Flash 2.5 for intelligent PDF extraction.
Applies: Factory Pattern, Retry Logic with Exponential Backoff
"""

import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import logging
import google.generativeai as genai
import openai
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

logger = logging.getLogger(__name__)


class ExtractionStatus(Enum):
    """Enum for extraction status tracking."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    RETRY = "retry"


@dataclass
class ExtractionResult:
    """Data structure to hold extraction results."""
    status: ExtractionStatus
    platform: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    confidence: float = 0.0
    extraction_time: float = 0.0
    retry_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


from ...core.prompts import PromptManager

class PromptBuilder:
    """
    Builder Pattern for constructing platform-specific prompts.
    Delegates to central PromptManager.
    
    Design Pattern: Builder Pattern
    """
    
    def __init__(self):
        self.prompt_manager = PromptManager()
    
    def build_prompt(self, platform: str, pdf_text: str) -> str:
        """
        Build platform-specific prompt.
        
        Args:
            platform: Platform identifier
            pdf_text: Extracted PDF text
            
        Returns:
            Formatted prompt string
        """
        return self.prompt_manager.get_extraction_prompt(platform, pdf_text)


class GeminiExtractor:
    """
    Gemini API wrapper with retry logic and error handling.
    
    Design Pattern: Singleton-like behavior, Strategy Pattern
    DSA: Exponential Backoff Algorithm
    """
    
    def __init__(self, api_key: str, model_name: str = "gemini-2.0-flash"):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._api_key = api_key
        self._model_name = model_name
        self._model = None
        self._initialize_model()
    
    def _initialize_model(self) -> None:
        """Initialize Gemini model with error handling."""
        try:
            genai.configure(api_key=self._api_key)
            
            self._model = genai.GenerativeModel(
                model_name=self._model_name,
                generation_config={
                    'temperature': 0.1,  # Low temperature for consistent extraction
                    'top_p': 0.95,
                    'top_k': 40,
                    'max_output_tokens': 8192,
                    'response_mime_type': 'application/json',
                }
            )
            
            self.logger.info(f"Initialized Gemini model: {self._model_name}")
            
        except Exception as e:
            self.logger.error(f"Model initialization failed: {e}", exc_info=True)
            raise
    
    @retry(
        stop=stop_after_attempt(10),
        wait=wait_exponential(multiplier=2, min=4, max=60),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    def extract(self, prompt: str) -> str:
        """
        Extract data using Gemini with retry logic.
        
        Retry Strategy: Exponential backoff (2s, 4s, 8s)
        
        Args:
            prompt: Formatted extraction prompt
            
        Returns:
            Raw model response text
        """
        try:
            if not self._model:
                raise RuntimeError("Model not initialized")
            
            self.logger.info("Sending request to Gemini...")
            
            response = self._model.generate_content(prompt)
            
            if not response or not response.text:
                raise ValueError("Empty response from Gemini")
            
            self.logger.info("Successfully received response from Gemini")
            return response.text
            
        except Exception as e:
            self.logger.error(f"Extraction failed: {e}", exc_info=True)
            raise


class OpenAIExtractor:
    """
    OpenAI API wrapper with retry logic and error handling.
    """
    
    def __init__(self, api_key: str, model_name: str = "gpt-4o"):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._api_key = api_key
        self._model_name = model_name
        self._client = None
        self._initialize_model()
    
    def _initialize_model(self) -> None:
        """Initialize OpenAI client."""
        try:
            self._client = openai.OpenAI(api_key=self._api_key)
            self.logger.info(f"Initialized OpenAI model: {self._model_name}")
        except Exception as e:
            self.logger.error(f"OpenAI client initialization failed: {e}", exc_info=True)
            raise
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=2, max=30),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    def extract(self, prompt: str) -> str:
        """Extract data using OpenAI with retry logic."""
        try:
            if not self._client:
                raise RuntimeError("OpenAI client not initialized")
            
            self.logger.info("Sending request to OpenAI...")
            
            response = self._client.chat.completions.create(
                model=self._model_name,
                messages=[
                    {"role": "system", "content": "You are an expert PDF data extractor. You always return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from OpenAI")
            
            self.logger.info("Successfully received response from OpenAI")
            return content
            
        except Exception as e:
            self.logger.error(f"OpenAI extraction failed: {e}", exc_info=True)
            raise


class ExtractorNode:
    """
    Main Extractor Node orchestrating the extraction process.
    
    Design Pattern: Facade Pattern (hides complexity of extraction)
    OOP: Composition (uses PromptBuilder and GeminiExtractor)
    """
    
    def __init__(self, config):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.prompt_builder = PromptBuilder()
        
        provider = config.app.LLM_PROVIDER
        if provider == "gemini":
            self.extractor = GeminiExtractor(
                api_key=config.google_ai.GOOGLE_API_KEY,
                model_name=config.google_ai.MODEL_NAME
            )
        elif provider == "openai":
            self.extractor = OpenAIExtractor(
                api_key=config.openai.OPENAI_API_KEY,
                model_name=config.openai.MODEL_NAME
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")
            
        self._extraction_history = []  # Stack to track history (DSA)
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse Gemini response with robust error handling.
        
        Args:
            response_text: Raw response from Gemini
            
        Returns:
            Parsed JSON dictionary
        """
        try:
            import json
            import re
            
            # Remove markdown code blocks if present
            cleaned_text = re.sub(r'```json\s*|\s*```', '', response_text)
            cleaned_text = cleaned_text.strip()
            
            # Parse JSON
            parsed_data = json.loads(cleaned_text)
            
            return parsed_data
            
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON parsing failed: {e}")
            raise ValueError(f"Invalid JSON response: {str(e)}")
        except Exception as e:
            self.logger.error(f"Response parsing failed: {e}", exc_info=True)
            raise
    
    def extract(
        self,
        pdf_text: str,
        platform: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ExtractionResult:
        """
        Main extraction method with comprehensive error handling.
        
        Args:
            pdf_text: Extracted PDF text
            platform: Platform identifier
            metadata: Additional metadata
            
        Returns:
            ExtractionResult object
        """
        start_time = time.time()
        retry_count = 0
        
        try:
            if not pdf_text or not isinstance(pdf_text, str):
                raise ValueError("Invalid PDF text provided")
            
            if not platform:
                raise ValueError("Platform not specified")
            
            self.logger.info(f"Starting extraction for platform: {platform}")
            
            # Build prompt
            prompt = self.prompt_builder.build_prompt(platform, pdf_text)
            
            # Extract with retry
            response_text = self.extractor.extract(prompt)

            # Log raw response length and snippet for debugging
            self.logger.info(f"Raw response length: {len(response_text)}")
            self.logger.info(f"Raw response start: {response_text[:200]}")
            self.logger.info(f"Raw response end: {response_text[-200:]}")
            
            # Parse response
            extracted_data = self._parse_response(response_text)
            
            # Calculate extraction time
            extraction_time = time.time() - start_time
            
            # Create result
            result = ExtractionResult(
                status=ExtractionStatus.SUCCESS,
                platform=platform,
                data=extracted_data,
                confidence=0.95,  # High confidence for successful extraction
                extraction_time=extraction_time,
                retry_count=retry_count,
                metadata=metadata or {}
            )
            
            # Add to history (Stack - DSA)
            self._extraction_history.append(result)
            
            self.logger.info(
                f"Extraction successful in {extraction_time:.2f}s"
            )
            
            return result
            
        except ValueError as e:
            self.logger.error(f"Validation error: {e}")
            return ExtractionResult(
                status=ExtractionStatus.FAILED,
                platform=platform,
                error=str(e),
                extraction_time=time.time() - start_time
            )
        except Exception as e:
            self.logger.error(f"Extraction failed: {e}", exc_info=True)
            return ExtractionResult(
                status=ExtractionStatus.FAILED,
                platform=platform,
                error=f"Extraction error: {str(e)}",
                extraction_time=time.time() - start_time
            )
    
    def batch_extract(
        self,
        pdf_texts: List[str],
        platforms: List[str]
    ) -> List[ExtractionResult]:
        """
        Batch extraction with error isolation.
        
        Args:
            pdf_texts: List of PDF texts
            platforms: List of platform identifiers
            
        Returns:
            List of ExtractionResult objects
        """
        try:
            if len(pdf_texts) != len(platforms):
                raise ValueError("Mismatch between PDFs and platforms count")
            
            results = []
            for idx, (pdf_text, platform) in enumerate(zip(pdf_texts, platforms)):
                if idx > 0:
                    self.logger.info("Waiting 10s between extractions to respect rate limits...")
                    time.sleep(10)
                
                self.logger.info(f"Extracting PDF {idx + 1}/{len(pdf_texts)}")
                result = self.extract(pdf_text, platform)
                results.append(result)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Batch extraction failed: {e}", exc_info=True)
            return []
    
    def get_extraction_history(self) -> List[ExtractionResult]:
        """Get extraction history (Stack operation)."""
        return self._extraction_history.copy()
