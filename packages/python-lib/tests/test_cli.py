"""Test the CLI interface."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from khandhas.cli import create_parser, main


def test_create_parser():
    """Test CLI parser creation."""
    parser = create_parser()

    # Test default arguments
    args = parser.parse_args([])
    assert args.host == "0.0.0.0"
    assert args.port == 8000
    assert args.debug is False
    assert args.reload is False
    assert args.log_level == "INFO"

    # Test custom arguments
    args = parser.parse_args(
        [
            "--host",
            "127.0.0.1",
            "--port",
            "9000",
            "--debug",
            "--reload",
            "--log-level",
            "DEBUG",
        ]
    )
    assert args.host == "127.0.0.1"
    assert args.port == 9000
    assert args.debug is True
    assert args.reload is True
    assert args.log_level == "DEBUG"


def test_run_command():
    """Test run command parsing."""
    parser = create_parser()

    args = parser.parse_args(["run", "--workers", "4"])
    assert args.command == "run"
    assert args.workers == 4


def test_dev_command():
    """Test dev command parsing."""
    parser = create_parser()

    args = parser.parse_args(["dev", "--watch"])
    assert args.command == "dev"
    assert args.watch is True


def test_version_command():
    """Test version command parsing."""
    parser = create_parser()

    args = parser.parse_args(["version"])
    assert args.command == "version"


@patch("khandhas.cli.run_server")
def test_main_run_command(mock_run_server):
    """Test main function with run command."""
    with patch("sys.argv", ["khandhas", "run"]):
        main()
        mock_run_server.assert_called_once()


@patch("khandhas.cli.run_dev_server")
def test_main_dev_command(mock_run_dev_server):
    """Test main function with dev command."""
    with patch("sys.argv", ["khandhas", "dev"]):
        main()
        mock_run_dev_server.assert_called_once()


@patch("khandhas.cli.show_version")
def test_main_version_command(mock_show_version):
    """Test main function with version command."""
    with patch("sys.argv", ["khandhas", "version"]):
        main()
        mock_show_version.assert_called_once()


@patch("khandhas.cli.run_server")
def test_main_default_command(mock_run_server):
    """Test main function with no command (default to run)."""
    with patch("sys.argv", ["khandhas"]):
        main()
        mock_run_server.assert_called_once()


def test_show_version():
    """Test version display."""
    from khandhas.cli import show_version

    with patch("builtins.print") as mock_print:
        show_version()
        mock_print.assert_called_once()
        call_args = mock_print.call_args[0][0]
        assert "Khandhas" in call_args
        assert "0.1.0" in call_args
