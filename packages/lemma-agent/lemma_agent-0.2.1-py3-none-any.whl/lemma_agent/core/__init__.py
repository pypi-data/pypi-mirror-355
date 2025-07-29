"""
AgentDebugger SDK - Core Module

This module contains the core debugging functionality including:
- Main decorator system
- Execution tracing
- Data collection
- Configuration management
"""

from .decorator import smart_debug, SmartDebugDecorator
from .tracer import ExecutionTracer, TraceResult
from .collector import DataCollector, CollectedData, ErrorData, PerformanceData
from .config import DebugConfig, ValidationError

__all__ = [
    "smart_debug",
    "SmartDebugDecorator", 
    "ExecutionTracer",
    "TraceResult",
    "DataCollector",
    "CollectedData",
    "ErrorData", 
    "PerformanceData",
    "DebugConfig",
    "ValidationError"
]