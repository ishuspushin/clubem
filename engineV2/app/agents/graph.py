"""
LangGraph Workflow Definition - Main orchestration graph.
Applies: Graph data structure, Conditional edges, State machine
"""

import os
import uuid
from typing import Dict, List, Any, Literal
import logging
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .state import (
    ExtractionState,
    StateManager,
    StateValidator,
    WorkflowStage
)
from .nodes import (
    ClassifierNode,
    ExtractorNode,
    ValidatorNode,
    HumanReviewNode
)
from ..core.pdf_processor import PDFProcessor
from ..core.config import Config

logger = logging.getLogger(__name__)


class ExtractionGraph:
    """
    Main LangGraph workflow orchestrator.
    
    Design Pattern: Builder Pattern, Facade Pattern
    Graph Structure: Directed Acyclic Graph (DAG) with conditional edges
    """
    
    def __init__(self, config: Config):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config = config
        
        # Initialize components
        self.state_manager = StateManager()
        self.state_validator = StateValidator()
        self.pdf_processor = PDFProcessor()
        
        # Initialize nodes
        self.classifier_node = ClassifierNode()
        self.extractor_node = ExtractorNode(config)
        self.validator_node = ValidatorNode()
        self.human_review_node = HumanReviewNode(
            timeout_seconds=config.workflow.HUMAN_REVIEW_TIMEOUT
        )
        
        # Build graph
        self.graph = self._build_graph()
        
        self.logger.info("ExtractionGraph initialized successfully")
    
    def _build_graph(self) -> StateGraph:
        """
        Build LangGraph workflow.
        
        Graph Structure:
        START → classify → extract → validate → review → END
                  ↓          ↓          ↓          ↓
                ERROR → END  ERROR → END ERROR → END  ↓
                                                  (if rejected)
                                                  → extract (retry)
        
        Returns:
            Compiled StateGraph
        """
        try:
            # Create graph with state schema
            workflow = StateGraph(ExtractionState)
            
            # Add nodes
            workflow.add_node("classify_pdfs", self._classify_node_wrapper)
            workflow.add_node("extract_data", self._extract_node_wrapper)
            workflow.add_node("validate_data", self._validate_node_wrapper)
            workflow.add_node("request_review", self._review_node_wrapper)
            workflow.add_node("finalize_output", self._finalize_node_wrapper)
            workflow.add_node("handle_error", self._error_node_wrapper)
            
            # Set entry point
            workflow.set_entry_point("classify_pdfs")
            
            # Add edges
            
            # Classify → Extract or Error
            workflow.add_conditional_edges(
                "classify_pdfs",
                self._should_continue_after_classify,
                {
                    "extract": "extract_data",
                    "error": "handle_error"
                }
            )
            
            # Extract → Validate or Error
            workflow.add_conditional_edges(
                "extract_data",
                self._should_continue_after_extract,
                {
                    "validate": "validate_data",
                    "error": "handle_error"
                }
            )
            
            # Validate → Review or Finalize or Error
            workflow.add_conditional_edges(
                "validate_data",
                self._should_continue_after_validate,
                {
                    "review": "request_review",
                    "finalize": "finalize_output",
                    "error": "handle_error"
                }
            )
            
            # Review → Retry Extract or Finalize
            workflow.add_conditional_edges(
                "request_review",
                self._should_continue_after_review,
                {
                    "retry": "extract_data",
                    "finalize": "finalize_output",
                    "pending": END  # Wait for human input
                }
            )
            
            # Finalize → END
            workflow.add_edge("finalize_output", END)
            
            # Error → END
            workflow.add_edge("handle_error", END)
            
            # Compile graph with checkpointing
            memory = MemorySaver()
            compiled_graph = workflow.compile(checkpointer=memory)
            
            self.logger.info("Graph compiled successfully")
            return compiled_graph
            
        except Exception as e:
            self.logger.error(f"Graph building failed: {e}", exc_info=True)
            raise
    
    # ==================== Node Wrappers ====================
    
    def _classify_node_wrapper(self, state: ExtractionState) -> ExtractionState:
        """
        Wrapper for classification node.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with classification results
        """
        try:
            self.logger.info("=== CLASSIFICATION STAGE ===")
            
            # Update stage
            state = self.state_manager.update_state(
                state,
                {},
                WorkflowStage.CLASSIFYING
            )
            
            # Extract PDF texts if not already done
            if not state.get('pdf_texts'):
                pdf_files = state['pdf_files']
                pdf_texts = []
                
                for pdf_path in pdf_files:
                    try:
                        text = self.pdf_processor.extract_text(pdf_path)
                        pdf_texts.append(text)
                    except Exception as e:
                        self.logger.error(f"PDF extraction failed: {e}")
                        pdf_texts.append("")
                
                state['pdf_texts'] = pdf_texts

            # Check for forced platform
            forced_platform = state.get('forced_platform')
            if forced_platform:
                self.logger.info(f"Using forced platform: {forced_platform}")
                platforms = [forced_platform] * len(state['pdf_texts'])
                classification_results = [
                    {'platform': forced_platform, 'success': True, 'confidence': 1.0, 'forced': True}
                    for _ in state['pdf_texts']
                ]
                classification_errors = []
                
                # Update state immediately
                updated_state = self.state_manager.update_state(
                    state,
                    {
                        'platforms': platforms,
                        'classification_results': classification_results,
                        'classification_errors': classification_errors
                    }
                )
                self.logger.info(f"Classified {len(platforms)} PDFs (Forced)")
                return updated_state
            
            # Classify platforms
            classification_results = self.classifier_node.batch_classify(
                state['pdf_texts']
            )
            
            # CONSENSUS LOGIC: If any file is identified, assume all files belong to that platform
            # This handles cases where one file is a cover (identified) and another is labels (unidentified)
            identified_platforms = [
                r['platform'] for r in classification_results 
                if r.get('success') and r.get('platform') != 'unknown'
            ]
            
            if identified_platforms:
                # Use the first identified platform (assuming homogeneous batch)
                consensus_platform = identified_platforms[0]
                self.logger.info(f"Consensus platform identified: {consensus_platform}")
                
                platforms = []
                classification_errors = [] # Clear errors as we are inferring
                
                for i, result in enumerate(classification_results):
                    if result.get('success') and result.get('platform') != 'unknown':
                        platforms.append(result['platform'])
                    else:
                        # Override unknown/failed with consensus
                        self.logger.info(f"Inferring platform {consensus_platform} for PDF {i+1}")
                        platforms.append(consensus_platform)
                        # Update result object to reflect success
                        classification_results[i]['platform'] = consensus_platform
                        classification_results[i]['success'] = True
                        classification_results[i]['confidence'] = 1.0
                        classification_results[i]['inferred'] = True
            else:
                # Fallback to original logic if no consensus
                platforms = [
                    result['platform'] for result in classification_results
                ]
                
                # Check for classification errors
                classification_errors = [
                    f"PDF {i}: {result.get('error', 'Unknown error')}"
                    for i, result in enumerate(classification_results)
                    if not result.get('success', False)
                ]
            
            # Update state
            updated_state = self.state_manager.update_state(
                state,
                {
                    'platforms': platforms,
                    'classification_results': classification_results,
                    'classification_errors': classification_errors
                }
            )
            
            self.logger.info(f"Classified {len(platforms)} PDFs")
            return updated_state
            
        except Exception as e:
            self.logger.error(f"Classification node failed: {e}", exc_info=True)
            return self.state_manager.add_error(
                state,
                f"Classification failed: {str(e)}"
            )
    
    def _extract_node_wrapper(self, state: ExtractionState) -> ExtractionState:
        """Wrapper for extraction node."""
        try:
            self.logger.info("=== EXTRACTION STAGE ===")
            
            # Update stage
            state = self.state_manager.update_state(
                state,
                {},
                WorkflowStage.EXTRACTING
            )
            
            # Extract data
            extraction_results = self.extractor_node.batch_extract(
                state['pdf_texts'],
                state['platforms']
            )
            
            # Process results
            extracted_data = []
            extraction_errors = []
            extraction_times = []
            
            for i, result in enumerate(extraction_results):
                if result.status.value == "success":
                    extracted_data.append(result.data)
                    extraction_times.append(result.extraction_time)
                else:
                    # Maintain alignment by appending None or empty dict
                    extracted_data.append(None) 
                    extraction_times.append(0.0)
                    extraction_errors.append(
                        f"PDF {i}: {result.error}"
                    )
            
            # Update state
            updated_state = self.state_manager.update_state(
                state,
                {
                    'extracted_data': extracted_data,
                    'extraction_errors': extraction_errors,
                    'extraction_times': extraction_times
                }
            )
            
            self.logger.info(f"Extracted {len(extracted_data)} PDFs")
            return updated_state
            
        except Exception as e:
            self.logger.error(f"Extraction node failed: {e}", exc_info=True)
            return self.state_manager.add_error(
                state,
                f"Extraction failed: {str(e)}"
            )
    
    def _validate_node_wrapper(self, state: ExtractionState) -> ExtractionState:
        """Wrapper for validation node."""
        try:
            self.logger.info("=== VALIDATION STAGE ===")
            
            # Update stage
            state = self.state_manager.update_state(
                state,
                {},
                WorkflowStage.VALIDATING
            )
            
            # Validate data
            validation_results = self.validator_node.batch_validate(
                state['extracted_data'],
                state['platforms']
            )
            
            # Check overall validity
            is_valid = all(
                result.get('success', False)
                for result in validation_results
            )
            
            # Collect validation errors
            validation_errors = []
            for i, result in enumerate(validation_results):
                if not result.get('success', False):
                    validation_errors.append(
                        f"PDF {i}: {result.get('error', 'Validation failed')}"
                    )
            
            # Update state
            updated_state = self.state_manager.update_state(
                state,
                {
                    'validation_results': validation_results,
                    'validation_errors': validation_errors,
                    'is_valid': is_valid
                }
            )
            
            self.logger.info(f"Validation complete. Valid: {is_valid}")
            return updated_state
            
        except Exception as e:
            self.logger.error(f"Validation node failed: {e}", exc_info=True)
            return self.state_manager.add_error(
                state,
                f"Validation failed: {str(e)}"
            )
    
    def _review_node_wrapper(self, state: ExtractionState) -> ExtractionState:
        """Wrapper for human review node."""
        try:
            self.logger.info("=== REVIEW STAGE ===")
            
            # Update stage
            state = self.state_manager.update_state(
                state,
                {},
                WorkflowStage.REVIEWING
            )
            
            # Check if review already exists
            if state.get('review_request_id'):
                # Check review status
                review_status = self.human_review_node.get_review_status(
                    state['review_request_id']
                )
                
                if review_status.get('success'):
                    return self.state_manager.update_state(
                        state,
                        {
                            'review_status': review_status['status'],
                            'review_feedback': review_status.get('feedback')
                        }
                    )
            
            # Create new review request
            review_result = self.human_review_node.request_review(
                platform="multi" if len(state['platforms']) > 1 else state['platforms'][0],
                extracted_data=state['extracted_data'],
                validation_result={
                    'is_valid': state['is_valid'],
                    'validation_results': state['validation_results']
                }
            )
            
            if review_result.get('success'):
                return self.state_manager.update_state(
                    state,
                    {
                        'review_request_id': review_result['request_id'],
                        'review_status': review_result['status']
                    }
                )
            else:
                return self.state_manager.add_error(
                    state,
                    f"Review request failed: {review_result.get('error')}"
                )
            
        except Exception as e:
            self.logger.error(f"Review node failed: {e}", exc_info=True)
            return self.state_manager.add_error(
                state,
                f"Review failed: {str(e)}"
            )
    
    def _finalize_node_wrapper(self, state: ExtractionState) -> ExtractionState:
        """Wrapper for finalization node."""
        try:
            self.logger.info("=== FINALIZATION STAGE ===")
            
            # Prepare final output
            final_output = []
            
            for i, extracted_data in enumerate(state['extracted_data']):
                final_output.append({
                    'pdf_file': state['pdf_files'][i],
                    'platform': state['platforms'][i],
                    'data': extracted_data,
                    'validation': state['validation_results'][i]
                })
            
            # Update state
            updated_state = self.state_manager.update_state(
                state,
                {
                    'final_output': final_output,
                    'stage': WorkflowStage.COMPLETED.value
                },
                WorkflowStage.COMPLETED
            )
            
            self.logger.info("Workflow completed successfully")
            return updated_state
            
        except Exception as e:
            self.logger.error(f"Finalization failed: {e}", exc_info=True)
            return self.state_manager.add_error(
                state,
                f"Finalization failed: {str(e)}"
            )
    
    def _error_node_wrapper(self, state: ExtractionState) -> ExtractionState:
        """Wrapper for error handling node."""
        try:
            self.logger.error("=== ERROR STAGE ===")
            
            # Update stage
            updated_state = self.state_manager.update_state(
                state,
                {},
                WorkflowStage.FAILED
            )
            
            # Log errors
            errors = state.get('errors', [])
            for error in errors:
                self.logger.error(f"Error: {error}")
            
            return updated_state
            
        except Exception as e:
            self.logger.error(f"Error handling failed: {e}", exc_info=True)
            return state
    
    # ==================== Conditional Edge Functions ====================
    
    def _should_continue_after_classify(
        self,
        state: ExtractionState
    ) -> Literal["extract", "error"]:
        """Determine next step after classification."""
        if state.get('classification_errors'):
            return "error"
        if not state.get('platforms'):
            return "error"
        return "extract"
    
    def _should_continue_after_extract(
        self,
        state: ExtractionState
    ) -> Literal["validate", "error"]:
        """Determine next step after extraction."""
        if state.get('extraction_errors'):
            # Check if we should retry
            if self.state_manager.should_retry(state):
                self.logger.info("Extraction errors detected, will retry")
                state = self.state_manager.increment_retry(state)
                return "validate"  # Still go to validate to check
            return "error"
        if not state.get('extracted_data'):
            return "error"
        return "validate"
    
    def _should_continue_after_validate(
        self,
        state: ExtractionState
    ) -> Literal["review", "finalize", "error"]:
        """Determine next step after validation."""
        if state.get('validation_errors'):
            return "error"
        
        # If review is required and data is valid
        if state.get('requires_review', True) and state.get('is_valid'):
            return "review"
        
        # If data is valid and no review needed
        if state.get('is_valid'):
            return "finalize"
        
        return "error"
    
    def _should_continue_after_review(
        self,
        state: ExtractionState
    ) -> Literal["retry", "finalize", "pending"]:
        """Determine next step after review."""
        review_status = state.get('review_status')
        
        if review_status == 'approved':
            return "finalize"
        elif review_status == 'rejected':
            # Check if we can retry
            if self.state_manager.should_retry(state):
                state = self.state_manager.increment_retry(state)
                return "retry"
            else:
                return "finalize"  # Max retries reached, finalize anyway
        else:
            # Still pending review
            return "pending"
    
    # ==================== Public API ====================
    
    def run(self, pdf_files: List[str], platform: str = None) -> Dict[str, Any]:
        """
        Run extraction workflow on PDF files.
        
        Args:
            pdf_files: List of PDF file paths
            platform: Optional platform override
            
        Returns:
            Final workflow result
        """
        try:
            # Generate workflow ID
            workflow_id = str(uuid.uuid4())
            
            self.logger.info(f"Starting workflow: {workflow_id}")
            self.logger.info(f"Processing {len(pdf_files)} PDF(s)")
            if platform:
                self.logger.info(f"Forcing platform: {platform}")
            
            # Initialize state
            initial_state = self.state_manager.initialize_state(
                workflow_id=workflow_id,
                pdf_files=pdf_files,
                forced_platform=platform
            )
            
            # Run graph
            config = {"configurable": {"thread_id": workflow_id}}
            final_state = self.graph.invoke(initial_state, config)
            
            # Return result
            return {
                'success': final_state.get('stage') == WorkflowStage.COMPLETED.value,
                'workflow_id': workflow_id,
                'summary': self.state_manager.get_summary(final_state),
                'output': final_state.get('final_output'),
                'extracted_data': final_state.get('extracted_data', []),  # Return raw data even if validation failed
                'errors': final_state.get('errors', []),
                'warnings': final_state.get('warnings', [])
            }
            
        except Exception as e:
            self.logger.error(f"Workflow execution failed: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
    
    def resume(self, workflow_id: str, review_action: str, feedback: str = None) -> Dict[str, Any]:
        """
        Resume workflow after human review.
        
        Args:
            workflow_id: Workflow identifier
            review_action: approve/reject
            feedback: Optional feedback
            
        Returns:
            Updated workflow result
        """
        try:
            self.logger.info(f"Resuming workflow: {workflow_id}")
            
            # Submit review
            review_result = self.human_review_node.submit_review(
                request_id=f"review_{workflow_id}",
                action=review_action,
                feedback=feedback
            )
            
            if not review_result.get('success'):
                return {
                    'success': False,
                    'error': review_result.get('error')
                }
            
            # Resume graph execution
            config = {"configurable": {"thread_id": workflow_id}}
            final_state = self.graph.invoke(None, config)
            
            return {
                'success': True,
                'workflow_id': workflow_id,
                'summary': self.state_manager.get_summary(final_state),
                'output': final_state.get('final_output')
            }
            
        except Exception as e:
            self.logger.error(f"Workflow resume failed: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }
