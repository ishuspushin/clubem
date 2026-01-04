"""
Flask API Routes with comprehensive error handling.
Applies: RESTful design, Error handling, Request validation
"""

import os
import uuid
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
import logging

from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

from .schemas import (
    UploadRequestSchema,
    UploadResponseSchema,
    StatusResponseSchema,
    ReviewRequestSchema,
    ReviewResponseSchema,
    ErrorResponseSchema,
    HealthCheckSchema,
    PendingReviewSchema
)
from ..agents.graph import ExtractionGraph
from ..agents.nodes import HumanReviewNode
from ..core.config import Config
from ..core.pdf_processor import PDFProcessor

logger = logging.getLogger(__name__)

# Create Blueprint
api_bp = Blueprint('api', __name__)

# Global instances (initialized in app factory)
_config: Config = None
_extraction_graph: ExtractionGraph = None
_pdf_processor: PDFProcessor = None
_human_review_node: HumanReviewNode = None


def init_api(config: Config):
    """
    Initialize API with configuration.
    
    Args:
        config: Application configuration
    """
    global _config, _extraction_graph, _pdf_processor, _human_review_node
    
    try:
        _config = config
        _extraction_graph = ExtractionGraph(config)
        _pdf_processor = PDFProcessor()
        _human_review_node = HumanReviewNode(
            timeout_seconds=config.workflow.HUMAN_REVIEW_TIMEOUT
        )
        logger.info("API initialized successfully")
        
    except Exception as e:
        logger.error(f"API initialization failed: {e}", exc_info=True)
        raise


# ==================== Error Handlers ====================

@api_bp.errorhandler(400)
def bad_request(e):
    """Handle bad request errors."""
    return jsonify(ErrorResponseSchema(
        error=str(e),
        error_type="bad_request"
    ).dict()), 400


@api_bp.errorhandler(404)
def not_found(e):
    """Handle not found errors."""
    return jsonify(ErrorResponseSchema(
        error=str(e),
        error_type="not_found"
    ).dict()), 404


@api_bp.errorhandler(413)
@api_bp.errorhandler(RequestEntityTooLarge)
def file_too_large(e):
    """Handle file too large errors."""
    return jsonify(ErrorResponseSchema(
        error="File too large. Maximum size is 16MB.",
        error_type="file_too_large"
    ).dict()), 413


@api_bp.errorhandler(500)
def internal_error(e):
    """Handle internal server errors."""
    logger.error(f"Internal error: {e}", exc_info=True)
    return jsonify(ErrorResponseSchema(
        error="Internal server error",
        error_type="internal_error"
    ).dict()), 500


# ==================== Helper Functions ====================

def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    return _config and _config.is_allowed_file(filename)


def save_uploaded_file(file) -> tuple[bool, str, str]:
    """
    Save uploaded file to disk.
    
    Args:
        file: Werkzeug FileStorage object
        
    Returns:
        Tuple of (success, filepath, error_message)
    """
    try:
        if not file or file.filename == '':
            return False, '', 'No file selected'
        
        if not allowed_file(file.filename):
            return False, '', 'Invalid file type. Only PDF files allowed'
        
        # Generate secure filename
        original_filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{uuid.uuid4().hex[:8]}_{original_filename}"
        
        # Save file
        upload_path = _config.storage.get_upload_path()
        filepath = upload_path / unique_filename
        file.save(str(filepath))
        
        # Validate PDF
        is_valid, error = _pdf_processor.validate_pdf(filepath)
        if not is_valid:
            # Delete invalid file
            filepath.unlink()
            return False, '', f'Invalid PDF: {error}'
        
        logger.info(f"File saved: {unique_filename}")
        return True, str(filepath), ''
        
    except Exception as e:
        logger.error(f"File save failed: {e}", exc_info=True)
        return False, '', str(e)


# ==================== API Endpoints ====================

