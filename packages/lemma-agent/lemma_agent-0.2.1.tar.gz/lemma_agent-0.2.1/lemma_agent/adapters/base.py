"""
Base adapter system for AgentDebugger SDK.

Provides the foundation for framework-specific adapters and automatic
framework detection capabilities.
"""

import inspect
import sys
from typing import Any, Dict, List, Optional, Type, Union
from enum import Enum
from dataclasses import dataclass
from abc import ABC, abstractmethod


class FrameworkType(Enum):
    """Enumeration of supported AI frameworks."""
    LANGCHAIN = "langchain"
    CREWAI = "crewai" 
    AUTOGEN = "autogen"
    CUSTOM = "custom"
    UNKNOWN = "unknown"


@dataclass
class FrameworkInfo:
    """Information about a detected framework."""
    framework_type: FrameworkType
    version: Optional[str] = None
    confidence: float = 0.0  # 0.0 to 1.0
    detected_modules: List[str] = None
    agent_class: Optional[str] = None
    
    def __post_init__(self):
        if self.detected_modules is None:
            self.detected_modules = []


@dataclass
class NormalizedTrace:
    """Normalized trace data format for cross-framework compatibility."""
    trace_id: str
    framework_type: str
    agent_type: str
    execution_steps: List[Dict[str, Any]]
    performance_metrics: Dict[str, Any]
    framework_specific_data: Dict[str, Any]
    metadata: Dict[str, Any]


class BaseAdapter(ABC):
    """
    Abstract base class for framework-specific adapters.
    
    All framework adapters should inherit from this class and implement
    the required methods for their specific framework.
    """
    
    def __init__(self, debug_config: Dict[str, Any]):
        """
        Initialize the adapter with debug configuration.
        
        Args:
            debug_config: Configuration dictionary for debugging
        """
        self.debug_config = debug_config
        self.framework_info: Optional[FrameworkInfo] = None
    
    @abstractmethod
    def detect_framework(self, agent_instance: Any) -> FrameworkInfo:
        """
        Detect if this adapter can handle the given agent instance.
        
        Args:
            agent_instance: Agent instance to analyze
            
        Returns:
            FrameworkInfo with detection results
        """
        pass
    
    @abstractmethod
    def normalize_trace_data(self, raw_trace_data: Dict[str, Any], 
                           framework_type: FrameworkType) -> NormalizedTrace:
        """
        Convert framework-specific trace data to normalized format.
        
        Args:
            raw_trace_data: Raw trace data from execution
            framework_type: Type of framework that generated the data
            
        Returns:
            Normalized trace data
        """
        pass
    
    @abstractmethod
    def get_framework_hooks(self) -> Dict[str, Any]:
        """
        Get framework-specific hooks for instrumenting agent execution.
        
        Returns:
            Dictionary of hook functions and configuration
        """
        pass
    
    def is_compatible(self, agent_instance: Any) -> bool:
        """
        Check if this adapter is compatible with the agent instance.
        
        Args:
            agent_instance: Agent instance to check
            
        Returns:
            True if compatible, False otherwise
        """
        framework_info = self.detect_framework(agent_instance)
        return framework_info.confidence > 0.5
    
    def extract_agent_metadata(self, agent_instance: Any) -> Dict[str, Any]:
        """
        Extract metadata from an agent instance.
        
        Args:
            agent_instance: Agent instance to analyze
            
        Returns:
            Dictionary of agent metadata
        """
        metadata = {
            "agent_class": agent_instance.__class__.__name__,
            "agent_module": agent_instance.__class__.__module__,
            "has_memory": self._check_for_memory(agent_instance),
            "has_tools": self._check_for_tools(agent_instance),
            "methods": self._get_public_methods(agent_instance)
        }
        
        return metadata
    
    def _check_for_memory(self, agent_instance: Any) -> bool:
        """Check if agent has memory capabilities."""
        memory_indicators = [
            "memory", "chat_memory", "conversation_memory", 
            "history", "context", "state"
        ]
        
        for attr in dir(agent_instance):
            if any(indicator in attr.lower() for indicator in memory_indicators):
                return True
        
        return False
    
    def _check_for_tools(self, agent_instance: Any) -> bool:
        """Check if agent has tool/function calling capabilities."""
        tool_indicators = [
            "tools", "functions", "tool_call", "function_call",
            "available_tools", "tool_manager"
        ]
        
        for attr in dir(agent_instance):
            if any(indicator in attr.lower() for indicator in tool_indicators):
                return True
        
        return False
    
    def _get_public_methods(self, agent_instance: Any) -> List[str]:
        """Get list of public methods on the agent."""
        methods = []
        for name, method in inspect.getmembers(agent_instance, predicate=inspect.ismethod):
            if not name.startswith('_'):
                methods.append(name)
        
        return methods


