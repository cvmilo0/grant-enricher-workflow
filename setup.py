#!/usr/bin/env python3
"""
Setup script for the LangGraph Subsidy Analyzer
"""

from setuptools import setup, find_packages

with open("README_langgraph.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements_langgraph.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="langgraph-subsidy-analyzer",
    version="3.0.0",
    author="DocxFormatScript 2.0",
    description="A LangGraph-based subsidy analyzer with LangSmith tracing",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'subsidy-analyzer=main_langgraph:main',
        ],
    },
)