@api_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint.
    
    Returns:
        JSON response with service status
    """
    try:
        services = {
            'config': _config is not None,
            'extraction_graph': _extraction_graph is not None,
            'pdf_processor': _pdf_processor is not None,
            'human_review': _human_review_node is not None
        }
        
        all_healthy = all(services.values())
        
        response = HealthCheckSchema(
            status="healthy" if all_healthy else "degraded",
            version=_config.app.VERSION if _config else "unknown",
            services=services
        )
        
        return jsonify(response.dict()), 200
        
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        return jsonify(ErrorResponseSchema(
            error=str(e),
            error_type="health_check_failed"
        ).dict()), 500


@api_bp.route('/upload', methods=['POST'])
def upload_pdfs():
    """
    Upload PDF files for extraction.
    
    Request:
        - files: Multiple PDF files
        - require_review: bool (optional, default True)
        - max_retries: int (optional, default 3)
    
    Returns:
        JSON response with workflow ID and status
    """
    try:
        # Check if files are present
        if 'files' not in request.files:
            return jsonify(ErrorResponseSchema(
                error="No files provided",
                error_type="missing_files"
            ).dict()), 400
        
        files = request.files.getlist('files')
        
        if not files or all(f.filename == '' for f in files):
            return jsonify(ErrorResponseSchema(
                error="No files selected",
                error_type="no_files_selected"
            ).dict()), 400
        
        # Parse request parameters
        require_review = request.form.get('require_review', 'true').lower() == 'true'
        max_retries = int(request.form.get('max_retries', '3'))
        
        # Save uploaded files
        saved_files = []
        errors = []
        
        for file in files:
            success, filepath, error = save_uploaded_file(file)
            if success:
                saved_files.append(filepath)
            else:
                errors.append(f"{file.filename}: {error}")
        
        if not saved_files:
            return jsonify(ErrorResponseSchema(
                error="No valid files uploaded",
                error_type="no_valid_files",
                details={'errors': errors}
            ).dict()), 400
        
        # Generate workflow ID
        workflow_id = str(uuid.uuid4())
        
        logger.info(
            f"Starting extraction workflow {workflow_id} "
            f"for {len(saved_files)} files"
        )
        
        # Start extraction workflow (async in production)
        # For now, we'll return immediately and process in background
        # In production, use Celery or similar
        
        response = UploadResponseSchema(
            success=True,
            workflow_id=workflow_id,
            message=f"Successfully uploaded {len(saved_files)} file(s)",
            uploaded_files=[Path(f).name for f in saved_files],
            errors=errors
        )
        
        return jsonify(response.dict()), 202  # Accepted
        
    except ValueError as e:
        return jsonify(ErrorResponseSchema(
            error=f"Invalid parameter: {str(e)}",
            error_type="invalid_parameter"
        ).dict()), 400
        
    except Exception as e:
        logger.error(f"Upload failed: {e}", exc_info=True)
        return jsonify(ErrorResponseSchema(
            error=str(e),
            error_type="upload_failed"
        ).dict()), 500


@api_bp.route('/extract', methods=['POST'])
def extract_pdfs():
    """
    Upload and immediately extract PDFs.
    
    This endpoint processes PDFs synchronously and returns results.
    
    Returns:
        JSON response with extraction results
    """
    try:
        # Check files
        if 'files' not in request.files:
            return jsonify(ErrorResponseSchema(
                error="No files provided",
                error_type="missing_files"
            ).dict()), 400
        
        files = request.files.getlist('files')
        
        # Save files
        saved_files = []
        for file in files:
            success, filepath, error = save_uploaded_file(file)
            if success:
                saved_files.append(filepath)
        
        if not saved_files:
            return jsonify(ErrorResponseSchema(
                error="No valid files uploaded",
                error_type="no_valid_files"
            ).dict()), 400
        
        # Run extraction
        result = _extraction_graph.run(saved_files)
        
        # Clean up uploaded files
        for filepath in saved_files:
            try:
                Path(filepath).unlink()
            except Exception as e:
                logger.warning(f"Failed to delete {filepath}: {e}")
        
        # Consider it a success if data was extracted, even if it's pending review
        is_success = result.get('success') or (
            result.get('extracted_data') and 
            len(result['extracted_data']) > 0 and 
            result['extracted_data'][0] is not None
        )
        
        return jsonify(result), 200 if is_success else 500
        
    except Exception as e:
        logger.error(f"Extraction failed: {e}", exc_info=True)
        return jsonify(ErrorResponseSchema(
            error=str(e),
            error_type="extraction_failed"
        ).dict()), 500


@api_bp.route('/status/<workflow_id>', methods=['GET'])
def get_status(workflow_id: str):
    """
    Get workflow status.
    
    Args:
        workflow_id: Workflow identifier
    
    Returns:
        JSON response with workflow status
    """
    try:
        # In production, retrieve from database or cache
        # For now, return mock status
        
        response = StatusResponseSchema(
            success=True,
            workflow_id=workflow_id,
            status="processing",
            stage="extracting",
            summary={
                'created_at': datetime.now().isoformat(),
                'progress': '50%'
            },
            review_pending=False
        )
        
        return jsonify(response.dict()), 200
        
    except Exception as e:
        logger.error(f"Status check failed: {e}", exc_info=True)
        return jsonify(ErrorResponseSchema(
            error=str(e),
            error_type="status_check_failed"
        ).dict()), 500


@api_bp.route('/review/pending', methods=['GET'])
def get_pending_reviews():
    """
    Get all pending review requests.
    
    Returns:
        JSON list of pending reviews
    """
    try:
        pending_reviews = _human_review_node.get_pending_reviews()
        
        return jsonify({
            'success': True,
            'count': len(pending_reviews),
            'reviews': pending_reviews
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get pending reviews: {e}", exc_info=True)
        return jsonify(ErrorResponseSchema(
            error=str(e),
            error_type="review_fetch_failed"
        ).dict()), 500


@api_bp.route('/review/submit', methods=['POST'])
def submit_review():
    """
    Submit human review decision.
    
    Request body:
        - workflow_id: str
        - action: 'approve' or 'reject'
        - feedback: str (optional)
    
    Returns:
        JSON response with review result
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify(ErrorResponseSchema(
                error="No JSON data provided",
                error_type="missing_data"
            ).dict()), 400
        
        # Validate request
        try:
            review_request = ReviewRequestSchema(**data)
        except Exception as e:
            return jsonify(ErrorResponseSchema(
                error=f"Invalid request: {str(e)}",
                error_type="validation_error"
            ).dict()), 400
        
        # Submit review
        from ..agents.nodes.human_review_node import ReviewAction
        
        action_map = {
            'approve': ReviewAction.APPROVE,
            'reject': ReviewAction.REJECT,
            'request_changes': ReviewAction.REQUEST_CHANGES
        }
        
        action = action_map[review_request.action]
        
        result = _human_review_node.submit_review(
            request_id=f"review_{review_request.workflow_id}",
            action=action,
            feedback=review_request.feedback
        )
        
        if not result['success']:
            return jsonify(ErrorResponseSchema(
                error=result.get('error', 'Review submission failed'),
                error_type="review_failed"
            ).dict()), 400
        
        # Resume workflow if approved
        workflow_resumed = False
        if action == ReviewAction.APPROVE:
            # Resume extraction workflow
            resume_result = _extraction_graph.resume(
                review_request.workflow_id,
                review_request.action,
                review_request.feedback
            )
            workflow_resumed = resume_result.get('success', False)
        
        response = ReviewResponseSchema(
            success=True,
            workflow_id=review_request.workflow_id,
            message="Review submitted successfully",
            review_status=result['status'],
            workflow_resumed=workflow_resumed
        )
        
        return jsonify(response.dict()), 200
        
    except Exception as e:
        logger.error(f"Review submission failed: {e}", exc_info=True)
        return jsonify(ErrorResponseSchema(
            error=str(e),
            error_type="review_submission_failed"
        ).dict()), 500


