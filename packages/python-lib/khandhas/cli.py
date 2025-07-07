"""Command line interface for khandhas."""

import argparse
import sys
import os
from typing import Optional

from .server import KhandhasServer
from .config import Config
from .utils import get_logger


def create_parser() -> argparse.ArgumentParser:
    """Create command line parser."""
    parser = argparse.ArgumentParser(
        description="Khandhas - A Python library for khandhas application"
    )

    # Server configuration
    parser.add_argument(
        "--host", default="0.0.0.0", help="Application host (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="Application port (default: 8000)"
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument(
        "--reload", action="store_true", help="Enable auto-reload on code changes"
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Logging level (default: INFO)",
    )

    # Environment configuration
    parser.add_argument("--env-file", help="Path to environment file")
    parser.add_argument("--config-file", help="Path to configuration file")

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Run server command
    run_parser = subparsers.add_parser("run", help="Run the application")
    run_parser.add_argument(
        "--workers", type=int, default=1, help="Number of worker processes (default: 1)"
    )

    # Development command
    dev_parser = subparsers.add_parser("dev", help="Run in development mode")
    dev_parser.add_argument(
        "--watch", action="store_true", help="Watch for file changes and restart"
    )

    # Version command
    version_parser = subparsers.add_parser("version", help="Show version information")

    return parser


def load_env_file(env_file: str) -> None:
    """Load environment variables from file."""
    if not os.path.exists(env_file):
        return

    try:
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()
    except Exception as e:
        logger = get_logger(__name__)
        logger.error(f"Failed to load environment file {env_file}: {e}")


def load_config_file(config_file: str) -> Optional[dict]:
    """Load configuration from file."""
    if not os.path.exists(config_file):
        return None

    try:
        import json

        with open(config_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger = get_logger(__name__)
        logger.error(f"Failed to load config file {config_file}: {e}")
        return None


def run_server(args: argparse.Namespace) -> None:
    """Run the application."""
    logger = get_logger(__name__)

    # Load environment file if specified
    if args.env_file:
        load_env_file(args.env_file)

    # Load configuration
    config_data = {}
    if args.config_file:
        file_config = load_config_file(args.config_file)
        if file_config:
            config_data.update(file_config)

    # Override with command line arguments
    config_data.update(
        {
            "host": args.host,
            "port": args.port,
            "debug": args.debug,
            "reload": args.reload,
            "log_level": args.log_level,
        }
    )

    # Create server config
    config = Config(**config_data)

    # Create and run server
    server = KhandhasServer(config)

    try:
        logger.info(f"Starting Khandhas on {config.host}:{config.port}")
        server.run()
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)


def run_dev_server(args: argparse.Namespace) -> None:
    """Run development application."""
    logger = get_logger(__name__)

    # Load environment file if specified
    if args.env_file:
        load_env_file(args.env_file)

    # Development configuration
    config_data = {
        "host": args.host,
        "port": args.port,
        "debug": True,
        "reload": True,
        "log_level": "DEBUG",
    }

    # Load configuration file if specified
    if args.config_file:
        file_config = load_config_file(args.config_file)
        if file_config:
            config_data.update(file_config)
            # Ensure dev settings
            config_data["debug"] = True
            config_data["reload"] = True

    # Create server config
    config = Config(**config_data)

    # Create and run server
    server = KhandhasServer(config)

    try:
        logger.info(
            f"Starting Khandhas in development mode on {config.host}:{config.port}"
        )
        logger.info("Debug mode enabled, auto-reload enabled")
        server.run(reload=True)
    except KeyboardInterrupt:
        logger.info("Development application stopped by user")
    except Exception as e:
        logger.error(f"Development application error: {e}")
        sys.exit(1)


def show_version() -> None:
    """Show version information."""
    from . import __version__

    print(f"Khandhas v{__version__}")


def main() -> None:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    # Set log level
    logger = get_logger(__name__, args.log_level)

    # Handle commands
    if args.command == "run":
        run_server(args)
    elif args.command == "dev":
        run_dev_server(args)
    elif args.command == "version":
        show_version()
    else:
        # Default to run if no command specified
        run_server(args)


if __name__ == "__main__":
    main()