class AdapterRegistry:
    """
    Registry for managing framework adapters and automatic detection.
    """
    
    def __init__(self):
        """Initialize the adapter registry."""
        self._adapters: Dict[FrameworkType, Type[BaseAdapter]] = {}
        self._detection_cache: Dict[str, FrameworkInfo] = {}
    
    def register_adapter(self, framework_type: FrameworkType, 
                        adapter_class: Type[BaseAdapter]) -> None:
        """
        Register an adapter for a specific framework.
        
        Args:
            framework_type: Framework type this adapter handles
            adapter_class: Adapter class to register
        """
        self._adapters[framework_type] = adapter_class
    
    def detect_framework(self, agent_instance: Any) -> FrameworkInfo:
        """
        Automatically detect which framework an agent instance uses.
        
        Args:
            agent_instance: Agent instance to analyze
            
        Returns:
            FrameworkInfo with best detection match
        """
        # Check cache first
        cache_key = f"{agent_instance.__class__.__module__}.{agent_instance.__class__.__name__}"
        if cache_key in self._detection_cache:
            return self._detection_cache[cache_key]
        
        best_match = FrameworkInfo(FrameworkType.UNKNOWN)
        
        # Try each registered adapter
        for framework_type, adapter_class in self._adapters.items():
            try:
                adapter = adapter_class({})
                framework_info = adapter.detect_framework(agent_instance)
                
                if framework_info.confidence > best_match.confidence:
                    best_match = framework_info
                    
            except Exception:
                # Adapter detection failed, continue with others
                continue
        
        # If no specific adapter matched, try generic detection
        if best_match.framework_type == FrameworkType.UNKNOWN:
            best_match = self._generic_framework_detection(agent_instance)
        
        # Cache the result
        self._detection_cache[cache_key] = best_match
        
        return best_match
    
    def create_adapter(self, framework_type: FrameworkType, 
                      debug_config: Dict[str, Any]) -> Optional[BaseAdapter]:
        """
        Create an adapter instance for the specified framework.
        
        Args:
            framework_type: Type of framework adapter to create
            debug_config: Configuration for the adapter
            
        Returns:
            Adapter instance or None if not available
        """
        adapter_class = self._adapters.get(framework_type)
        if adapter_class:
            return adapter_class(debug_config)
        
        return None
    
    def get_best_adapter(self, agent_instance: Any, 
                        debug_config: Dict[str, Any]) -> Optional[BaseAdapter]:
        """
        Get the best adapter for an agent instance.
        
        Args:
            agent_instance: Agent instance to analyze
            debug_config: Configuration for the adapter
            
        Returns:
            Best matching adapter instance or None
        """
        framework_info = self.detect_framework(agent_instance)
        
        if framework_info.confidence > 0.5:
            return self.create_adapter(framework_info.framework_type, debug_config)
        
        return None
    
    def normalize_trace_data(self, raw_trace_data: Dict[str, Any], 
                           framework_type: FrameworkType) -> NormalizedTrace:
        """
        Normalize trace data using the appropriate adapter.
        
        Args:
            raw_trace_data: Raw trace data to normalize
            framework_type: Framework that generated the data
            
        Returns:
            Normalized trace data
        """
        adapter = self.create_adapter(framework_type, {})
        if adapter:
            return adapter.normalize_trace_data(raw_trace_data, framework_type)
        
        # Fallback to generic normalization
        return self._generic_normalize_trace_data(raw_trace_data, framework_type)
    
    def _generic_framework_detection(self, agent_instance: Any) -> FrameworkInfo:
        """
        Generic framework detection using module analysis.
        
        Args:
            agent_instance: Agent instance to analyze
            
        Returns:
            FrameworkInfo with detection results
        """
        module_name = agent_instance.__class__.__module__
        class_name = agent_instance.__class__.__name__
        
        # Check for LangChain
        if "langchain" in module_name.lower():
            return FrameworkInfo(
                framework_type=FrameworkType.LANGCHAIN,
                confidence=0.8,
                detected_modules=[module_name],
                agent_class=class_name
            )
        
        # Check for CrewAI
        if "crewai" in module_name.lower() or "crew" in class_name.lower():
            return FrameworkInfo(
                framework_type=FrameworkType.CREWAI,
                confidence=0.8,
                detected_modules=[module_name],
                agent_class=class_name
            )
        
        # Check for AutoGen
        if "autogen" in module_name.lower() or any(
            keyword in class_name.lower() for keyword in ["autogen", "conversable"]
        ):
            return FrameworkInfo(
                framework_type=FrameworkType.AUTOGEN,
                confidence=0.8,
                detected_modules=[module_name],
                agent_class=class_name
            )
        
        # Check imported modules for framework indicators
        framework_modules = self._scan_imported_modules()
        
        if any("langchain" in mod for mod in framework_modules):
            return FrameworkInfo(
                framework_type=FrameworkType.LANGCHAIN,
                confidence=0.6,
                detected_modules=framework_modules,
                agent_class=class_name
            )
        
        if any("crewai" in mod for mod in framework_modules):
            return FrameworkInfo(
                framework_type=FrameworkType.CREWAI,
                confidence=0.6,
                detected_modules=framework_modules,
                agent_class=class_name
            )
        
        if any("autogen" in mod for mod in framework_modules):
            return FrameworkInfo(
                framework_type=FrameworkType.AUTOGEN,
                confidence=0.6,
                detected_modules=framework_modules,
                agent_class=class_name
            )
        
        # Default to custom if we can't identify
        return FrameworkInfo(
            framework_type=FrameworkType.CUSTOM,
            confidence=0.3,
            detected_modules=[module_name],
            agent_class=class_name
        )
    
    def _scan_imported_modules(self) -> List[str]:
        """Scan currently imported modules for framework indicators."""
        relevant_modules = []
        
        framework_keywords = [
            "langchain", "crewai", "autogen", "openai", "anthropic",
            "transformers", "huggingface", "llamaindex"
        ]
        
        for module_name in sys.modules.keys():
            if any(keyword in module_name.lower() for keyword in framework_keywords):
                relevant_modules.append(module_name)
        
        return relevant_modules
    
    def _generic_normalize_trace_data(self, raw_trace_data: Dict[str, Any], 
                                    framework_type: FrameworkType) -> NormalizedTrace:
        """
        Generic trace data normalization for unknown frameworks.
        
        Args:
            raw_trace_data: Raw trace data
            framework_type: Framework type
            
        Returns:
            Normalized trace data
        """
        return NormalizedTrace(
            trace_id=raw_trace_data.get("trace_id", "unknown"),
            framework_type=framework_type.value,
            agent_type=raw_trace_data.get("function_name", "unknown"),
            execution_steps=raw_trace_data.get("steps", []),
            performance_metrics={
                "duration_ms": raw_trace_data.get("duration_ms", 0),
                "memory_usage": raw_trace_data.get("memory_growth_mb", 0)
            },
            framework_specific_data=raw_trace_data,
            metadata={
                "environment": raw_trace_data.get("environment", "unknown"),
                "normalized_by": "generic_adapter"
            }
        )


# Global adapter registry instance
adapter_registry = AdapterRegistry()


def detect_framework(agent_instance: Any) -> FrameworkInfo:
    """
    Convenience function for framework detection.
    
    Args:
        agent_instance: Agent instance to analyze
        
    Returns:
        FrameworkInfo with detection results
    """
    return adapter_registry.detect_framework(agent_instance)


def normalize_trace_data(raw_trace_data: Dict[str, Any], 
                        framework_type: FrameworkType) -> NormalizedTrace:
    """
    Convenience function for trace data normalization.
    
    Args:
        raw_trace_data: Raw trace data to normalize
        framework_type: Framework that generated the data
        
    Returns:
        Normalized trace data
    """
    return adapter_registry.normalize_trace_data(raw_trace_data, framework_type)