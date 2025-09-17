"""Utility functions for the server."""

import logging
import sys
import os
from typing import Optional, Any, Dict
from datetime import datetime
import json


def get_logger(name: str, level: str = "INFO") -> logging.Logger:
    """Get a configured logger."""
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    return logger


def load_json_file(file_path: str) -> Optional[Dict[str, Any]]:
    """Load JSON file safely."""
    try:
        if not os.path.exists(file_path):
            return None

        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger = get_logger(__name__)
        logger.error(f"Failed to load JSON file {file_path}: {e}")
        return None


def save_json_file(file_path: str, data: Dict[str, Any]) -> bool:
    """Save data to JSON file safely."""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        return True
    except Exception as e:
        logger = get_logger(__name__)
        logger.error(f"Failed to save JSON file {file_path}: {e}")
        return False


def get_env_var(
    name: str, default: Optional[str] = None, required: bool = False
) -> Optional[str]:
    """Get environment variable with validation."""
    value = os.getenv(name, default)

    if required and value is None:
        raise ValueError(f"Required environment variable {name} is not set")

    return value


def format_datetime(dt: Optional[datetime] = None) -> str:
    """Format datetime to ISO string."""
    if dt is None:
        dt = datetime.now()
    return dt.isoformat()


def parse_datetime(dt_str: str) -> Optional[datetime]:
    """Parse datetime from ISO string."""
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except Exception:
        return None


def safe_int(value: Any, default: int = 0) -> int:
    """Safely convert value to int."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert value to float."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_bool(value: Any, default: bool = False) -> bool:
    """Safely convert value to bool."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        value_lower = value.lower()
        if value_lower in ("true", "1", "yes", "on"):
            return True
        elif value_lower in ("false", "0", "no", "off"):
            return False
        else:
            return default
    try:
        return bool(int(value))
    except (ValueError, TypeError):
        return default


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file operations."""
    import re

    # Remove or replace invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', "_", filename)
    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip(". ")
    # Ensure it's not empty
    if not sanitized:
        sanitized = "unnamed"
    return sanitized


def get_file_size(file_path: str) -> int:
    """Get file size in bytes."""
    try:
        return os.path.getsize(file_path)
    except (OSError, IOError):
        return 0


def ensure_dir(dir_path: str) -> bool:
    """Ensure directory exists."""
    try:
        os.makedirs(dir_path, exist_ok=True)
        return True
    except OSError:
        return False


def deep_merge(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries."""
    result = dict1.copy()

    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value

    return result


class Timer:
    """Context manager for timing operations."""

    def __init__(self, name: str = "Operation"):
        self.name = name
        self.start_time = None
        self.end_time = None
        self.logger = get_logger(__name__)

    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.debug(f"Starting {self.name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = datetime.now()
        duration = (self.end_time - self.start_time).total_seconds()
        self.logger.debug(f"{self.name} completed in {duration:.3f} seconds")

    @property
    def duration(self) -> float:
        """Get duration in seconds."""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0
