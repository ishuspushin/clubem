"""
Pydantic schemas for extracted data validation.
Applies: Data validation, Type safety, Factory Pattern
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, validator, root_validator
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class Platform(str, Enum):
    """Supported platforms enum."""
    SHAREBITE = "sharebite"
    EZCATER = "ezcater"
    GRUBHUB = "grubhub"
    CATERCOW = "catercow"
    CLUBFEAST = "clubfeast"
    HUNGRY = "hungry"
    FORKABLE = "forkable"


class DeliveryType(str, Enum):
    """Delivery type enum."""
    DELIVERY = "Delivery"
    PICKUP = "Pickup"
    UNKNOWN = "Unknown"


class OrderLevelSchema(BaseModel):
    """
    Schema for order-level information.
    
    This validates the top-level order details extracted from PDFs.
    """
    business_client: str = Field(
        ...,
        min_length=1,
        description="Business client name (e.g., 'Group Sharebite')"
    )
    client_name: str = Field(
        ...,
        min_length=1,
        description="Company placing the order"
    )
    client_information: str = Field(
        default="",
        description="Full client contact information"
    )
    group_order_number: str = Field(
        ...,
        min_length=1,
        description="Unique order identifier"
    )
    group_order_pick_time: str = Field(
        default="",
        description="Pickup or delivery time"
    )
    order_subtotal: str = Field(
        default="",
        description="Order subtotal amount"
    )
    requested_pick_up_date: str = Field(
        ...,
        description="Requested pickup/delivery date"
    )
    number_of_guests: int = Field(
        ...,
        ge=0,
        le=10000,
        description="Number of guests in order"
    )
    delivery: str = Field(
        default="",
        description="Delivery or Pickup"
    )
    
    class Config:
        """Pydantic configuration."""
        use_enum_values = True
        validate_assignment = True
    
    @validator('business_client')
    def validate_business_client(cls, v):
        """Validate business client format."""
        valid_prefixes = ['Group Sharebite', 'Group EzCater', 'Group Grubhub',
                          'Group CaterCow', 'Group ClubFeast', 'Group Hungry',
                          'Group Forkable']
        
        if not any(v.startswith(prefix) for prefix in valid_prefixes):
            logger.warning(f"Unexpected business client format: {v}")
        
        return v
    
    @validator('number_of_guests')
    def validate_guest_count(cls, v):
        """Validate reasonable guest count."""
        if v < 0:
            raise ValueError("Guest count cannot be negative")
        if v == 0:
            logger.warning("Guest count is zero")
        if v > 1000:
            logger.warning(f"Unusually large guest count: {v}")
        return v
    
    @validator('order_subtotal')
    def validate_subtotal(cls, v):
        """Validate subtotal format."""
        if v:
            # Remove currency symbols and validate
            cleaned = v.replace('$', '').replace(',', '').strip()
            try:
                amount = float(cleaned)
                if amount < 0:
                    logger.warning(f"Negative subtotal: {v}")
            except ValueError:
                logger.warning(f"Invalid subtotal format: {v}")
        return v


class IndividualOrderSchema(BaseModel):
    """
    Schema for individual guest orders.
    
    Each guest's order with items and modifications.
    """
    group_order_number: str = Field(
        ...,
        min_length=1,
        description="Order number this item belongs to"
    )
    guest_name: str = Field(
        ...,
        min_length=1,
        description="Guest name or identifier"
    )
    item_name: str = Field(
        ...,
        min_length=1,
        description="Menu item name"
    )
    modifications: List[str] = Field(
        default_factory=list,
        description="Item modifications (structural changes)"
    )
    comments: Optional[str] = Field(
        default="",
        description="Special instructions or notes"
    )

    @validator('comments', pre=True)
    def validate_optional_strings(cls, v):
        """Convert None to empty string."""
        if v is None:
            return ""
        return str(v)
    
    @validator('modifications', pre=True)
    def validate_modifications(cls, v):
        """Ensure modifications is a list of strings."""
        if v is None:
            return []
        if isinstance(v, str):
            if not v.strip():
                return []
            # Split by comma if it looks like a CSV string
            if ',' in v:
                return [s.strip() for s in v.split(',')]
            return [v]
        if not isinstance(v, list):
            return []
        return [str(i) for i in v if i]

    
    class Config:
        """Pydantic configuration."""
        validate_assignment = True
    
    @validator('guest_name')
    def validate_guest_name(cls, v):
        """Validate guest name is not placeholder."""
        placeholder_values = ['unknown', 'n/a', 'null', 'none', '']
        
        if v.lower() in placeholder_values:
            logger.warning(f"Guest name is placeholder: {v}")
        
        # Allow "[Not provided]" for platforms without guest names
        if v.startswith('[') and v.endswith(']'):
            return v
        
        return v.strip()
    
    @validator('item_name')
    def validate_item_name(cls, v):
        """Validate item name."""
        if len(v.strip()) < 3:
            logger.warning(f"Very short item name: {v}")
        return v.strip()


class ExtractedDataSchema(BaseModel):
    """
    Complete extraction schema combining order-level and individual orders.
    
    This is the root schema for all extracted data.
    """
    order_level: OrderLevelSchema = Field(
        ...,
        description="Order-level information"
    )
    individual_orders: List[IndividualOrderSchema] = Field(
        ...,
        min_items=0,
        description="List of individual guest orders"
    )
    
    class Config:
        """Pydantic configuration."""
        validate_assignment = True
    
    @root_validator
    def validate_order_consistency(cls, values):
        """
        Validate consistency between order-level and individual orders.
        
        Cross-field validation for data integrity.
        """
        order_level = values.get('order_level')
        individual_orders = values.get('individual_orders', [])
        
        if order_level and individual_orders:
            # Check guest count consistency
            expected_count = order_level.number_of_guests
            actual_count = len(individual_orders)
            
            # Allow some tolerance for bulk orders
            if expected_count > 0 and abs(expected_count - actual_count) > 5:
                logger.warning(
                    f"Guest count mismatch: expected {expected_count}, "
                    f"got {actual_count} individual orders"
                )
            
            # Validate all individual orders have matching order number
            order_number = order_level.group_order_number
            for i, order in enumerate(individual_orders):
                if order.group_order_number != order_number:
                    logger.warning(
                        f"Individual order {i} has mismatched order number: "
                        f"{order.group_order_number} vs {order_number}"
                    )
        
        return values
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'order_level': self.order_level.dict(),
            'individual_orders': [order.dict() for order in self.individual_orders]
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics."""
        return {
            'platform': self.order_level.business_client,
            'order_number': self.order_level.group_order_number,
            'guest_count': self.order_level.number_of_guests,
            'individual_order_count': len(self.individual_orders),
            'has_modifications': any(
                order.modifications for order in self.individual_orders
            ),
            'has_comments': any(
                order.comments for order in self.individual_orders
            )
        }


