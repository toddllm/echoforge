#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Setup script for EchoForge package.
"""

import os
from setuptools import setup, find_packages

# Get the long description from the README file
with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

# Read version from pyproject.toml
version = "0.2.0"

# Read dependencies from requirements.txt
install_requires = [
    "fastapi>=0.104.1",
    "uvicorn>=0.23.2",
    "pydantic>=2.4.2",
    "jinja2>=3.1.2",
    "python-multipart>=0.0.6",
    "aiofiles>=23.2.1",
    "numpy>=1.26.0",
    "soundfile>=0.12.1",
    "python-dotenv>=1.0.0",
]

# Optional dependencies
extras_require = {
    "dev": [
        "pytest>=7.4.0",
        "pytest-cov>=4.1.0",
        "black>=24.0.0",
        "isort>=5.12.0",
        "mypy>=1.8.0",
        "flake8>=7.0.0",
    ],
    "torch": [
        "torch>=2.4.0",
        "torchaudio>=2.4.0",
        "librosa>=0.10.0",
        "tokenizers>=0.21.0",
        "transformers>=4.48.0",
        "huggingface_hub>=0.28.1",
    ],
    "full": [
        "torch>=2.4.0",
        "torchaudio>=2.4.0",
        "librosa>=0.10.0",
        "tokenizers>=0.21.0",
        "transformers>=4.48.0",
        "huggingface_hub>=0.28.1",
        "moshi>=0.2.2",
        "torchtune>=0.4.0",
        "torchao>=0.9.0",
    ],
}

setup(
    name="echoforge",
    version=version,
    description="Advanced voice generation platform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="EchoForge Team",
    author_email="info@echoforge.example.com",
    url="https://github.com/yourusername/echoforge",
    packages=find_packages(exclude=["tests", "tests.*"]),
    package_data={
        "app": [
            "static/**/*",
            "templates/**/*",
        ],
    },
    include_package_data=True,
    python_requires=">=3.10",
    install_requires=install_requires,
    extras_require=extras_require,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    entry_points={
        "console_scripts": [
            "echoforge=app.main:main",
        ],
    },
) 