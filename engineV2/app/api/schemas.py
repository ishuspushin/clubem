"""
API Request/Response schemas.
Applies: Data validation, Type safety, Documentation
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime

import logging

logger = logging.getLogger(__name__)


class UploadRequestSchema(BaseModel):
    """Schema for PDF upload request."""
    require_review: bool = Field(
        default=True,
        description="Whether human review is required"
    )
    max_retries: int = Field(
        default=3,
        ge=0,
        le=10,
        description="Maximum retry attempts"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata"
    )


class UploadResponseSchema(BaseModel):
    """Schema for upload response."""
    success: bool = Field(..., description="Upload success status")
    workflow_id: str = Field(..., description="Unique workflow identifier")
    message: str = Field(..., description="Response message")
    uploaded_files: List[str] = Field(
        default_factory=list,
        description="List of uploaded filenames"
    )
    errors: List[str] = Field(
        default_factory=list,
        description="Error messages"
    )


class ExtractionStatusSchema(BaseModel):
    """Schema for extraction status."""
    workflow_id: str = Field(..., description="Workflow identifier")
    stage: str = Field(..., description="Current workflow stage")
    is_complete: bool = Field(..., description="Completion status")
    success: Optional[bool] = Field(None, description="Success status if complete")
    progress: Dict[str, Any] = Field(
        default_factory=dict,
        description="Progress information"
    )


class StatusResponseSchema(BaseModel):
    """Schema for status check response."""
    success: bool = Field(..., description="Request success")
    workflow_id: str = Field(..., description="Workflow identifier")
    status: str = Field(..., description="Current status")
    stage: str = Field(..., description="Current stage")
    summary: Dict[str, Any] = Field(
        default_factory=dict,
        description="Workflow summary"
    )
    review_pending: bool = Field(
        default=False,
        description="Whether review is pending"
    )
    output: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Final output if completed"
    )
    errors: List[str] = Field(
        default_factory=list,
        description="Error messages"
    )


class ReviewRequestSchema(BaseModel):
    """Schema for review submission request."""
    workflow_id: str = Field(
        ...,
        min_length=1,
        description="Workflow identifier to review"
    )
    action: str = Field(
        ...,
        description="Review action: 'approve' or 'reject'"
    )
    feedback: Optional[str] = Field(
        None,
        description="Optional feedback text"
    )
    
    @validator('action')
    def validate_action(cls, v):
        """Validate review action."""
        valid_actions = ['approve', 'reject', 'request_changes']
        if v.lower() not in valid_actions:
            raise ValueError(f"Invalid action. Must be one of: {valid_actions}")
        return v.lower()


class ReviewResponseSchema(BaseModel):
    """Schema for review submission response."""
    success: bool = Field(..., description="Submission success")
    workflow_id: str = Field(..., description="Workflow identifier")
    message: str = Field(..., description="Response message")
    review_status: str = Field(..., description="Review status")
    workflow_resumed: bool = Field(
        default=False,
        description="Whether workflow was resumed"
    )


class ErrorResponseSchema(BaseModel):
    """Schema for error responses."""
    success: bool = Field(default=False, description="Always false for errors")
    error: str = Field(..., description="Error message")
    error_type: str = Field(
        default="unknown",
        description="Error type/category"
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Error timestamp"
    )
    details: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional error details"
    )


class PendingReviewSchema(BaseModel):
    """Schema for pending review information."""
    request_id: str = Field(..., description="Review request ID")
    workflow_id: str = Field(..., description="Associated workflow ID")
    platform: str = Field(..., description="Platform being reviewed")
    created_at: str = Field(..., description="Request creation time")
    validation_issues: int = Field(
        default=0,
        description="Number of validation issues"
    )
    extracted_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="Extracted data for review"
    )


class BatchUploadRequestSchema(BaseModel):
    """Schema for batch upload request."""
    require_review: bool = Field(default=True)
    max_retries: int = Field(default=3, ge=0, le=10)
    batch_metadata: Optional[Dict[str, Any]] = None


class BatchUploadResponseSchema(BaseModel):
    """Schema for batch upload response."""
    success: bool = Field(..., description="Overall batch success")
    batch_id: str = Field(..., description="Batch identifier")
    workflow_ids: List[str] = Field(
        default_factory=list,
        description="Individual workflow IDs"
    )
    total_files: int = Field(..., description="Total files in batch")
    successful: int = Field(..., description="Successfully uploaded")
    failed: int = Field(..., description="Failed uploads")
    errors: List[Dict[str, str]] = Field(
        default_factory=list,
        description="Per-file errors"
    )


class HealthCheckSchema(BaseModel):
    """Schema for health check response."""
    status: str = Field(default="healthy", description="Service status")
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="Check timestamp"
    )
    version: str = Field(default="1.0.0", description="API version")
    services: Dict[str, bool] = Field(
        default_factory=dict,
        description="Individual service status"
    )
