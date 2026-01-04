"""
Group Order Extraction System - Flask Application Factory.

This module creates and configures the Flask application with all necessary
components, blueprints, and error handlers.
"""

import os
import logging
from pathlib import Path
from flask import Flask, jsonify
from flask_cors import CORS

from .core.config import Config
from .utils.logger import setup_logger, LoggerConfig
from .api.routes import api_bp, init_api


# Package metadata
__version__ = "1.0.0"
__author__ = "Group Order Extraction Team"
__description__ = "AI-powered PDF extraction system for restaurant group orders"


def create_app(config: Config = None) -> Flask:
    """
    Application factory function.
    
    Creates and configures the Flask application with all necessary
    components including blueprints, error handlers, and extensions.
    
    Design Pattern: Factory Pattern
    
    Args:
        config: Optional configuration object. If None, loads from environment.
        
    Returns:
        Configured Flask application instance
    """
    
    # Create Flask app
    app = Flask(__name__)
    
    # Load configuration
    if config is None:
        try:
            config = Config.load_from_env()
        except Exception as e:
            print(f"ERROR: Failed to load configuration: {e}")
            raise
    
    # Validate configuration
    is_valid, errors = config.validate_configuration()
    if not is_valid:
        print(f"WARNING: Configuration validation issues: {errors}")
    
    # Configure Flask app
    app.config['SECRET_KEY'] = config.flask.SECRET_KEY
    app.config['MAX_CONTENT_LENGTH'] = config.flask.MAX_CONTENT_LENGTH
    app.config['UPLOAD_FOLDER'] = str(config.storage.get_upload_path())
    app.config['OUTPUT_FOLDER'] = str(config.storage.get_output_path())
    app.config['DEBUG'] = config.app.DEBUG
    
    # Store config in app
    app.config['APP_CONFIG'] = config
    
    # Setup logging
    try:
        logger_config = LoggerConfig(
            name='group_order_extraction',
            level=config.app.LOG_LEVEL,
            console_output=True,
            file_output=True,
            json_format=False
        )
        logger = setup_logger(logger_config)
        app.logger = logger
        logger.info("=" * 60)
        logger.info("Group Order Extraction System Starting...")
        logger.info(f"Version: {__version__}")
        logger.info(f"Environment: {'Development' if config.app.DEBUG else 'Production'}")
        logger.info("=" * 60)
    except Exception as e:
        print(f"ERROR: Failed to setup logging: {e}")
        raise
    
    # Enable CORS
    try:
        CORS(app, resources={
            r"/api/*": {
                "origins": "*",
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization"]
            }
        })
        logger.info("CORS enabled for API endpoints")
    except Exception as e:
        logger.error(f"Failed to enable CORS: {e}")
    
    # Create necessary directories
    try:
        config.storage.create_directories()
        logger.info("Storage directories verified")
    except Exception as e:
        logger.error(f"Failed to create directories: {e}")
    
    # Initialize API
    try:
        init_api(config)
        logger.info("API components initialized")
    except Exception as e:
        logger.error(f"Failed to initialize API: {e}", exc_info=True)
        raise
    
    # Register blueprints
    try:
        app.register_blueprint(api_bp, url_prefix='/api')
        logger.info("API blueprint registered at /api")
    except Exception as e:
        logger.error(f"Failed to register blueprints: {e}")
        raise
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register shell context
    register_shell_context(app)
    
    # Add custom CLI commands
    register_cli_commands(app, config)
    
    # Root route
    @app.route('/')
    def index():
        """Root endpoint with API information."""
        return jsonify({
            'name': 'Group Order Extraction API',
            'version': __version__,
            'description': __description__,
            'status': 'running',
            'endpoints': {
                'health': '/api/health',
                'upload': '/api/upload',
                'extract': '/api/extract',
                'status': '/api/status/<workflow_id>',
                'review': '/api/review/submit',
                'platforms': '/api/platforms'
            },
            'documentation': '/api/docs'  # Future: Add Swagger/OpenAPI docs
        })
    
    logger.info("Application factory completed successfully")
    return app


