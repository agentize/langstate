"""Test the utility functions."""

import pytest
import os
import json
import tempfile
from datetime import datetime
from khandhas.utils import (
    get_logger,
    load_json_file,
    save_json_file,
    get_env_var,
    format_datetime,
    parse_datetime,
    safe_int,
    safe_float,
    safe_bool,
    sanitize_filename,
    get_file_size,
    ensure_dir,
    deep_merge,
    Timer,
)


def test_get_logger():
    """Test logger creation."""
    logger = get_logger("test_logger")

    assert logger.name == "test_logger"
    assert logger.level == 20  # INFO level

    # Test with custom level
    debug_logger = get_logger("debug_logger", "DEBUG")
    assert debug_logger.level == 10  # DEBUG level


def test_load_save_json_file():
    """Test JSON file operations."""
    test_data = {"key": "value", "number": 42, "bool": True}

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_path = f.name

    try:
        # Test save
        result = save_json_file(temp_path, test_data)
        assert result is True

        # Test load
        loaded_data = load_json_file(temp_path)
        assert loaded_data == test_data

        # Test load non-existent file
        non_existent = load_json_file("/non/existent/file.json")
        assert non_existent is None

    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_get_env_var():
    """Test environment variable handling."""
    # Test with default
    value = get_env_var("NON_EXISTENT_VAR", "default_value")
    assert value == "default_value"

    # Test with set variable
    os.environ["TEST_VAR"] = "test_value"
    try:
        value = get_env_var("TEST_VAR")
        assert value == "test_value"
    finally:
        del os.environ["TEST_VAR"]

    # Test required variable
    with pytest.raises(ValueError):
        get_env_var("REQUIRED_VAR", required=True)


def test_format_parse_datetime():
    """Test datetime formatting and parsing."""
    now = datetime.now()

    # Test format
    formatted = format_datetime(now)
    assert isinstance(formatted, str)
    assert "T" in formatted  # ISO format

    # Test parse
    parsed = parse_datetime(formatted)
    assert isinstance(parsed, datetime)
    assert parsed.year == now.year
    assert parsed.month == now.month
    assert parsed.day == now.day

    # Test parse invalid
    invalid = parse_datetime("invalid-datetime")
    assert invalid is None


def test_safe_conversions():
    """Test safe type conversions."""
    # Test safe_int
    assert safe_int("42") == 42
    assert safe_int("invalid") == 0
    assert safe_int("invalid", 99) == 99
    assert safe_int(42.7) == 42

    # Test safe_float
    assert safe_float("42.5") == 42.5
    assert safe_float("invalid") == 0.0
    assert safe_float("invalid", 99.9) == 99.9
    assert safe_float(42) == 42.0

    # Test safe_bool
    assert safe_bool("true") is True
    assert safe_bool("false") is False
    assert safe_bool("1") is True
    assert safe_bool("0") is False
    assert safe_bool("yes") is True
    assert safe_bool("no") is False
    assert safe_bool("invalid") is False
    assert safe_bool("invalid", True) is True
    assert safe_bool(1) is True
    assert safe_bool(0) is False


def test_sanitize_filename():
    """Test filename sanitization."""
    assert sanitize_filename("valid_filename.txt") == "valid_filename.txt"
    assert sanitize_filename("invalid<>filename.txt") == "invalid__filename.txt"
    assert sanitize_filename("file:with|special*chars") == "file_with_special_chars"
    assert sanitize_filename("") == "unnamed"
    assert sanitize_filename("   ") == "unnamed"
    assert sanitize_filename("...") == "unnamed"


def test_get_file_size():
    """Test file size retrieval."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("test content")
        temp_path = f.name

    try:
        size = get_file_size(temp_path)
        assert size > 0

        # Test non-existent file
        non_existent_size = get_file_size("/non/existent/file.txt")
        assert non_existent_size == 0

    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)


def test_ensure_dir():
    """Test directory creation."""
    with tempfile.TemporaryDirectory() as temp_dir:
        test_dir = os.path.join(temp_dir, "test", "nested", "dir")

        result = ensure_dir(test_dir)
        assert result is True
        assert os.path.exists(test_dir)
        assert os.path.isdir(test_dir)


def test_deep_merge():
    """Test deep dictionary merging."""
    dict1 = {"a": 1, "b": {"c": 2, "d": 3}, "e": [1, 2, 3]}

    dict2 = {"a": 10, "b": {"c": 20, "f": 4}, "g": 5}

    result = deep_merge(dict1, dict2)

    assert result["a"] == 10  # Overwritten
    assert result["b"]["c"] == 20  # Overwritten
    assert result["b"]["d"] == 3  # Preserved
    assert result["b"]["f"] == 4  # Added
    assert result["e"] == [1, 2, 3]  # Preserved
    assert result["g"] == 5  # Added


def test_timer():
    """Test Timer context manager."""
    import time

    with Timer("test_operation") as timer:
        time.sleep(0.1)  # Sleep for 100ms

    assert timer.duration >= 0.1
    assert timer.duration < 0.2  # Should be close to 0.1 seconds
