"""
Extraction logic tests.
"""

import pytest
from pathlib import Path


class TestClassifierNode:
    """Test classifier node."""
    
    @pytest.fixture
    def classifier(self):
        """Create classifier instance."""
        from app.agents.nodes import ClassifierNode
        return ClassifierNode()
    
    def test_classifier_initialization(self, classifier):
        """Test classifier initializes."""
        assert classifier is not None
        assert len(classifier._platform_signatures) > 0
    
    def test_classify_sharebite(self, classifier):
        """Test Sharebite classification."""
        sample_text = """
        Yext - Friday Lunch (NYC)
        Scheduled for PICKUP AT: 11:30AM Nov 07, 2025
        YEX1644669319
        care@sharebite.com
        """
        
        result = classifier.classify(sample_text)
        assert result['success'] is True
        assert result['platform'] == 'sharebite'
    
    def test_classify_ezcater(self, classifier):
        """Test EzCater classification."""
        sample_text = """
        ezCater
        Order #1C5-3VR
        support@ezcater.com
        1-855-488-3746
        """
        
        result = classifier.classify(sample_text)
        assert result['success'] is True
        assert result['platform'] == 'ezcater'
    
    def test_classify_unknown(self, classifier):
        """Test unknown platform."""
        sample_text = "Random text with no platform indicators"
        
        result = classifier.classify(sample_text)
        # Should still return a result, even if low confidence
        assert 'platform' in result


class TestValidatorNode:
    """Test validator node."""
    
    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        from app.agents.nodes import ValidatorNode
        return ValidatorNode()
    
    def test_validator_initialization(self, validator):
        """Test validator initializes."""
        assert validator is not None
    
    def test_validate_valid_data(self, validator):
        """Test validation of valid data."""
        valid_data = {
            'order_level': {
                'business_client': 'Group Sharebite',
                'client_name': 'Test Company',
                'client_information': '123 Main St',
                'group_order_number': 'YEX123456',
                'group_order_pick_time': '12:00 PM',
                'order_subtotal': '$100.00',
                'requested_pick_up_date': '2025-01-03',
                'number_of_guests': 5,
                'delivery': 'Pickup'
            },
            'individual_orders': [
                {
                    'group_order_number': 'YEX123456',
                    'guest_name': 'John Doe',
                    'item_name': 'Test Bowl',
                    'modifications': 'Extra sauce',
                    'comments': 'No onions'
                }
            ]
        }
        
        result = validator.validate(valid_data, 'sharebite')
        assert 'success' in result
    
    def test_validate_missing_fields(self, validator):
        """Test validation with missing required fields."""
        invalid_data = {
            'order_level': {
                'business_client': 'Group Sharebite'
                # Missing required fields
            },
            'individual_orders': []
        }
        
        result = validator.validate(invalid_data, 'sharebite')
        assert result['success'] is False
        assert result['total_issues'] > 0


class TestPDFProcessor:
    """Test PDF processor."""
    
    @pytest.fixture
    def processor(self):
        """Create PDF processor."""
        from app.core.pdf_processor import PDFProcessor
        return PDFProcessor()
    
    def test_processor_initialization(self, processor):
        """Test processor initializes."""
        assert processor is not None
    
    def test_validate_nonexistent_file(self, processor):
        """Test validation of non-existent file."""
        is_valid, error = processor.validate_pdf('nonexistent.pdf')
        assert is_valid is False
        assert error is not None
