"""
State Management for LangGraph Workflow.
Applies: TypedDict for type safety, Immutable state pattern
"""

from typing import TypedDict, List, Dict, Optional, Any, Literal
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
import copy

logger = logging.getLogger(__name__)


class WorkflowStage(Enum):
    """Enum for workflow stages."""
    INITIALIZED = "initialized"
    CLASSIFYING = "classifying"
    EXTRACTING = "extracting"
    VALIDATING = "validating"
    REVIEWING = "reviewing"
    COMPLETED = "completed"
    FAILED = "failed"


class ExtractionState(TypedDict, total=False):
    """
    TypedDict for LangGraph state management.
    
    This ensures type safety and clear state structure throughout the workflow.
    total=False allows optional fields.
    """
    # Input Data
    pdf_files: List[str]  # List of PDF file paths
    pdf_texts: List[str]  # Extracted text from PDFs
    forced_platform: Optional[str]  # Manually specified platform (optional)
    
    # Workflow Metadata
    workflow_id: str
    stage: str  # Current workflow stage
    created_at: str  # ISO format timestamp
    updated_at: str  # ISO format timestamp
    
    # Classification Results
    platforms: List[str]  # Detected platforms for each PDF
    classification_results: List[Dict[str, Any]]
    classification_errors: List[str]
    
    # Extraction Results
    extracted_data: List[Dict[str, Any]]  # Extracted data for each PDF
    extraction_errors: List[str]
    extraction_times: List[float]
    
    # Validation Results
    validation_results: List[Dict[str, Any]]
    validation_errors: List[str]
    is_valid: bool
    
    # Human Review
    review_request_id: Optional[str]
    review_status: Optional[str]
    review_feedback: Optional[str]
    review_action: Optional[str]
    requires_review: bool
    
    # Final Output
    final_output: Optional[List[Dict[str, Any]]]
    
    # Error Tracking
    errors: List[str]
    warnings: List[str]
    
    # Retry Mechanism
    retry_count: int
    max_retries: int


@dataclass
class StateSnapshot:
    """
    Immutable snapshot of state at a point in time.
    
    Design Pattern: Memento Pattern (for state history)
    """
    workflow_id: str
    stage: WorkflowStage
    timestamp: datetime
    state_data: Dict[str, Any]
    
    def __repr__(self) -> str:
        return f"StateSnapshot(workflow_id={self.workflow_id}, stage={self.stage.value})"


