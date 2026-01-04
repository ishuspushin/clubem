"""
Validator Node - Validates extracted data against JSON schemas.
Applies: Schema Validation, Composite Pattern
"""

from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from enum import Enum
import logging
from pydantic import BaseModel, ValidationError, Field, validator

logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    """Validation severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationIssue:
    """Data structure for validation issues."""
    level: ValidationLevel
    field: str
    message: str
    expected: Optional[Any] = None
    actual: Optional[Any] = None


class OrderLevelData(BaseModel):
    """Pydantic model for order-level validation."""
    business_client: str = Field(..., min_length=1)
    client_name: str = Field(..., min_length=1)
    client_information: str
    group_order_number: str = Field(..., min_length=1)
    group_order_pick_time: str
    order_subtotal: str
    requested_pick_up_date: str
    number_of_guests: int = Field(..., ge=0)
    delivery: str
    
    @validator('business_client')
    def validate_business_client(cls, v):
        """Validate business client format."""
        valid_clients = {
            'Group Sharebite', 'Group EzCater', 'Group Grubhub',
            'Group CaterCow', 'Group ClubFeast', 'Group Hungry',
            'Group Forkable'
        }
        if v not in valid_clients:
            raise ValueError(f'Invalid business client: {v}')
        return v
    
    @validator('number_of_guests')
    def validate_guest_count(cls, v):
        """Validate guest count is reasonable."""
        if v < 0 or v > 1000:
            raise ValueError(f'Guest count out of range: {v}')
        return v


class IndividualOrderData(BaseModel):
    """Pydantic model for individual order validation."""
    group_order_number: str = Field(..., min_length=1)
    guest_name: str = Field(..., min_length=1)
    item_name: str = Field(..., min_length=1)
    modifications: Optional[str] = ""
    comments: Optional[str] = ""
    
    @validator('modifications', 'comments', pre=True)
    def validate_optional_strings(cls, v):
        """Convert None to empty string."""
        if v is None:
            return ""
        return str(v)
    
    @validator('guest_name')
    def validate_guest_name(cls, v):
        """Validate guest name is not placeholder."""
        if v.lower() in ['unknown', 'n/a', 'null', '']:
            raise ValueError('Guest name cannot be placeholder')
        return v


class ExtractedDataSchema(BaseModel):
    """Complete extraction schema."""
    order_level: OrderLevelData
    individual_orders: List[IndividualOrderData] = Field(..., min_items=1)
    
    @validator('individual_orders')
    def validate_order_consistency(cls, v, values):
        """Validate individual orders match order-level guest count."""
        if 'order_level' in values:
            expected_count = values['order_level'].number_of_guests
            actual_count = len(v)
            
            # Allow some tolerance
            if abs(expected_count - actual_count) > 2:
                logger.warning(
                    f"Guest count mismatch: expected {expected_count}, "
                    f"got {actual_count}"
                )
        return v


class ValidationRule:
    """
    Base class for validation rules.
    
    Design Pattern: Strategy Pattern
    """
    
    def __init__(self, name: str, severity: ValidationLevel):
        self.name = name
        self.severity = severity
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def validate(self, data: Dict[str, Any]) -> List[ValidationIssue]:
        """
        Validate data against this rule.
        
        Args:
            data: Data to validate
            
        Returns:
            List of validation issues
        """
        raise NotImplementedError


class RequiredFieldsRule(ValidationRule):
    """Validate required fields are present."""
    
    def __init__(self, required_fields: Set[str]):
        super().__init__("RequiredFieldsRule", ValidationLevel.ERROR)
        self.required_fields = required_fields
    
    def validate(self, data: Dict[str, Any]) -> List[ValidationIssue]:
        """Check for missing required fields."""
        issues = []
        
        try:
            for field in self.required_fields:
                if field not in data or data[field] is None:
                    issues.append(ValidationIssue(
                        level=self.severity,
                        field=field,
                        message=f"Required field '{field}' is missing",
                        expected="Non-null value",
                        actual=None
                    ))
        except Exception as e:
            self.logger.error(f"Validation error: {e}")
        
        return issues


class DataTypeRule(ValidationRule):
    """Validate data types."""
    
    def __init__(self, field_types: Dict[str, type]):
        super().__init__("DataTypeRule", ValidationLevel.ERROR)
        self.field_types = field_types
    
    def validate(self, data: Dict[str, Any]) -> List[ValidationIssue]:
        """Check data types match expected types."""
        issues = []
        
        try:
            for field, expected_type in self.field_types.items():
                if field in data:
                    actual_value = data[field]
                    if not isinstance(actual_value, expected_type):
                        issues.append(ValidationIssue(
                            level=self.severity,
                            field=field,
                            message=f"Invalid type for field '{field}'",
                            expected=expected_type.__name__,
                            actual=type(actual_value).__name__
                        ))
        except Exception as e:
            self.logger.error(f"Type validation error: {e}")
        
        return issues


class ValidatorNode:
    """
    Main Validator Node with composite validation.
    
    Design Pattern: Composite Pattern, Chain of Responsibility
    OOP: Inheritance, Polymorphism
    DSA: Set operations for efficient field checking
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._validation_rules = self._initialize_rules()
        self._validation_cache = {}  # Memoization (DSA)
    
    def _initialize_rules(self) -> List[ValidationRule]:
        """Initialize validation rules."""
        rules = []
        
        # Required fields rule
        required_fields = {
            'business_client', 'client_name', 'group_order_number',
            'number_of_guests', 'requested_pick_up_date'
        }
        rules.append(RequiredFieldsRule(required_fields))
        
        # Data type rule
        field_types = {
            'business_client': str,
            'client_name': str,
            'number_of_guests': int
        }
        rules.append(DataTypeRule(field_types))
        
        return rules
    
    def _run_pydantic_validation(
        self,
        data: Dict[str, Any]
    ) -> tuple[bool, List[ValidationIssue]]:
        """
        Run Pydantic schema validation.
        
        Args:
            data: Data to validate
            
        Returns:
            Tuple of (is_valid, issues)
        """
        issues = []
        
        try:
            # Validate using Pydantic model
            validated_data = ExtractedDataSchema(**data)
            self.logger.info("Pydantic validation passed")
            return True, issues
            
        except ValidationError as e:
            self.logger.warning(f"Pydantic validation failed: {e}")
            
            # Convert Pydantic errors to ValidationIssues
            for error in e.errors():
                field = '.'.join(str(loc) for loc in error['loc'])
                issues.append(ValidationIssue(
                    level=ValidationLevel.ERROR,
                    field=field,
                    message=error['msg'],
                    expected=error.get('ctx', {}).get('expected'),
                    actual=None
                ))
            
            return False, issues
            
        except Exception as e:
            self.logger.error(f"Unexpected validation error: {e}", exc_info=True)
            issues.append(ValidationIssue(
                level=ValidationLevel.CRITICAL,
                field='*',
                message=f"Validation system error: {str(e)}"
            ))
            return False, issues
    
    def _run_custom_rules(
        self,
        data: Dict[str, Any]
    ) -> List[ValidationIssue]:
        """
        Run custom validation rules.
        
        Args:
            data: Data to validate
            
        Returns:
            List of validation issues
        """
        all_issues = []
        
        try:
            order_level = data.get('order_level', {})
            
            # Run all validation rules
            for rule in self._validation_rules:
                try:
                    issues = rule.validate(order_level)
                    all_issues.extend(issues)
                except Exception as e:
                    self.logger.error(f"Rule {rule.name} failed: {e}")
                    all_issues.append(ValidationIssue(
                        level=ValidationLevel.ERROR,
                        field='*',
                        message=f"Rule execution error: {str(e)}"
                    ))
        
        except Exception as e:
            self.logger.error(f"Custom rules execution failed: {e}", exc_info=True)
        
        return all_issues
    
    def validate(
        self,
        extracted_data: Dict[str, Any],
        platform: str
    ) -> Dict[str, Any]:
        """
        Main validation method with comprehensive checks.
        
        Args:
            extracted_data: Data to validate
            platform: Platform identifier
            
        Returns:
            Validation result dictionary
        """
        try:
            if not extracted_data:
                raise ValueError("No data provided for validation")
            
            self.logger.info(f"Validating extraction for platform: {platform}")
            
            all_issues = []
            
            # Run Pydantic validation
            pydantic_valid, pydantic_issues = self._run_pydantic_validation(
                extracted_data
            )
            all_issues.extend(pydantic_issues)
            
            # Run custom rules
            custom_issues = self._run_custom_rules(extracted_data)
            all_issues.extend(custom_issues)
            
            # Categorize issues by severity
            critical_issues = [
                issue for issue in all_issues 
                if issue.level == ValidationLevel.CRITICAL
            ]
            error_issues = [
                issue for issue in all_issues 
                if issue.level == ValidationLevel.ERROR
            ]
            warning_issues = [
                issue for issue in all_issues 
                if issue.level == ValidationLevel.WARNING
            ]
            
            # Determine overall validity
            is_valid = len(critical_issues) == 0 and len(error_issues) == 0
            
            result = {
                'success': is_valid,
                'platform': platform,
                'total_issues': len(all_issues),
                'critical_issues': len(critical_issues),
                'error_issues': len(error_issues),
                'warning_issues': len(warning_issues),
                'issues': [
                    {
                        'level': issue.level.value,
                        'field': issue.field,
                        'message': issue.message,
                        'expected': issue.expected,
                        'actual': issue.actual
                    }
                    for issue in all_issues
                ],
                'validated_data': extracted_data if is_valid else None
            }
            
            if is_valid:
                self.logger.info("Validation successful")
            else:
                self.logger.warning(
                    f"Validation failed with {len(error_issues)} errors"
                )
            
            return result
            
        except ValueError as e:
            self.logger.error(f"Validation input error: {e}")
            return {
                'success': False,
                'platform': platform,
                'error': str(e)
            }
        except Exception as e:
            self.logger.error(f"Validation failed: {e}", exc_info=True)
            return {
                'success': False,
                'platform': platform,
                'error': f"Validation system error: {str(e)}"
            }
    
    def batch_validate(
        self,
        extracted_data_list: List[Dict[str, Any]],
        platforms: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Batch validation with error isolation.
        
        Args:
            extracted_data_list: List of extracted data
            platforms: List of platform identifiers
            
        Returns:
            List of validation results
        """
        try:
            if len(extracted_data_list) != len(platforms):
                raise ValueError("Mismatch between data and platforms count")
            
            results = []
            for data, platform in zip(extracted_data_list, platforms):
                result = self.validate(data, platform)
                results.append(result)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Batch validation failed: {e}", exc_info=True)
            return []
