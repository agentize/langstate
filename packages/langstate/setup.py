#!/usr/bin/env python3
"""Setup configuration for langstate-server package."""

from setuptools import setup, find_packages
import os


# Read README for long description
def read_readme():
    """Read README.md for long description."""
    readme_path = os.path.join(os.path.dirname(__file__), "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


# Read version from __init__.py
def read_version():
    """Read version from langstate/__init__.py."""
    version_file = os.path.join(os.path.dirname(__file__), "__init__.py")
    if os.path.exists(version_file):
        with open(version_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("__version__"):
                    return line.split("=")[1].strip().strip('"').strip("'")
    return "0.1.0"


setup(
    name="langstate",
    version=read_version(),
    author="Your Name",
    author_email="your.email@example.com",
    description="A Python library for langstate application",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/langstate",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.9",
    install_requires=[
        "pydantic>=2.0.0,<3.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0,<9.0.0",
            "pytest-asyncio>=0.21.0,<1.0.0",
            "pytest-cov>=4.0.0,<6.0.0",
        ],
        "docs": [
            "mkdocs>=1.5.0,<2.0.0",
            "mkdocs-material>=9.0.0,<10.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "langstate=langstate.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "langstate": ["py.typed", "*.pyi"],
    },
)
