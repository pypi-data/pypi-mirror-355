#!/usr/bin/env python3
"""Setup script for tektii-strategy-sdk."""

from pathlib import Path
from typing import Any, Dict

from setuptools import find_packages, setup

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

# Read version from __version__.py
version_file = Path(__file__).parent / "tektii_sdk" / "__version__.py"
version: Dict[str, Any] = {}
exec(version_file.read_text(), version)

setup(
    name="tektii-strategy-sdk",
    version=version["__version__"],
    author="Tektii Team",
    author_email="support@tektii.com",
    description="SDK for building and running backtest strategies on Tektii platform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tektii/tektii-strategy-sdk-python",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Office/Business :: Financial :: Investment",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "grpcio>=1.50.0",
        "grpcio-tools>=1.50.0",
        "grpcio-reflection>=1.50.0",
        "protobuf>=4.21.0",
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
        "python-dateutil>=2.8.2",
        "numpy>=1.21.0",
        "pandas>=1.3.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.11.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "pre-commit>=3.0.0",
            "requests>=2.26.0",
        ],
        "examples": [
            "ta>=0.10.0",  # Technical analysis library for examples
        ],
    },
    entry_points={
        "console_scripts": [
            "tektii=tektii_sdk.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "tektii_sdk": ["proto/*.proto"],
    },
    cmdclass={},  # Can be extended for custom commands
)