class StateManager:
    """
    State manager with history tracking and rollback capabilities.
    
    Design Pattern: Memento Pattern, Command Pattern
    OOP: Encapsulation, Single Responsibility
    DSA: Stack for state history (LIFO)
    """
    
    def __init__(self, max_history: int = 50):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.max_history = max_history
        self._state_history: List[StateSnapshot] = []  # Stack (DSA)
        self._current_state: Optional[ExtractionState] = None
    
    def initialize_state(
        self,
        workflow_id: str,
        pdf_files: List[str],
        forced_platform: Optional[str] = None,
        max_retries: int = 3
    ) -> ExtractionState:
        """
        Initialize new extraction state.
        
        Args:
            workflow_id: Unique workflow identifier
            pdf_files: List of PDF file paths
            forced_platform: Manually specified platform (optional)
            max_retries: Maximum retry attempts
            
        Returns:
            Initial state dictionary
        """
        try:
            current_time = datetime.now().isoformat()
            
            initial_state: ExtractionState = {
                # Input
                'pdf_files': pdf_files,
                'pdf_texts': [],
                'forced_platform': forced_platform,
                
                # Metadata
                'workflow_id': workflow_id,
                'stage': WorkflowStage.INITIALIZED.value,
                'created_at': current_time,
                'updated_at': current_time,
                
                # Classification
                'platforms': [],
                'classification_results': [],
                'classification_errors': [],
                
                # Extraction
                'extracted_data': [],
                'extraction_errors': [],
                'extraction_times': [],
                
                # Validation
                'validation_results': [],
                'validation_errors': [],
                'is_valid': False,
                
                # Human Review
                'review_request_id': None,
                'review_status': None,
                'review_feedback': None,
                'review_action': None,
                'requires_review': True,  # Default to requiring review
                
                # Output
                'final_output': None,
                
                # Errors
                'errors': [],
                'warnings': [],
                
                # Retry
                'retry_count': 0,
                'max_retries': max_retries
            }
            
            self._current_state = initial_state
            self._save_snapshot(WorkflowStage.INITIALIZED, initial_state)
            
            self.logger.info(f"Initialized state for workflow: {workflow_id}")
            return initial_state
            
        except Exception as e:
            self.logger.error(f"State initialization failed: {e}", exc_info=True)
            raise
    
    def _save_snapshot(
        self,
        stage: WorkflowStage,
        state: ExtractionState
    ) -> None:
        """
        Save state snapshot to history stack.
        
        Time Complexity: O(1) for append, O(n) if history limit exceeded
        Space Complexity: O(k) where k = max_history
        
        Args:
            stage: Current workflow stage
            state: State to snapshot
        """
        try:
            # Create deep copy to ensure immutability
            snapshot = StateSnapshot(
                workflow_id=state['workflow_id'],
                stage=stage,
                timestamp=datetime.now(),
                state_data=copy.deepcopy(state)
            )
            
            # Add to history stack
            self._state_history.append(snapshot)
            
            # Maintain max history size (FIFO when limit exceeded)
            if len(self._state_history) > self.max_history:
                self._state_history.pop(0)  # Remove oldest
            
            self.logger.debug(
                f"Saved snapshot: {stage.value} "
                f"(history size: {len(self._state_history)})"
            )
            
        except Exception as e:
            self.logger.error(f"Failed to save snapshot: {e}")
    
    def update_state(
        self,
        state: ExtractionState,
        updates: Dict[str, Any],
        stage: Optional[WorkflowStage] = None
    ) -> ExtractionState:
        """
        Update state with new values.
        
        Args:
            state: Current state
            updates: Dictionary of updates
            stage: New workflow stage (if changing)
            
        Returns:
            Updated state
        """
        try:
            # Create new state dict (immutability principle)
            updated_state = state.copy()
            
            # Apply updates
            for key, value in updates.items():
                if key in ExtractionState.__annotations__:
                    updated_state[key] = value
                else:
                    self.logger.warning(f"Unknown state key: {key}")
            
            # Update timestamp
            updated_state['updated_at'] = datetime.now().isoformat()
            
            # Update stage if provided
            if stage:
                updated_state['stage'] = stage.value
                self._save_snapshot(stage, updated_state)
            
            self._current_state = updated_state
            
            self.logger.debug(f"State updated with keys: {list(updates.keys())}")
            return updated_state
            
        except Exception as e:
            self.logger.error(f"State update failed: {e}", exc_info=True)
            return state  # Return unchanged state on error
    
    def add_error(
        self,
        state: ExtractionState,
        error_message: str,
        error_type: Literal['error', 'warning'] = 'error'
    ) -> ExtractionState:
        """
        Add error or warning to state.
        
        Args:
            state: Current state
            error_message: Error message
            error_type: Type of error
            
        Returns:
            Updated state
        """
        try:
            updated_state = state.copy()
            
            if error_type == 'error':
                updated_state['errors'] = state.get('errors', []) + [error_message]
            else:
                updated_state['warnings'] = state.get('warnings', []) + [error_message]
            
            updated_state['updated_at'] = datetime.now().isoformat()
            
            self.logger.info(f"Added {error_type}: {error_message}")
            return updated_state
            
        except Exception as e:
            self.logger.error(f"Failed to add error: {e}")
            return state
    
    def increment_retry(self, state: ExtractionState) -> ExtractionState:
        """
        Increment retry counter.
        
        Args:
            state: Current state
            
        Returns:
            Updated state
        """
        try:
            updated_state = state.copy()
            updated_state['retry_count'] = state.get('retry_count', 0) + 1
            updated_state['updated_at'] = datetime.now().isoformat()
            
            self.logger.info(
                f"Retry count: {updated_state['retry_count']}/"
                f"{state.get('max_retries', 3)}"
            )
            
            return updated_state
            
        except Exception as e:
            self.logger.error(f"Failed to increment retry: {e}")
            return state
    
    def get_history(self) -> List[StateSnapshot]:
        """
        Get state history.
        
        Returns:
            List of state snapshots (oldest to newest)
        """
        return self._state_history.copy()
    
    def rollback(self, steps: int = 1) -> Optional[ExtractionState]:
        """
        Rollback state to previous snapshot.
        
        Args:
            steps: Number of steps to rollback
            
        Returns:
            Previous state or None if not available
        """
        try:
            if len(self._state_history) < steps + 1:
                self.logger.warning("Not enough history for rollback")
                return None
            
            # Get previous snapshot
            previous_snapshot = self._state_history[-(steps + 1)]
            previous_state = previous_snapshot.state_data
            
            self._current_state = previous_state
            
            self.logger.info(
                f"Rolled back {steps} step(s) to stage: "
                f"{previous_snapshot.stage.value}"
            )
            
            return previous_state
            
        except Exception as e:
            self.logger.error(f"Rollback failed: {e}", exc_info=True)
            return None
    
    def get_current_stage(self, state: ExtractionState) -> WorkflowStage:
        """Get current workflow stage as enum."""
        try:
            stage_str = state.get('stage', WorkflowStage.INITIALIZED.value)
            return WorkflowStage(stage_str)
        except ValueError:
            return WorkflowStage.INITIALIZED
    
    def is_complete(self, state: ExtractionState) -> bool:
        """Check if workflow is complete."""
        stage = self.get_current_stage(state)
        return stage in [WorkflowStage.COMPLETED, WorkflowStage.FAILED]
    
    def should_retry(self, state: ExtractionState) -> bool:
        """Check if workflow should retry."""
        retry_count = state.get('retry_count', 0)
        max_retries = state.get('max_retries', 3)
        return retry_count < max_retries
    
    def get_summary(self, state: ExtractionState) -> Dict[str, Any]:
        """
        Get workflow summary.
        
        Args:
            state: Current state
            
        Returns:
            Summary dictionary
        """
        try:
            return {
                'workflow_id': state.get('workflow_id'),
                'stage': state.get('stage'),
                'pdf_count': len(state.get('pdf_files', [])),
                'platforms_detected': len(state.get('platforms', [])),
                'extracted_count': len(state.get('extracted_data', [])),
                'is_valid': state.get('is_valid', False),
                'requires_review': state.get('requires_review', False),
                'review_status': state.get('review_status'),
                'errors': len(state.get('errors', [])),
                'warnings': len(state.get('warnings', [])),
                'retry_count': state.get('retry_count', 0),
                'created_at': state.get('created_at'),
                'updated_at': state.get('updated_at')
            }
        except Exception as e:
            self.logger.error(f"Failed to generate summary: {e}")
            return {}


