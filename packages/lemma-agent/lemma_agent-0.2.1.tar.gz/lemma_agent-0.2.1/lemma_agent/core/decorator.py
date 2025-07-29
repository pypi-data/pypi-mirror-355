"""
Main decorator system for AgentDebugger SDK.

Provides the @smart_debug decorator that instruments functions and classes
with intelligent debugging capabilities.
"""

import functools
import inspect
import asyncio
from typing import Any, Callable, Dict, Optional, Union, Type

def smart_debug(
    project_id: str = "",
    environment: str = "development", 
    trace_level: str = "basic",
    auto_fix: bool = False,
    cost_tracking: bool = True,
    **options
) -> Callable:
    """
    Main decorator for adding intelligent debugging to AI agents.
    
    This decorator can be applied to functions or classes to automatically
    instrument them with comprehensive debugging capabilities.
    
    Args:
        project_id: Unique identifier for your agent project
        environment: Environment name (development, staging, production)
        trace_level: Level of tracing detail (basic, detailed, verbose)
        auto_fix: Enable automatic fix suggestions
        cost_tracking: Track LLM API costs
        **options: Additional configuration options
    
    Usage:
        @smart_debug(project_id="my-chatbot", auto_fix=True)
        def my_agent_function(query: str) -> str:
            # Agent logic here
            pass
        
        @smart_debug(project_id="my-agent-class")
        class MyAgent:
            def chat(self, message: str) -> str:
                # Agent logic here
                pass
    
    Returns:
        Decorated function or class with debugging capabilities
    """
    def decorator(target: Union[Callable, Type]) -> Union[Callable, Type]:
        # Create decorator instance
        debug_decorator = SmartDebugDecorator(
            project_id=project_id,
            environment=environment,
            trace_level=trace_level,
            auto_fix=auto_fix,
            cost_tracking=cost_tracking,
            **options
        )
        
        return debug_decorator(target)
    
    return decorator