def register_error_handlers(app: Flask) -> None:
    """
    Register global error handlers.
    
    Args:
        app: Flask application instance
    """
    
    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 errors."""
        return jsonify({
            'success': False,
            'error': 'Resource not found',
            'error_type': 'not_found'
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors."""
        app.logger.error(f"Internal server error: {error}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'error_type': 'internal_error'
        }), 500
    
    @app.errorhandler(413)
    def request_entity_too_large(error):
        """Handle file too large errors."""
        return jsonify({
            'success': False,
            'error': 'File too large. Maximum size is 16MB',
            'error_type': 'file_too_large'
        }), 413
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        """Handle uncaught exceptions."""
        app.logger.error(f"Unhandled exception: {error}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred',
            'error_type': 'unexpected_error'
        }), 500


def register_shell_context(app: Flask) -> None:
    """
    Register shell context for Flask shell.
    
    Makes commonly used objects available in Flask shell.
    
    Args:
        app: Flask application instance
    """
    
    @app.shell_context_processor
    def make_shell_context():
        """Create shell context."""
        from app.core.config import Config
        from app.core.pdf_processor import PDFProcessor
        from app.agents.graph import ExtractionGraph
        
        return {
            'app': app,
            'config': app.config.get('APP_CONFIG'),
            'Config': Config,
            'PDFProcessor': PDFProcessor,
            'ExtractionGraph': ExtractionGraph
        }


def register_cli_commands(app: Flask, config: Config) -> None:
    """
    Register custom CLI commands.
    
    Args:
        app: Flask application instance
        config: Application configuration
    """
    
    @app.cli.command('init-db')
    def init_db():
        """Initialize database (placeholder for future implementation)."""
        click.echo("Database initialization not yet implemented.")
    
    @app.cli.command('cleanup')
    def cleanup_files():
        """Clean up old temporary files."""
        from app.utils.file_handler import FileManager
        
        click.echo("Cleaning up old files...")
        
        upload_manager = FileManager(config.storage.get_upload_path())
        deleted_uploads = upload_manager.cleanup_old_files(days=7)
        
        output_manager = FileManager(config.storage.get_output_path())
        deleted_outputs = output_manager.cleanup_old_files(days=30)
        
        click.echo(f"Deleted {deleted_uploads} old uploads")
        click.echo(f"Deleted {deleted_outputs} old outputs")
        click.echo("Cleanup complete!")
    
    @app.cli.command('test-extraction')
    @click.argument('pdf_path')
    def test_extraction(pdf_path):
        """Test extraction on a single PDF file."""
        from app.agents.graph import ExtractionGraph
        
        click.echo(f"Testing extraction on: {pdf_path}")
        
        if not Path(pdf_path).exists():
            click.echo(f"ERROR: File not found: {pdf_path}", err=True)
            return
        
        graph = ExtractionGraph(config)
        result = graph.run([pdf_path])
        
        if result['success']:
            click.echo("✓ Extraction successful!")
            click.echo(f"Workflow ID: {result['workflow_id']}")
            
            import json
            click.echo("\nExtracted Data:")
            click.echo(json.dumps(result['output'], indent=2))
        else:
            click.echo("✗ Extraction failed!", err=True)
            click.echo(f"Error: {result.get('error')}")
    
    @app.cli.command('config-info')
    def config_info():
        """Display current configuration."""
        click.echo("Current Configuration:")
        click.echo("=" * 60)
        click.echo(f"Environment: {'Development' if config.app.DEBUG else 'Production'}")
        click.echo(f"Log Level: {config.app.LOG_LEVEL}")
        click.echo(f"Upload Folder: {config.storage.get_upload_path()}")
        click.echo(f"Output Folder: {config.storage.get_output_path()}")
        click.echo(f"Max Retries: {config.workflow.MAX_RETRIES}")
        click.echo(f"Review Timeout: {config.workflow.HUMAN_REVIEW_TIMEOUT}s")
        click.echo(f"Supported Platforms: {len(config.platform.SUPPORTED_PLATFORMS)}")
        click.echo("=" * 60)


# Import click for CLI commands
try:
    import click
except ImportError:
    click = None
