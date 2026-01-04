#!/usr/bin/env python3
"""
Group Order Extraction System - Main Entry Point.

This script starts the Flask development server.
For production, use a WSGI server like Gunicorn or uWSGI.

Usage:
    python run.py                    # Start development server
    python run.py --host 0.0.0.0     # Expose to network
    python run.py --port 8000        # Custom port
    python run.py --debug            # Force debug mode
"""

import sys
import os
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Check Python version
if sys.version_info < (3, 10):
    print("ERROR: Python 3.10 or higher is required")
    print(f"Current version: {sys.version}")
    sys.exit(1)


def check_dependencies():
    """
    Check if all required dependencies are installed.
    
    Returns:
        Tuple of (success, missing_packages)
    """
    required_packages = [
        'flask',
        'flask_cors',
        'pydantic',
        'google.generativeai',
        'openai',
        'langgraph',
        'pypdf',
        'dotenv'
    ]
    
    missing = []
    
    for package in required_packages:
        try:
            __import__(package.replace('.', '/').split('/')[0])
        except ImportError:
            missing.append(package)
    
    return len(missing) == 0, missing


def check_environment():
    """
    Check if environment is properly configured.
    
    Returns:
        Tuple of (success, issues)
    """
    issues = []
    
    # Check .env file
    env_file = project_root / '.env'
    if not env_file.exists():
        issues.append(".env file not found. Copy .env.example to .env")
    
    # Check required environment variables
    llm_provider = os.getenv('LLM_PROVIDER', 'gemini').lower()
    if llm_provider == 'gemini':
        required_vars = ['GOOGLE_API_KEY']
    elif llm_provider == 'openai':
        required_vars = ['OPENAI_API_KEY']
    else:
        issues.append(f"Invalid LLM_PROVIDER: {llm_provider}")
        required_vars = []

    for var in required_vars:
        if not os.getenv(var):
            issues.append(f"Environment variable {var} not set")
    
    # Check directories
    required_dirs = ['uploads', 'outputs', 'logs']
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                issues.append(f"Failed to create directory {dir_name}: {e}")
    
    return len(issues) == 0, issues


def print_banner():
    """Print application banner."""
    banner = """
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║     GROUP ORDER EXTRACTION SYSTEM                         ║
    ║     AI-Powered PDF Processing for Restaurant Orders      ║
    ║                                                           ║
    ║     Version: 1.0.0                                        ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """
    print(banner)


def main():
    """Main entry point."""
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Group Order Extraction System'
    )
    parser.add_argument(
        '--host',
        default='0.0.0.0',
        help='Host to bind to (default: 0.0.0.0)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=5001,
        help='Port to bind to (default: 5001)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode'
    )
    parser.add_argument(
        '--no-reload',
        action='store_true',
        help='Disable auto-reload in debug mode'
    )
    parser.add_argument(
        '--check-only',
        action='store_true',
        help='Only check dependencies and environment, do not start server'
    )
    
    args = parser.parse_args()
    
    # Print banner
    print_banner()
    
    # Check dependencies
    print("Checking dependencies...")
    deps_ok, missing = check_dependencies()
    
    if not deps_ok:
        print("✗ Missing required packages:")
        for package in missing:
            print(f"  - {package}")
        print("\nInstall missing packages with:")
        print("  pip install -r requirements.txt")
        sys.exit(1)
    
    print("✓ All dependencies installed")
    
    # Check environment
    print("\nChecking environment...")
    env_ok, issues = check_environment()
    
    if not env_ok:
        print("✗ Environment issues:")
        for issue in issues:
            print(f"  - {issue}")
        
        if any('GOOGLE_API_KEY' in issue for issue in issues):
            print("\nCritical: GOOGLE_API_KEY is required!")
            print("Set it in your .env file:")
            print("  GOOGLE_API_KEY=your_api_key_here")
            sys.exit(1)
        
        print("\nWarning: Some environment issues detected")
        print("Attempting to continue...")
    else:
        print("✓ Environment configured correctly")
    
    # If check-only mode, exit here
    if args.check_only:
        print("\n✓ All checks passed!")
        sys.exit(0)
    
    # Import Flask app
    try:
        from app import create_app
        print("\n✓ Application modules loaded")
    except Exception as e:
        print(f"\n✗ Failed to import application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Create Flask app
    try:
        app = create_app()
        print("✓ Application created successfully")
    except Exception as e:
        print(f"\n✗ Failed to create application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Determine debug mode
    debug_mode = args.debug or os.getenv('FLASK_ENV') == 'development'
    use_reloader = not args.no_reload and debug_mode
    
    # Print startup information
    print("\n" + "=" * 60)
    print("SERVER CONFIGURATION")
    print("=" * 60)
    print(f"Host: {args.host}")
    print(f"Port: {args.port}")
    print(f"Debug Mode: {'Enabled' if debug_mode else 'Disabled'}")
    print(f"Auto-Reload: {'Enabled' if use_reloader else 'Disabled'}")
    print("=" * 60)
    print(f"\nServer starting at: http://{args.host}:{args.port}")
    print("API documentation: http://{args.host}:{args.port}/api")
    print("\nPress CTRL+C to stop the server")
    print("=" * 60 + "\n")
    
    # Start server
    try:
        app.run(
            host=args.host,
            port=args.port,
            debug=debug_mode,
            use_reloader=use_reloader,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n\n✓ Server stopped gracefully")
    except Exception as e:
        print(f"\n✗ Server error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
