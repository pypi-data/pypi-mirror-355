"""
AgentDebugger SDK - Adapters Module

Framework-specific adapters for integrating with popular AI agent frameworks
like LangChain, CrewAI, AutoGen, and custom frameworks.
"""

from .base import BaseAdapter, FrameworkType, AdapterRegistry, detect_framework, normalize_trace_data
from .langchain import LangChainAdapter

__all__ = [
    "BaseAdapter",
    "FrameworkType", 
    "AdapterRegistry",
    "detect_framework",
    "normalize_trace_data",
    "LangChainAdapter"
]