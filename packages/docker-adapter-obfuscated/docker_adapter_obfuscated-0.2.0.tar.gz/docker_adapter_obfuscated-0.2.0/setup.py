#!/usr/bin/env python3
"""Setup script for obfuscated Docker Adapter."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="docker-adapter-obfuscated",
    version="0.2.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A Python adapter for Docker operations (obfuscated version)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/evolvis/docker-adapter",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "docker>=7.0.0",
        "python-dotenv>=1.0.0",
        "typing-extensions>=4.7.0",
        "pydantic>=2.0.0",
    ],
    include_package_data=True,
)