class SmartDebugDecorator:
    """
    Core decorator implementation that handles wrapping functions and classes
    with debugging instrumentation.
    """
    
    def __init__(
        self,
        project_id: str = "",
        environment: str = "development",
        trace_level: str = "basic", 
        auto_fix: bool = False,
        cost_tracking: bool = True,
        **options
    ):
        """
        Initialize the decorator with configuration options.
        
        Args:
            project_id: Project identifier
            environment: Environment name
            trace_level: Tracing detail level
            auto_fix: Enable automatic fix suggestions
            cost_tracking: Enable cost tracking
            **options: Additional options
        """
        # Import here to avoid circular imports
        from .config import DebugConfig
        from .tracer import ExecutionTracer
        from .collector import DataCollector
        from ..utils.logger import Logger
        
        # Create configuration
        config_dict = {
            "project_id": project_id,
            "environment": environment,
            "trace_level": trace_level,
            "auto_fix": auto_fix,
            "cost_tracking": cost_tracking,
            **options
        }
        
        # Load full configuration with overrides (merges with defaults and env vars)
        self.config = DebugConfig.load_config(override_values=config_dict)
        
        # Initialize components
        self.tracer = ExecutionTracer(self.config.get_effective_config())
        self.collector = DataCollector(self.config)
        self.logger = Logger.setup_logger(
            log_level=self.config.log_level,
            output_format=self.config.log_format
        )
        
        # Cache for wrapped methods to avoid re-wrapping
        self._wrapped_cache = {}
    
    def __call__(self, target: Union[Callable, Type]) -> Union[Callable, Type]:
        """
        Main decorator entry point that determines whether to wrap a function or class.
        
        Args:
            target: Function or class to be decorated
            
        Returns:
            Wrapped function or class with debugging
        """
        if inspect.isclass(target):
            return self._wrap_class(target)
        elif inspect.isfunction(target) or inspect.ismethod(target):
            return self._wrap_function(target)
        else:
            raise TypeError(f"@smart_debug can only decorate functions or classes, got {type(target)}")
    
    def _wrap_function(self, func: Callable) -> Callable:
        """
        Wrap a single function with debugging instrumentation.
        
        Args:
            func: Function to wrap
            
        Returns:
            Wrapped function with debugging
        """
        # Check if already wrapped
        if hasattr(func, '_agentdebugger_wrapped'):
            return func
        
        # Determine if function is async
        if asyncio.iscoroutinefunction(func):
            return self._wrap_async_function(func)
        else:
            return self._wrap_sync_function(func)
    
    def _wrap_sync_function(self, func: Callable) -> Callable:
        """
        Wrap a synchronous function with debugging.
        
        Args:
            func: Synchronous function to wrap
            
        Returns:
            Wrapped synchronous function
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Prepare context for tracing
            context = {
                "environment": self.config.environment,
                "project_id": self.config.project_id,
                "trace_level": self.config.trace_level,
                "function_module": func.__module__,
                "function_qualname": func.__qualname__
            }
            
            # Start tracing
            trace_id = self.tracer.start_trace(context, func, args, kwargs)
            
            try:
                # Log function start
                self.logger.log_debug_event(
                    "function_start",
                    {
                        "trace_id": trace_id,
                        "function_name": func.__name__,
                        "args_count": len(args),
                        "kwargs_keys": list(kwargs.keys())
                    }
                )
                
                # Execute original function
                result = func(*args, **kwargs)
                
                # End tracing with successful result
                trace_result = self.tracer.end_trace(result=result)
                
                # Collect and process data
                collected_data = self.collector.collect_execution_data(trace_result, context)
                
                # Log successful completion
                self.logger.log_debug_event(
                    "function_success",
                    {
                        "trace_id": trace_id,
                        "duration_ms": trace_result.duration_ms,
                        "steps_count": len(trace_result.steps)
                    }
                )
                
                return result
                
            except Exception as error:
                # End tracing with error
                trace_result = self.tracer.end_trace(error=error)
                
                # Collect error data
                error_data = self.collector.collect_error_data(error, context, trace_result)
                
                # Log error
                self.logger.log_debug_event(
                    "function_error",
                    {
                        "trace_id": trace_id,
                        "error_type": type(error).__name__,
                        "error_message": str(error),
                        "duration_ms": trace_result.duration_ms
                    },
                    level="ERROR"
                )
                
                # Re-raise the original exception
                raise
        
        # Mark as wrapped to prevent double-wrapping
        wrapper._agentdebugger_wrapped = True
        wrapper._agentdebugger_original = func
        wrapper._agentdebugger_config = self.config
        
        return wrapper
    
    def _wrap_async_function(self, func: Callable) -> Callable:
        """
        Wrap an asynchronous function with debugging.
        
        Args:
            func: Async function to wrap
            
        Returns:
            Wrapped async function
        """
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Prepare context for tracing
            context = {
                "environment": self.config.environment,
                "project_id": self.config.project_id,
                "trace_level": self.config.trace_level,
                "function_module": func.__module__,
                "function_qualname": func.__qualname__,
                "is_async": True
            }
            
            # Start tracing
            trace_id = self.tracer.start_trace(context, func, args, kwargs)
            
            try:
                # Log async function start
                self.logger.log_debug_event(
                    "async_function_start",
                    {
                        "trace_id": trace_id,
                        "function_name": func.__name__,
                        "args_count": len(args),
                        "kwargs_keys": list(kwargs.keys())
                    }
                )
                
                # Execute original async function
                result = await func(*args, **kwargs)
                
                # End tracing with successful result
                trace_result = self.tracer.end_trace(result=result)
                
                # Collect and process data
                collected_data = self.collector.collect_execution_data(trace_result, context)
                
                # Log successful completion
                self.logger.log_debug_event(
                    "async_function_success",
                    {
                        "trace_id": trace_id,
                        "duration_ms": trace_result.duration_ms,
                        "steps_count": len(trace_result.steps)
                    }
                )
                
                return result
                
            except Exception as error:
                # End tracing with error
                trace_result = self.tracer.end_trace(error=error)
                
                # Collect error data
                error_data = self.collector.collect_error_data(error, context, trace_result)
                
                # Log error
                self.logger.log_debug_event(
                    "async_function_error",
                    {
                        "trace_id": trace_id,
                        "error_type": type(error).__name__,
                        "error_message": str(error),
                        "duration_ms": trace_result.duration_ms
                    },
                    level="ERROR"
                )
                
                # Re-raise the original exception
                raise
        
        # Mark as wrapped
        async_wrapper._agentdebugger_wrapped = True
        async_wrapper._agentdebugger_original = func
        async_wrapper._agentdebugger_config = self.config
        
        return async_wrapper
    
    def _wrap_class(self, cls: Type) -> Type:
        """
        Wrap all eligible methods in a class with debugging.
        
        Args:
            cls: Class to wrap
            
        Returns:
            Class with wrapped methods
        """
        # Get all methods that should be wrapped
        for attr_name in dir(cls):
            if self._should_wrap_method(attr_name):
                attr = getattr(cls, attr_name)
                
                if callable(attr) and not hasattr(attr, '_agentdebugger_wrapped'):
                    # Create a new decorator instance for this method to avoid shared state
                    method_decorator = SmartDebugDecorator(
                        project_id=self.config.project_id,
                        environment=self.config.environment,
                        trace_level=self.config.trace_level,
                        auto_fix=self.config.auto_fix,
                        cost_tracking=self.config.cost_tracking
                    )
                    
                    wrapped_method = method_decorator._wrap_function(attr)
                    setattr(cls, attr_name, wrapped_method)
        
        # Mark class as wrapped
        cls._agentdebugger_wrapped = True
        cls._agentdebugger_config = self.config
        
        return cls
    
    def _should_wrap_method(self, method_name: str) -> bool:
        """
        Determine if a method should be wrapped with debugging.
        
        Args:
            method_name: Name of the method
            
        Returns:
            True if method should be wrapped
        """
        # Skip private methods (unless explicitly enabled)
        if method_name.startswith('_') and not self.config.get_effective_config().get("trace_private_methods", False):
            return False
        
        # Skip special methods
        if method_name.startswith('__') and method_name.endswith('__'):
            return False
        
        # Skip common utility methods that shouldn't be traced
        skip_methods = {
            'to_dict', 'from_dict', 'serialize', 'deserialize',
            'validate', 'copy', 'clone', '__str__', '__repr__'
        }
        
        if method_name in skip_methods:
            return False
        
        return True