"""
Platform Classifier Node - Uses pattern matching and heuristics to detect platform.
Applies: Hash Maps (O(1) lookup), String matching algorithms
"""

import re
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class PlatformSignature:
    """Data structure to hold platform identification patterns."""
    name: str
    keywords: Set[str]
    patterns: List[re.Pattern]
    confidence_threshold: float


class ClassifierNode:
    """
    Classifier Node using OOP and Hash Map for O(1) platform lookup.
    
    Design Pattern: Strategy Pattern for different classification strategies
    DSA: Hash Map for keyword matching, Trie-like structure for pattern matching
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._platform_signatures = self._build_platform_signatures()
        self._keyword_map = self._build_keyword_hash_map()
        
    def _build_platform_signatures(self) -> Dict[str, PlatformSignature]:
        """
        Build platform signatures using hash map for O(1) access.
        
        Returns:
            Dict mapping platform names to their signatures
        """
        signatures = {
            'sharebite': PlatformSignature(
                name='Sharebite',
                keywords={'sharebite', 'yex', 'confirmation code'},
                patterns=[
                    re.compile(r'YEX\d+', re.IGNORECASE),
                    re.compile(r'care@sharebite\.com', re.IGNORECASE),
                    re.compile(r'\(800\)\s*527-9005', re.IGNORECASE)
                ],
                confidence_threshold=0.6
            ),
            'ezcater': PlatformSignature(
                name='EzCater',
                keywords={'ezcater', 'ezcater support'},
                patterns=[
                    re.compile(r'Order\s*#[A-Z0-9-]+', re.IGNORECASE),
                    re.compile(r'support@ezcater\.com', re.IGNORECASE),
                    re.compile(r'1-855-488-3746', re.IGNORECASE)
                ],
                confidence_threshold=0.6
            ),
            'grubhub': PlatformSignature(
                name='Grubhub',
                keywords={'grubhub', 'team delivery', 'relay.delivery'},
                patterns=[
                    re.compile(r'Confirmation\s+Code:\s*\d+', re.IGNORECASE),
                    re.compile(r'Order:\s*#\d+', re.IGNORECASE),
                    re.compile(r'relay\.delivery', re.IGNORECASE)
                ],
                confidence_threshold=0.6
            ),
            'catercow': PlatformSignature(
                name='CaterCow',
                keywords={'catercow', 'catercow order', 'catercow support'},
                patterns=[
                    re.compile(r'CaterCow\s+Order\s+\d+', re.IGNORECASE),
                    re.compile(r'support@catercow\.com', re.IGNORECASE),
                    re.compile(r'\(855\)\s*269-4056', re.IGNORECASE)
                ],
                confidence_threshold=0.3
            ),
            'clubfeast': PlatformSignature(
                name='ClubFeast',
                keywords={'clubfeast', 'club feast', 'hue', 'terra', 'eat better food'},
                patterns=[
                    re.compile(r'HUE[A-Z0-9-]+', re.IGNORECASE),
                    re.compile(r'Club\s*Feast', re.IGNORECASE),
                    re.compile(r'Terra\s*-\s*Eat\s*Better\s*Food', re.IGNORECASE)
                ],
                confidence_threshold=0.3
            ),
            'hungry': PlatformSignature(
                name='Hungry',
                keywords={'hungry', 'tryhungry', 'food partner order form'},
                patterns=[
                    re.compile(r'HUNGRY\s+will\s+reach\s+out', re.IGNORECASE),
                    re.compile(r'NYC\d+', re.IGNORECASE),
                    re.compile(r'angela@tryhungry\.com', re.IGNORECASE)
                ],
                confidence_threshold=0.3
            ),
            'forkable': PlatformSignature(
                name='Forkable',
                keywords={'forkable', 'forkable order'},
                patterns=[
                    re.compile(r'Forkable', re.IGNORECASE),
                    re.compile(r'support@forkable\.com', re.IGNORECASE)
                ],
                confidence_threshold=0.3
            )
        }
        return signatures
    
    def _build_keyword_hash_map(self) -> Dict[str, str]:
        """
        Build keyword hash map for O(1) platform lookup.
        
        Returns:
            Dict mapping keywords to platform names
        """
        keyword_map = {}
        for platform_key, signature in self._platform_signatures.items():
            for keyword in signature.keywords:
                keyword_map[keyword.lower()] = platform_key
        return keyword_map
    
    def _calculate_confidence_score(
        self, 
        text: str, 
        signature: PlatformSignature
    ) -> float:
        """
        Calculate confidence score using multiple heuristics.
        
        Algorithm: Weighted scoring based on keyword matches and pattern matches
        Time Complexity: O(n * m) where n = text length, m = patterns
        
        Args:
            text: Extracted PDF text
            signature: Platform signature to match
            
        Returns:
            Confidence score between 0 and 1
        """
        try:
            text_lower = text.lower()
            score = 0.0
            max_score = 0.0
            
            # Keyword matching (40% weight)
            keyword_weight = 0.4
            keyword_matches = sum(
                1 for keyword in signature.keywords 
                if keyword in text_lower
            )
            if signature.keywords:
                score += (keyword_matches / len(signature.keywords)) * keyword_weight
            max_score += keyword_weight
            
            # Pattern matching (60% weight)
            pattern_weight = 0.6
            pattern_matches = sum(
                1 for pattern in signature.patterns 
                if pattern.search(text)
            )
            if signature.patterns:
                score += (pattern_matches / len(signature.patterns)) * pattern_weight
            max_score += pattern_weight
            
            # Normalize score
            normalized_score = score / max_score if max_score > 0 else 0.0
            
            return normalized_score
            
        except Exception as e:
            self.logger.error(f"Error calculating confidence: {e}", exc_info=True)
            return 0.0
    
    def classify(self, pdf_text: str) -> Dict[str, any]:
        """
        Classify platform using multi-strategy approach.
        
        Strategy:
        1. Quick keyword lookup (O(1))
        2. Pattern matching (O(n*m))
        3. Confidence scoring
        
        Args:
            pdf_text: Extracted text from PDF
            
        Returns:
            Dict containing platform, confidence, and metadata
        """
        try:
            if not pdf_text or not isinstance(pdf_text, str):
                raise ValueError("Invalid PDF text provided")
            
            self.logger.info("Starting platform classification...")
            
            # Store all platform scores
            platform_scores = {}
            
            # Calculate scores for all platforms
            for platform_key, signature in self._platform_signatures.items():
                confidence = self._calculate_confidence_score(pdf_text, signature)
                platform_scores[platform_key] = {
                    'name': signature.name,
                    'confidence': confidence,
                    'threshold': signature.confidence_threshold
                }
            
            # Find best match using max heap concept (DSA)
            best_platform = max(
                platform_scores.items(),
                key=lambda x: x[1]['confidence']
            )
            
            platform_key, platform_data = best_platform
            
            # Check if confidence meets threshold
            if platform_data['confidence'] < platform_data['threshold']:
                self.logger.warning(
                    f"Low confidence: {platform_data['confidence']:.2f} "
                    f"< {platform_data['threshold']:.2f}"
                )
                return {
                    'success': False,
                    'platform': 'unknown',
                    'confidence': platform_data['confidence'],
                    'all_scores': platform_scores,
                    'error': 'Confidence below threshold'
                }
            
            self.logger.info(
                f"Classified as {platform_data['name']} "
                f"with {platform_data['confidence']:.2%} confidence"
            )
            
            return {
                'success': True,
                'platform': platform_key,
                'platform_name': platform_data['name'],
                'confidence': platform_data['confidence'],
                'all_scores': platform_scores
            }
            
        except ValueError as e:
            self.logger.error(f"Validation error: {e}")
            return {
                'success': False,
                'platform': 'unknown',
                'error': str(e)
            }
        except Exception as e:
            self.logger.error(f"Classification failed: {e}", exc_info=True)
            return {
                'success': False,
                'platform': 'unknown',
                'error': f"Classification error: {str(e)}"
            }
    
    def batch_classify(self, pdf_texts: List[str]) -> List[Dict[str, any]]:
        """
        Classify multiple PDFs efficiently.
        
        Time Complexity: O(n * m) where n = number of PDFs, m = classification time
        
        Args:
            pdf_texts: List of PDF texts
            
        Returns:
            List of classification results
        """
        try:
            results = []
            for idx, pdf_text in enumerate(pdf_texts):
                self.logger.info(f"Classifying PDF {idx + 1}/{len(pdf_texts)}")
                result = self.classify(pdf_text)
                result['pdf_index'] = idx
                results.append(result)
            return results
        except Exception as e:
            self.logger.error(f"Batch classification failed: {e}", exc_info=True)
            return []
