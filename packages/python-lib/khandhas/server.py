"""Core server implementation."""

import asyncio
import logging
from typing import Optional, Dict, Any, Callable, List
from contextlib import asynccontextmanager

try:
    from fastapi import FastAPI, Request, Response
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    import uvicorn
except ImportError:
    # Fallback for when FastAPI is not installed
    FastAPI = None
    uvicorn = None

from .config import Config
from .models import ResponseModel
from .utils import get_logger


class KhandhasServer:
    """Main server class for Khandhas application."""

    def __init__(self, config: Optional[Config] = None):
        """Initialize the server."""
        self.config = config or Config()
        self.logger = get_logger(__name__)
        self.app: Optional[FastAPI] = None
        self._startup_handlers: List[Callable] = []
        self._shutdown_handlers: List[Callable] = []

        if FastAPI is None:
            self.logger.warning(
                "FastAPI not installed. Some features will be unavailable."
            )

    def create_app(self) -> FastAPI:
        """Create and configure the FastAPI application."""
        if FastAPI is None:
            raise RuntimeError(
                "FastAPI is not installed. Please install with: pip install fastapi"
            )

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            # Startup
            self.logger.info("Starting Khandhas...")
            for handler in self._startup_handlers:
                await handler() if asyncio.iscoroutinefunction(handler) else handler()
            yield
            # Shutdown
            self.logger.info("Shutting down Khandhas...")
            for handler in self._shutdown_handlers:
                await handler() if asyncio.iscoroutinefunction(handler) else handler()

        self.app = FastAPI(
            title="Khandhas",
            description="A Python library for khandhas application",
            version="0.1.0",
            lifespan=lifespan,
            debug=self.config.debug,
        )

        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=self.config.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Add exception handler
        @self.app.exception_handler(Exception)
        async def general_exception_handler(request: Request, exc: Exception):
            self.logger.error(f"Unhandled exception: {exc}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content=ResponseModel(
                    success=False,
                    message="Internal application error",
                    error=(
                        str(exc) if self.config.debug else "Internal application error"
                    ),
                ).model_dump(),
            )

        # Add basic health check
        @self.app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return ResponseModel(
                success=True,
                message="Application is healthy",
                data={"status": "ok", "version": "0.1.0"},
            )

        # Add API routes
        self._setup_routes()

        return self.app

    def _setup_routes(self):
        """Set up API routes."""
        if not self.app:
            return

        api_router = self.app

        @api_router.get(f"{self.config.api_prefix}/info")
        async def get_server_info():
            """Get application information."""
            return ResponseModel(
                success=True,
                message="Application information",
                data={
                    "version": "0.1.0",
                    "config": self.config.to_dict(),
                    "debug": self.config.debug,
                },
            )

        @api_router.post(f"{self.config.api_prefix}/echo")
        async def echo(request: Request):
            """Echo endpoint for testing."""
            body = (
                await request.json()
                if request.headers.get("content-type") == "application/json"
                else {}
            )
            return ResponseModel(
                success=True,
                message="Echo response",
                data={
                    "method": request.method,
                    "url": str(request.url),
                    "headers": dict(request.headers),
                    "body": body,
                },
            )

    def add_startup_handler(self, handler: Callable):
        """Add a startup handler."""
        self._startup_handlers.append(handler)

    def add_shutdown_handler(self, handler: Callable):
        """Add a shutdown handler."""
        self._shutdown_handlers.append(handler)

    def run(self, **kwargs):
        """Run the server."""
        if uvicorn is None:
            raise RuntimeError(
                "uvicorn is not installed. Please install with: pip install uvicorn"
            )

        if not self.app:
            self.create_app()

        # Override config with kwargs
        run_config = {
            "host": self.config.host,
            "port": self.config.port,
            "log_level": self.config.log_level.lower(),
            "reload": self.config.reload,
            **kwargs,
        }

        self.logger.info(
            f"Starting application on {run_config['host']}:{run_config['port']}"
        )
        uvicorn.run(self.app, **run_config)

    async def start(self, **kwargs):
        """Start the server asynchronously."""
        if not self.app:
            self.create_app()

        config = uvicorn.Config(
            self.app,
            host=self.config.host,
            port=self.config.port,
            log_level=self.config.log_level.lower(),
            **kwargs,
        )
        server = uvicorn.Server(config)
        await server.serve()

    def get_app(self) -> FastAPI:
        """Get the FastAPI application."""
        if not self.app:
            self.create_app()
        return self.app