class ValidationResultSchema(BaseModel):
    """Schema for validation results."""
    success: bool = Field(..., description="Validation success status")
    platform: str = Field(..., description="Platform identifier")
    total_issues: int = Field(default=0, description="Total validation issues")
    critical_issues: int = Field(default=0, description="Critical issues")
    error_issues: int = Field(default=0, description="Error issues")
    warning_issues: int = Field(default=0, description="Warning issues")
    issues: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Detailed issue list"
    )
    validated_data: Optional[ExtractedDataSchema] = Field(
        None,
        description="Validated data if successful"
    )


class ExtractionResponseSchema(BaseModel):
    """Schema for API extraction response."""
    success: bool = Field(..., description="Extraction success status")
    workflow_id: str = Field(..., description="Unique workflow identifier")
    platform: str = Field(..., description="Detected platform")
    extracted_data: Optional[ExtractedDataSchema] = Field(
        None,
        description="Extracted data"
    )
    validation_result: Optional[ValidationResultSchema] = Field(
        None,
        description="Validation result"
    )
    errors: List[str] = Field(default_factory=list, description="Error messages")
    warnings: List[str] = Field(default_factory=list, description="Warnings")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )


class PlatformSchemas:
    """
    Factory for platform-specific schema variations.
    
    Design Pattern: Factory Pattern
    """
    
    @staticmethod
    def get_schema_for_platform(platform: str) -> type[ExtractedDataSchema]:
        """
        Get schema class for specific platform.
        
        Currently returns base schema, but can be extended for
        platform-specific validations.
        
        Args:
            platform: Platform identifier
            
        Returns:
            Schema class
        """
        # Future: Add platform-specific schema classes if needed
        return ExtractedDataSchema
    
    @staticmethod
    def validate_platform_data(
        platform: str,
        data: Dict[str, Any]
    ) -> tuple[bool, Optional[ExtractedDataSchema], List[str]]:
        """
        Validate data for specific platform.
        
        Args:
            platform: Platform identifier
            data: Data to validate
            
        Returns:
            Tuple of (is_valid, validated_data, errors)
        """
        errors = []
        
        try:
            schema_class = PlatformSchemas.get_schema_for_platform(platform)
            validated_data = schema_class(**data)
            return True, validated_data, errors
            
        except Exception as e:
            errors.append(str(e))
            return False, None, errors
