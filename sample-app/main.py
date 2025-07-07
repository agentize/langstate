#!/usr/bin/env python3
"""
Sample application demonstrating khandhas usage.

This app can run in two modes:
1. Development mode: Uses the package in development mode with live reloading
2. Production mode: Uses the compiled/installed package
"""

import os
import sys
import argparse
from pathlib import Path

# Add the package to the path if in development mode
DEV_MODE = os.getenv("KHANDHAS_DEV_MODE", "true").lower() == "true"

if DEV_MODE:
    # Development mode: use local package
    package_path = Path(__file__).parent.parent / "packages" / "python-lib"
    sys.path.insert(0, str(package_path))
    print(f"🔧 Development mode: Using local package from {package_path}")
else:
    # Production mode: use installed package
    print("🚀 Production mode: Using installed package")

try:
    from khandhas import KhandhasServer, Config
    from khandhas.models import ResponseModel
    from khandhas.utils import get_logger
except ImportError as e:
    print(f"❌ Error importing khandhas: {e}")
    print("💡 Try installing the package first:")
    print("   pip install -e packages/python-lib")
    sys.exit(1)

# Configure logging
logger = get_logger(__name__)


def create_custom_server():
    """Create a custom server with additional routes and configuration."""
    # Create configuration
    config = Config(
        host="0.0.0.0",
        port=8000,
        debug=DEV_MODE,
        reload=DEV_MODE,
        log_level="DEBUG" if DEV_MODE else "INFO",
        api_prefix="/api/v1",
        cors_origins=["*"],
    )
    
    # Create server
    server = KhandhasServer(config)
    
    # Add custom startup handler
    async def startup_handler():
        mode = "development" if DEV_MODE else "production"
        logger.info(f"🚀 Sample app starting in {mode} mode")
        try:
            import khandhas
            logger.info(f"📦 Package location: {khandhas.__file__}")
        except:
            logger.info("📦 Package location: Unknown")
    
    server.add_startup_handler(startup_handler)
    
    # Add custom shutdown handler
    async def shutdown_handler():
        logger.info("🛑 Sample app shutting down")
    
    server.add_shutdown_handler(shutdown_handler)
    
    # Get FastAPI app and add custom routes
    try:
        app = server.get_app()
        
        @app.get("/")
        async def root():
            """Root endpoint."""
            return ResponseModel(
                success=True,
                message="Welcome to Khandhas Sample App",
                data={
                    "mode": "development" if DEV_MODE else "production",
                    "version": "0.1.0",
                    "endpoints": {
                        "health": "/health",
                        "info": "/api/v1/info",
                        "echo": "/api/v1/echo",
                        "sample": "/api/v1/sample",
                        "docs": "/docs",
                    }
                }
            )
        
        @app.get("/api/v1/sample")
        async def sample_endpoint():
            """Sample custom endpoint."""
            return ResponseModel(
                success=True,
                message="This is a sample endpoint",
                data={
                    "mode": "development" if DEV_MODE else "production",
                    "dev_features": {
                        "live_reload": DEV_MODE,
                        "debug_mode": DEV_MODE,
                        "detailed_errors": DEV_MODE,
                    },
                    "server_info": {
                        "host": config.host,
                        "port": config.port,
                        "log_level": config.log_level,
                    }
                }
            )
        
        @app.get("/api/v1/toggle-mode")
        async def toggle_mode():
            """Endpoint to show how to toggle between modes."""
            return ResponseModel(
                success=True,
                message="Mode information",
                data={
                    "current_mode": "development" if DEV_MODE else "production",
                    "how_to_switch": {
                        "to_development": "Set KHANDHAS_DEV_MODE=true",
                        "to_production": "Set KHANDHAS_DEV_MODE=false",
                        "restart_required": True,
                    },
                    "environment_variables": {
                        "KHANDHAS_DEV_MODE": os.getenv("KHANDHAS_DEV_MODE", "true"),
                        "KHANDHAS_HOST": os.getenv("KHANDHAS_HOST", "not set"),
                        "KHANDHAS_PORT": os.getenv("KHANDHAS_PORT", "not set"),
                        "KHANDHAS_DEBUG": os.getenv("KHANDHAS_DEBUG", "not set"),
                    }
                }
            )
        
    except Exception as e:
        logger.error(f"Error setting up custom routes: {e}")
        if DEV_MODE:
            raise
    
    return server


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Khandhas Sample Application")
    parser.add_argument("--mode", choices=["dev", "prod"], 
                       help="Override mode (dev/prod)")
    parser.add_argument("--host", default="0.0.0.0", 
                       help="Application host")
    parser.add_argument("--port", type=int, default=8000, 
                       help="Application port")
    parser.add_argument("--no-reload", action="store_true",
                       help="Disable auto-reload even in dev mode")
    
    args = parser.parse_args()
    
    # Override mode if specified
    if args.mode:
        global DEV_MODE
        DEV_MODE = args.mode == "dev"
        os.environ["KHANDHAS_DEV_MODE"] = "true" if DEV_MODE else "false"
    
    # Create and run server
    server = create_custom_server()
    
    # Override server config if specified
    if args.host != "0.0.0.0":
        server.config.host = args.host
    if args.port != 8000:
        server.config.port = args.port
    if args.no_reload:
        server.config.reload = False
    
    try:
        print(f"🚀 Starting Khandhas Sample App")
        print(f"🔧 Mode: {'Development' if DEV_MODE else 'Production'}")
        print(f"🌐 Application: http://{server.config.host}:{server.config.port}")
        print(f"📚 API Docs: http://{server.config.host}:{server.config.port}/docs")
        print(f"🔄 Auto-reload: {server.config.reload}")
        print(f"🐛 Debug mode: {server.config.debug}")
        print()
        print("Available endpoints:")
        print("  • GET  /              - Root endpoint")
        print("  • GET  /health        - Health check")
        print("  • GET  /api/v1/info   - Application info")
        print("  • POST /api/v1/echo   - Echo endpoint")
        print("  • GET  /api/v1/sample - Sample endpoint")
        print("  • GET  /api/v1/toggle-mode - Mode information")
        print()
        
        server.run()
        
    except KeyboardInterrupt:
        logger.info("👋 Sample app stopped by user")
    except Exception as e:
        logger.error(f"❌ Error running application: {e}")
        if DEV_MODE:
            raise
        sys.exit(1)


if __name__ == "__main__":
    main()
