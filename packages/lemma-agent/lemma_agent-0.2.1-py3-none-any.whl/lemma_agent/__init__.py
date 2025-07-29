"""
AgentDebugger SDK - The GitHub Copilot for AI Agent Development

AgentDebugger Pro is an intelligent debugging platform that understands,
fixes, and optimizes AI agents automatically. Just add @smart_debug to any
agent function or class to get comprehensive debugging capabilities.

Example usage:
    @smart_debug(project_id="my-chatbot", auto_fix=True)
    def my_agent_function(query: str) -> str:
        # Your agent logic here
        return response

    @smart_debug(project_id="my-agent-class")
    class MyAgent:
        def chat(self, message: str) -> str:
            # Agent logic here
            return response
"""

import os
from typing import Optional, Dict, Any

from .core import smart_debug, DebugConfig, ExecutionTracer, DataCollector
from .utils import Logger, validate_debug_config
from .adapters import BaseAdapter, FrameworkType, detect_framework, normalize_trace_data

# Version information
__version__ = "0.2.1"
__author__ = "Lemma Team"
__email__ = "shinojcm01@gmail.com"
__description__ = "The GitHub Copilot for AI Agent Development"

# Main exports that users will typically use
__all__ = [
    # Core decorator - main user interface
    "smart_debug",
    
    # Configuration and setup
    "DebugConfig",
    
    # Advanced components for power users
    "ExecutionTracer",
    "DataCollector",
    "Logger",
    
    # Validation utilities
    "validate_debug_config",
    
    # Framework integration
    "BaseAdapter",
    "FrameworkType", 
    "detect_framework",
    "normalize_trace_data",
    
    # Version info
    "__version__"
]

# Initialize adapter registry with built-in adapters
def _initialize_adapters():
    """Initialize the adapter registry with built-in framework adapters."""
    from .adapters.base import adapter_registry
    from .adapters.langchain import LangChainAdapter
    
    # Register LangChain adapter
    adapter_registry.register_adapter(FrameworkType.LANGCHAIN, LangChainAdapter)
    
    # TODO: Register other adapters as they're implemented
    # adapter_registry.register_adapter(FrameworkType.CREWAI, CrewAIAdapter)
    # adapter_registry.register_adapter(FrameworkType.AUTOGEN, AutoGenAdapter)

# Initialize adapters when module is imported
_initialize_adapters()

# Convenience functions for common operations
def get_version() -> str:
    """Get the AgentDebugger SDK version."""
    return __version__

def setup_logging(level: str = "INFO", format: str = "json") -> Logger:
    """
    Quick setup for AgentDebugger logging.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format: Log format (json, text, colored)
        
    Returns:
        Configured Logger instance
    """
    return Logger.setup_logger(log_level=level, output_format=format)

def create_config(project_id: str, **kwargs) -> DebugConfig:
    """
    Create a new debug configuration.
    
    Args:
        project_id: Unique project identifier
        **kwargs: Additional configuration options
        
    Returns:
        DebugConfig instance
    """
    config_dict = {"project_id": project_id, **kwargs}
    
    # Use the new override_values parameter to pass our config
    return DebugConfig.load_config(override_values=config_dict)

# Module-level configuration for default behavior
_default_config = None

def set_default_config(config: DebugConfig) -> None:
    """
    Set a default configuration for all @smart_debug decorators.
    
    Args:
        config: DebugConfig to use as default
    """
    global _default_config
    _default_config = config

def get_default_config() -> Optional[DebugConfig]:
    """Get the current default configuration."""
    return _default_config

# Quick start function for new users
def quick_start(project_id: str, environment: str = "development") -> None:
    """
    Quick start setup for AgentDebugger.
    
    Sets up logging and default configuration for immediate use.
    
    Args:
        project_id: Your project identifier
        environment: Environment name (development, staging, production)
    """
    # Setup logging
    log_format = "colored" if environment == "development" else "json"
    setup_logging(level="INFO", format=log_format)
    
    # Create and set default config
    config = create_config(
        project_id=project_id,
        environment=environment,
        trace_level="basic" if environment == "production" else "detailed"
    )
    set_default_config(config)
    
    print(f"✅ AgentDebugger initialized for project '{project_id}' in {environment} mode")
    print(f"📝 Add @smart_debug to your agent functions to start debugging")
    
    if environment == "development":
        print(f"💡 Try: @smart_debug(project_id='{project_id}', trace_level='verbose') for detailed tracing")

# Health check function
def health_check() -> Dict[str, Any]:
    """
    Perform a health check of the AgentDebugger SDK.
    
    Returns:
        Dictionary with health status and component information
    """
    health_status = {
        "status": "healthy",
        "version": __version__,
        "components": {},
        "adapters": {},
        "issues": []
    }
    
    # Check core components
    try:
        from .core import smart_debug, DebugConfig, ExecutionTracer, DataCollector
        health_status["components"]["core"] = "available"
    except ImportError as e:
        health_status["components"]["core"] = f"error: {e}"
        health_status["issues"].append(f"Core module import failed: {e}")
    
    # Check utils
    try:
        from .utils import Logger, validate_debug_config
        health_status["components"]["utils"] = "available"
    except ImportError as e:
        health_status["components"]["utils"] = f"error: {e}"
        health_status["issues"].append(f"Utils module import failed: {e}")
    
    # Check adapters
    try:
        from .adapters import BaseAdapter, detect_framework
        from .adapters.base import adapter_registry
        
        health_status["components"]["adapters"] = "available"
        
        # Check registered adapters
        for framework_type in FrameworkType:
            adapter_class = adapter_registry._adapters.get(framework_type)
            if adapter_class:
                health_status["adapters"][framework_type.value] = "registered"
            else:
                health_status["adapters"][framework_type.value] = "not_registered"
                
    except ImportError as e:
        health_status["components"]["adapters"] = f"error: {e}"
        health_status["issues"].append(f"Adapters module import failed: {e}")
    
    # Check optional dependencies
    optional_deps = {
        "langchain": "LangChain framework support",
        "crewai": "CrewAI framework support", 
        "autogen": "AutoGen framework support",
        "msgpack": "MessagePack serialization",
        "yaml": "YAML configuration support"
    }
    
    health_status["optional_dependencies"] = {}
    for dep, description in optional_deps.items():
        try:
            __import__(dep)
            health_status["optional_dependencies"][dep] = "available"
        except ImportError:
            health_status["optional_dependencies"][dep] = "not_available"
    
    # Overall status
    if health_status["issues"]:
        health_status["status"] = "degraded"
    
    return health_status

# Import guard for optional dependencies
def _safe_import(module_name: str, feature_name: str = None):
    """Safely import optional dependencies with helpful error messages."""
    try:
        return __import__(module_name)
    except ImportError:
        feature = feature_name or module_name
        raise ImportError(
            f"Optional dependency '{module_name}' not found. "
            f"Install it to use {feature}: pip install {module_name}"
        )

# Module initialization message
def _print_welcome():
    """Print welcome message when module is first imported."""
    # Only show welcome in interactive environments  
    if hasattr(__builtins__, '__IPYTHON__') or os.getenv('JUPYTER_CORE_PATHS'):
        print("🚀 AgentDebugger SDK loaded - The GitHub Copilot for AI Agent Development")
        print("📖 Quick start: agentdebugger.quick_start('your-project-id')")
        print("📚 Docs: https://docs.agentdebugger.pro")

# Show welcome message on first import (can be disabled with env var)
if not os.getenv('AGENTDEBUGGER_QUIET'):
    _print_welcome()