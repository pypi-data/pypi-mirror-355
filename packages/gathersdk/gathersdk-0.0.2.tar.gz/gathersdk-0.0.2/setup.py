#!/usr/bin/env python
"""Setup script for GatherChat Agent SDK"""

from setuptools import setup, find_packages
import os

# Read the README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="gathersdk",
    version="0.0.2",
    author="GatherChat Team",
    author_email="sdk@gatherchat.com",
    description="Python SDK for building GatherChat agents",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/gatherchat/gatherchat-agent-sdk",
    project_urls={
        "Bug Reports": "https://github.com/gatherchat/gatherchat-agent-sdk/issues",
        "Source": "https://github.com/gatherchat/gatherchat-agent-sdk",
        "Documentation": "https://docs.gatherchat.com/sdk",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "aiohttp>=3.8.0",
        "pydantic>=2.0.0",
        "python-dotenv>=0.19.0",
        "pydantic-ai>=0.0.1",
        "click>=8.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=22.0.0",
            "isort>=5.10.0",
            "mypy>=1.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "gathersdk=gatherchat_agent_sdk.cli:main",
        ],
    },
    keywords="gatherchat gathersdk agent chatbot websocket async",
)