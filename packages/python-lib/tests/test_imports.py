"""Test package imports."""


def test_package_imports():
    """Test that all main components can be imported."""
    from khandhas import KhandhasServer, Config, BaseModel, ResponseModel, get_logger

    # Test that classes are available
    assert KhandhasServer is not None
    assert Config is not None
    assert BaseModel is not None
    assert ResponseModel is not None
    assert get_logger is not None


def test_version_import():
    """Test that version can be imported."""
    from khandhas import __version__

    assert __version__ == "0.1.0"


def test_package_attributes():
    """Test that package attributes are available."""
    import khandhas

    assert hasattr(khandhas, "KhandhasServer")
    assert hasattr(khandhas, "Config")
    assert hasattr(khandhas, "BaseModel")
    assert hasattr(khandhas, "ResponseModel")
    assert hasattr(khandhas, "get_logger")

    assert hasattr(khandhas, "__version__")
    assert hasattr(khandhas, "__author__")
    assert hasattr(khandhas, "__email__")


def test_submodule_imports():
    """Test that submodules can be imported."""
    from khandhas import config, server, models, utils, cli

    assert config is not None
    assert server is not None
    assert models is not None
    assert utils is not None
    assert cli is not None