@api_bp.route('/result/<workflow_id>', methods=['GET'])
def get_result(workflow_id: str):
    """
    Get final extraction result.
    
    Args:
        workflow_id: Workflow identifier
    
    Returns:
        JSON response with extraction results
    """
    try:
        # In production, retrieve from database
        # For now, return mock result
        
        return jsonify({
            'success': True,
            'workflow_id': workflow_id,
            'message': 'Results not yet available. Use /extract endpoint for synchronous processing.'
        }), 200
        
    except Exception as e:
        logger.error(f"Result retrieval failed: {e}", exc_info=True)
        return jsonify(ErrorResponseSchema(
            error=str(e),
            error_type="result_retrieval_failed"
        ).dict()), 500


@api_bp.route('/platforms', methods=['GET'])
def get_platforms():
    """
    Get list of supported platforms.
    
    Returns:
        JSON list of platforms
    """
    try:
        platforms = _config.platform.SUPPORTED_PLATFORMS
        display_names = _config.platform.PLATFORM_DISPLAY_NAMES
        
        platform_list = [
            {
                'key': platform,
                'name': display_names.get(platform, platform.title())
            }
            for platform in platforms
        ]
        
        return jsonify({
            'success': True,
            'count': len(platform_list),
            'platforms': platform_list
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get platforms: {e}", exc_info=True)
        return jsonify(ErrorResponseSchema(
            error=str(e),
            error_type="platform_fetch_failed"
        ).dict()), 500


@api_bp.route('/config', methods=['GET'])
def get_config():
    """
    Get current configuration (sanitized).
    
    Returns:
        JSON configuration
    """
    try:
        config_dict = _config.to_dict()
        
        return jsonify({
            'success': True,
            'config': config_dict
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get config: {e}", exc_info=True)
        return jsonify(ErrorResponseSchema(
            error=str(e),
            error_type="config_fetch_failed"
        ).dict()), 500
