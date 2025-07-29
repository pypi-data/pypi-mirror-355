#!/usr/bin/env python3
"""
Setup configuration for AgentDebugger SDK
"""
import os
import re
from setuptools import setup, find_packages

# Read version from __init__.py
def get_version():
    """Extract version from __init__.py"""
    init_py = os.path.join(os.path.dirname(__file__), 'lemma_agent', '__init__.py')
    with open(init_py, 'r', encoding='utf-8') as f:
        content = f.read()
        match = re.search(r'__version__ = ["\']([^"\']+)["\']', content)
        if match:
            return match.group(1)
    raise RuntimeError('Unable to find version string.')

# Read long description from README
def get_long_description():
    """Read long description from README file"""
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "The GitHub Copilot for AI Agent Development"

# Read requirements from requirements.txt
def get_requirements():
    """Read requirements from requirements.txt"""
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    if os.path.exists(requirements_path):
        with open(requirements_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return []

setup(
    # Basic package info
    name="lemma_agent",
    version=get_version(),
    author="Lemma Team",
    author_email="shinojcm01@gmail.com",
    description="The GitHub Copilot for AI Agent Development - Intelligent debugging for AI agents",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/fridayowl/Lemma",
    project_urls={
        "Documentation": "https://github.com/fridayowl/Lemma",
        "Source": "https://github.com/fridayowl/Lemma",
        "Tracker": "https://github.com/fridayowl/Lemma/issues",
        "Pitch Deck": "https://github.com/fridayowl/Lemma",
        "Demo": "https://github.com/fridayowl/Lemma",
    },
    
    # Package discovery
    packages=find_packages(exclude=['tests*', 'docs*', 'examples*']),
    include_package_data=True,
    
    # Python version requirements
    python_requires=">=3.8",
    
    # Core dependencies
    install_requires=[
        # Core functionality
        "typing-extensions>=4.0.0",
        "dataclasses-json>=0.5.7",
        "pydantic>=1.8.0",
        
        # Logging and serialization
        "structlog>=21.1.0",
        "msgpack>=1.0.0",
        
        # HTTP client for API integration
        "httpx>=0.24.0",
        "aiohttp>=3.8.0",
        
        # Configuration
        "pyyaml>=6.0",
        "python-dotenv>=0.19.0",
        
        # Performance monitoring
        "psutil>=5.8.0",
        
        # Token counting
        "tiktoken>=0.4.0",
    ],
    
    # Optional dependencies grouped by feature
    extras_require={
        # Framework adapters
        "langchain": [
            "langchain>=0.1.0",
            "langchain-core>=0.1.0",
        ],
        "crewai": [
            "crewai>=0.1.0",
        ],
        "autogen": [
            "pyautogen>=0.1.0",
        ],
        
        # Development tools
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "isort>=5.10.0",
            "flake8>=4.0.0",
            "mypy>=0.991",
            "pre-commit>=2.20.0",
        ],
        
        # Documentation
        "docs": [
            "sphinx>=4.5.0",
            "sphinx-rtd-theme>=1.0.0",
            "myst-parser>=0.17.0",
        ],
        
        # All optional dependencies
        "all": [
            "langchain>=0.1.0",
            "langchain-core>=0.1.0",
            "crewai>=0.1.0",
            "pyautogen>=0.1.0",
        ],
        
        # Enterprise features
        "enterprise": [
            "cryptography>=3.4.0",
            "jwt>=1.3.0",
            "redis>=4.0.0",
        ],
    },
    
    # Entry points for CLI tools
    entry_points={
        "console_scripts": [
            "lemma_agent=lemma_agent.cli:main",
            "lemma-agent=lemma_agent.cli:main", 
        ],
    },
    
    # Package classification
    classifiers=[
        # Development Status
        "Development Status :: 4 - Beta",
        
        # Intended Audience
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        
        # Topic
        "Topic :: Software Development :: Debuggers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        
        # License
        "License :: OSI Approved :: MIT License",
        
        # Python versions
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        
        # Operating System
        "Operating System :: OS Independent",
        
        # Framework
        "Framework :: AsyncIO",
    ],
    
    # Keywords for discovery
    keywords=[
        "ai", "lemma", "agents", "debugging", "llm", "langchain", "crewai", "autogen",
        "artificial-intelligence", "machine-learning", "development-tools",
        "productivity", "automation", "chatbots", "conversational-ai"
    ],
    
    # Package data
    package_data={
        "lemma_agent": [
            "py.typed",  # Mark as typed package
            "config/*.yaml",
            "templates/*.json",
        ],
    },
    
    # Zip safety
    zip_safe=False,
    
    # Test suite
    test_suite="tests",
)