class StateValidator:
    """
    Validator for state transitions.
    
    Design Pattern: State Pattern
    """
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._valid_transitions = self._build_transition_map()
    
    def _build_transition_map(self) -> Dict[WorkflowStage, List[WorkflowStage]]:
        """
        Build valid state transition map.
        
        Returns:
            Dictionary mapping current stage to allowed next stages
        """
        return {
            WorkflowStage.INITIALIZED: [
                WorkflowStage.CLASSIFYING,
                WorkflowStage.FAILED
            ],
            WorkflowStage.CLASSIFYING: [
                WorkflowStage.EXTRACTING,
                WorkflowStage.FAILED
            ],
            WorkflowStage.EXTRACTING: [
                WorkflowStage.VALIDATING,
                WorkflowStage.FAILED
            ],
            WorkflowStage.VALIDATING: [
                WorkflowStage.REVIEWING,
                WorkflowStage.COMPLETED,
                WorkflowStage.FAILED
            ],
            WorkflowStage.REVIEWING: [
                WorkflowStage.EXTRACTING,  # Re-extract if rejected
                WorkflowStage.COMPLETED,
                WorkflowStage.FAILED
            ],
            WorkflowStage.COMPLETED: [],  # Terminal state
            WorkflowStage.FAILED: []  # Terminal state
        }
    
    def can_transition(
        self,
        from_stage: WorkflowStage,
        to_stage: WorkflowStage
    ) -> bool:
        """
        Check if state transition is valid.
        
        Args:
            from_stage: Current stage
            to_stage: Target stage
            
        Returns:
            True if transition is allowed
        """
        try:
            allowed_stages = self._valid_transitions.get(from_stage, [])
            is_valid = to_stage in allowed_stages
            
            if not is_valid:
                self.logger.warning(
                    f"Invalid transition: {from_stage.value} -> {to_stage.value}"
                )
            
            return is_valid
            
        except Exception as e:
            self.logger.error(f"Transition validation failed: {e}")
            return False
    
    def validate_state(self, state: ExtractionState) -> List[str]:
        """
        Validate state completeness.
        
        Args:
            state: State to validate
            
        Returns:
            List of validation errors
        """
        errors = []
        
        try:
            # Required fields
            required_fields = ['workflow_id', 'stage', 'created_at']
            for field in required_fields:
                if field not in state or state[field] is None:
                    errors.append(f"Missing required field: {field}")
            
            # Stage-specific validation
            stage = WorkflowStage(state.get('stage', ''))
            
            if stage == WorkflowStage.EXTRACTING:
                if not state.get('platforms'):
                    errors.append("No platforms detected for extraction")
            
            if stage == WorkflowStage.VALIDATING:
                if not state.get('extracted_data'):
                    errors.append("No extracted data to validate")
            
            if stage == WorkflowStage.REVIEWING:
                if not state.get('review_request_id'):
                    errors.append("No review request ID")
            
        except Exception as e:
            errors.append(f"State validation error: {str(e)}")
        
        return errors
