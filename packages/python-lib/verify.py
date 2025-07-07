#!/usr/bin/env python3
"""
Verification script for Khandhas installation and testing.

This script helps users verify that their Khandhas installation is working correctly
and provides guidance for testing and releasing the package.
"""

import sys
import subprocess
import os
from pathlib import Path


def run_command(cmd, description, required=True):
    """Run a command and report results."""
    print(f"🔍 {description}...")
    try:
        # Use the same Python executable as the current process
        if cmd.startswith("python "):
            cmd = cmd.replace("python ", f"{sys.executable} ")
        elif cmd.startswith("khandhas "):
            # Try to find khandhas in the same environment
            khandhas_path = Path(sys.executable).parent / "khandhas"
            if khandhas_path.exists():
                cmd = cmd.replace("khandhas ", f"{khandhas_path} ")
            else:
                cmd = cmd.replace("khandhas ", f"{sys.executable} -m khandhas.cli ")
        
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print(f"  ✅ Success")
            return True
        else:
            print(f"  ❌ Failed: {result.stderr.strip()}")
            if required:
                print(f"     Command: {cmd}")
            return False
    except subprocess.TimeoutExpired:
        print(f"  ⏰ Timeout after 30 seconds")
        return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def check_python_version():
    """Check Python version compatibility."""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version >= (3, 9):
        print(f"  ✅ Python {version.major}.{version.minor}.{version.micro} (compatible)")
        return True
    else:
        print(f"  ❌ Python {version.major}.{version.minor}.{version.micro} (requires 3.9+)")
        return False


def check_package_import():
    """Check if package can be imported."""
    print("📦 Checking package import...")
    try:
        import khandhas
        print(f"  ✅ Package imported successfully")
        print(f"  📌 Version: {khandhas.__version__}")
        return True
    except ImportError as e:
        print(f"  ❌ Import failed: {e}")
        print("  💡 Try: pip install -e .")
        return False


def check_development_environment():
    """Check development environment setup."""
    print("\n🛠️  Development Environment Checks:")
    
    checks = [
        ("python -c 'import pytest'", "pytest installed"),
        ("python -c 'import black'", "black installed"),
        ("python -c 'import flake8'", "flake8 installed"),
        ("python -c 'import mypy'", "mypy installed"),
    ]
    
    passed = 0
    for cmd, desc in checks:
        if run_command(cmd, desc, required=False):
            passed += 1
    
    print(f"\n📊 Development tools: {passed}/{len(checks)} available")
    if passed < len(checks):
        print("💡 Install missing tools: pip install -e \".[dev]\"")
    
    return passed == len(checks)


def run_tests():
    """Run the test suite."""
    print("\n🧪 Running Tests:")
    
    if not Path("tests").exists():
        print("  ❌ No tests directory found")
        print("  💡 Make sure you're in the package root directory")
        return False
    
    # Basic test run
    if run_command("python -m pytest tests/ -v --tb=short", "Running test suite"):
        print("  🎉 All tests passed!")
        return True
    else:
        print("  💡 See TESTING.md for troubleshooting")
        return False


def check_code_quality():
    """Check code quality."""
    print("\n✨ Code Quality Checks:")
    
    checks = [
        ("python -m black --check .", "Code formatting (black)"),
        ("python -m flake8 .", "Linting (flake8)"),
        ("python -m mypy khandhas/", "Type checking (mypy)"),
    ]
    
    passed = 0
    for cmd, desc in checks:
        if run_command(cmd, desc, required=False):
            passed += 1
    
    print(f"\n📊 Code quality: {passed}/{len(checks)} checks passed")
    if passed < len(checks):
        print("💡 Fix issues or run: python -m black . && python -m flake8 . && python -m mypy khandhas/")
    
    return passed == len(checks)


def check_cli():
    """Check CLI functionality."""
    print("\n🖥️  CLI Checks:")
    
    checks = [
        ("khandhas version", "Version command"),
        ("khandhas --help", "Help command"),
    ]
    
    passed = 0
    for cmd, desc in checks:
        if run_command(cmd, desc, required=False):
            passed += 1
    
    return passed == len(checks)


def show_next_steps():
    """Show next steps for users."""
    print("\n🚀 Next Steps:")
    print("  📖 Read documentation:")
    print("     • TESTING.md - Comprehensive testing guide")
    print("     • RELEASE.md - Step-by-step release process")
    print("     • QUICK_REFERENCE.md - Essential commands")
    print()
    print("  🧪 Run specific tests:")
    print("     • pytest tests/test_config.py - Test configuration")
    print("     • pytest tests/test_server.py - Test server functionality")
    print("     • pytest --cov=khandhas - Test with coverage")
    print()
    print("  🚀 Release checklist:")
    print("     • Update version in khandhas/__init__.py")
    print("     • Update CHANGELOG.md")
    print("     • python -m build")
    print("     • python -m twine upload --repository testpypi dist/*")
    print("     • python -m twine upload dist/*")


def main():
    """Main verification function."""
    print("=" * 60)
    print("🔍 Khandhas Package Verification")
    print("=" * 60)
    
    # Basic checks
    all_good = True
    all_good &= check_python_version()
    all_good &= check_package_import()
    
    if not all_good:
        print("\n❌ Basic checks failed. Please fix issues before proceeding.")
        sys.exit(1)
    
    # Development environment
    dev_env = check_development_environment()
    
    # CLI checks
    cli_works = check_cli()
    
    # Test execution
    if dev_env:
        tests_pass = run_tests()
        code_quality = check_code_quality()
    else:
        print("\n⚠️  Skipping tests and code quality checks (dev tools not installed)")
        tests_pass = False
        code_quality = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Summary:")
    print(f"  🐍 Python version: {'✅' if all_good else '❌'}")
    print(f"  📦 Package import: {'✅' if all_good else '❌'}")
    print(f"  🛠️  Dev environment: {'✅' if dev_env else '❌'}")
    print(f"  🖥️  CLI tools: {'✅' if cli_works else '❌'}")
    print(f"  🧪 Tests: {'✅' if tests_pass else '❌'}")
    print(f"  ✨ Code quality: {'✅' if code_quality else '❌'}")
    print("=" * 60)
    
    if all_good and dev_env and tests_pass and code_quality:
        print("🎉 Everything looks great! You're ready to develop and release.")
    elif all_good:
        print("✅ Basic functionality works. Install dev dependencies for full testing.")
    else:
        print("❌ Some issues found. Please address them before proceeding.")
    
    show_next_steps()


if __name__ == "__main__":
    main()
