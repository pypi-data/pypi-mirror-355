"""
Execution tracing functionality for AgentDebugger SDK.

Captures detailed information about agent execution including timing,
performance metrics, system state, and step-by-step execution flow.
"""

import time
import uuid
import traceback
import threading
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from contextlib import contextmanager
import sys
import gc

# Try to import psutil, but make it optional for system monitoring
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


@dataclass
class TraceStep:
    """Represents a single step in agent execution."""
    step_id: str
    step_name: str
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    step_data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[Exception] = None
    memory_usage_mb: Optional[float] = None


@dataclass
class SystemState:
    """Captures system state at a point in time."""
    timestamp: float
    memory_usage_mb: float
    cpu_percent: float
    thread_count: int
    process_id: int
    python_version: str
    gc_stats: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TraceResult:
    """Complete trace result for an agent execution."""
    trace_id: str
    function_name: str
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    
    # Function execution details
    args: List[Any] = field(default_factory=list)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    result: Any = None
    error: Optional[Exception] = None
    error_traceback: Optional[str] = None
    
    # Performance metrics
    initial_state: Optional[SystemState] = None
    final_state: Optional[SystemState] = None
    peak_memory_mb: Optional[float] = None
    memory_growth_mb: Optional[float] = None
    
    # Execution flow
    steps: List[TraceStep] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    environment: str = "development"
    framework_type: Optional[str] = None
    agent_type: Optional[str] = None
    
    def is_successful(self) -> bool:
        """Check if the execution was successful."""
        return self.error is None
    
    def get_total_duration_ms(self) -> float:
        """Get total execution duration in milliseconds."""
        if self.duration_ms is not None:
            return self.duration_ms
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time) * 1000
        return 0.0
    
    def get_step_summary(self) -> Dict[str, Any]:
        """Get summary of execution steps."""
        return {
            "total_steps": len(self.steps),
            "successful_steps": len([s for s in self.steps if s.error is None]),
            "failed_steps": len([s for s in self.steps if s.error is not None]),
            "total_step_duration_ms": sum(s.duration_ms or 0 for s in self.steps),
            "longest_step": max(self.steps, key=lambda s: s.duration_ms or 0).step_name if self.steps else None
        }


class ExecutionTracer:
    """
    Main execution tracer that captures comprehensive information about agent execution.
    Thread-safe and designed for minimal performance overhead.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the execution tracer.
        
        Args:
            config: Configuration dictionary with tracing options
        """
        self.config = config or {}
        self.current_trace: Optional[TraceResult] = None
        self.trace_stack: List[TraceResult] = []
        self.lock = threading.RLock()
        
        # Configuration options
        self.capture_parameters = self.config.get("capture_parameters", True)
        self.capture_results = self.config.get("capture_results", True)
        self.memory_tracking = self.config.get("memory_tracking", True)
        self.step_tracking = self.config.get("step_tracking", True)
        self.max_parameter_size = self.config.get("max_parameter_size", 10000)
        self.timing_precision = self.config.get("timing_precision", "milliseconds")
        
        # Performance monitoring
        if HAS_PSUTIL:
            try:
                self.process = psutil.Process()
            except Exception:
                self.process = None
        else:
            self.process = None
        
    def start_trace(self, context: Dict[str, Any], func: Callable, 
                   args: tuple, kwargs: Dict[str, Any]) -> str:
        """
        Begin execution tracing for a function call.
        
        Args:
            context: Additional context information
            func: Function being traced
            args: Function positional arguments
            kwargs: Function keyword arguments
            
        Returns:
            Unique trace ID
        """
        with self.lock:
            trace_id = self._generate_trace_id()
            
            # Create new trace result
            trace = TraceResult(
                trace_id=trace_id,
                function_name=func.__name__,
                start_time=time.time(),
                environment=context.get("environment", "development"),
                framework_type=context.get("framework_type"),
                agent_type=context.get("agent_type"),
                context=context.copy()
            )
            
            # Capture function parameters if enabled
            if self.capture_parameters:
                trace.args = self._serialize_parameters(args)
                trace.kwargs = self._serialize_parameters(kwargs)
            
            # Capture initial system state
            if self.memory_tracking:
                trace.initial_state = self._capture_system_state()
            
            # Set as current trace
            if self.current_trace:
                self.trace_stack.append(self.current_trace)
            self.current_trace = trace
            
            return trace_id
    
    def end_trace(self, result: Any = None, error: Optional[Exception] = None) -> TraceResult:
        """
        Complete execution tracing and calculate final metrics.
        
        Args:
            result: Function execution result
            error: Exception if function failed
            
        Returns:
            Complete trace result
        """
        with self.lock:
            if not self.current_trace:
                raise RuntimeError("No active trace to end")
            
            trace = self.current_trace
            trace.end_time = time.time()
            trace.duration_ms = (trace.end_time - trace.start_time) * 1000
            
            # Store result or error
            if error:
                trace.error = error
                trace.error_traceback = traceback.format_exc()
            elif self.capture_results:
                trace.result = self._serialize_parameters(result)
            
            # Capture final system state and calculate metrics
            if self.memory_tracking and trace.initial_state:
                trace.final_state = self._capture_system_state()
                trace.memory_growth_mb = (
                    trace.final_state.memory_usage_mb - trace.initial_state.memory_usage_mb
                )
                
                # Calculate peak memory usage from steps
                step_memory_values = [s.memory_usage_mb for s in trace.steps if s.memory_usage_mb]
                if step_memory_values:
                    trace.peak_memory_mb = max(step_memory_values)
                else:
                    trace.peak_memory_mb = trace.final_state.memory_usage_mb
            
            # Restore previous trace from stack
            if self.trace_stack:
                self.current_trace = self.trace_stack.pop()
            else:
                self.current_trace = None
            
            return trace
    
    def capture_step(self, step_name: str, step_data: Dict[str, Any] = None, 
                    metadata: Dict[str, Any] = None) -> str:
        """
        Capture an individual execution step within the agent flow.
        
        Args:
            step_name: Descriptive name for this step
            step_data: Data associated with this step
            metadata: Additional metadata for this step
            
        Returns:
            Unique step ID
        """
        if not self.step_tracking or not self.current_trace:
            return ""
        
        with self.lock:
            step_id = self._generate_trace_id()
            
            step = TraceStep(
                step_id=step_id,
                step_name=step_name,
                start_time=time.time(),
                step_data=step_data or {},
                metadata=metadata or {}
            )
            
            # Capture memory usage if enabled
            if self.memory_tracking:
                step.memory_usage_mb = self._get_memory_usage()
            
            self.current_trace.steps.append(step)
            return step_id
    
    def complete_step(self, step_id: str, result_data: Dict[str, Any] = None, 
                     error: Optional[Exception] = None) -> None:
        """
        Mark a step as completed and record final timing.
        
        Args:
            step_id: ID of the step to complete
            result_data: Result data from the step
            error: Exception if step failed
        """
        if not self.current_trace:
            return
        
        with self.lock:
            # Find the step in current trace
            for step in self.current_trace.steps:
                if step.step_id == step_id:
                    step.end_time = time.time()
                    step.duration_ms = (step.end_time - step.start_time) * 1000
                    
                    if error:
                        step.error = error
                    elif result_data:
                        step.step_data.update(result_data)
                    
                    break
    
    @contextmanager
    def trace_step(self, step_name: str, step_data: Dict[str, Any] = None):
        """
        Context manager for tracing a step with automatic completion.
        
        Args:
            step_name: Name of the step
            step_data: Initial step data
            
        Usage:
            with tracer.trace_step("API Call", {"endpoint": "/chat"}):
                result = api.call()
        """
        step_id = self.capture_step(step_name, step_data)
        try:
            yield step_id
            self.complete_step(step_id)
        except Exception as e:
            self.complete_step(step_id, error=e)
            raise
    
    def add_context(self, key: str, value: Any) -> None:
        """
        Add contextual information to the current trace.
        
        Args:
            key: Context key
            value: Context value
        """
        if self.current_trace:
            with self.lock:
                self.current_trace.context[key] = value
    
    def get_current_trace(self) -> Optional[TraceResult]:
        """Get the currently active trace."""
        return self.current_trace
    
    def _generate_trace_id(self) -> str:
        """Generate a unique trace ID."""
        return str(uuid.uuid4())
    
    def _capture_system_state(self) -> SystemState:
        """Capture current system state."""
        try:
            if HAS_PSUTIL and self.process:
                memory_info = self.process.memory_info()
                memory_mb = memory_info.rss / 1024 / 1024  # Convert to MB
                
                cpu_percent = self.process.cpu_percent()
                thread_count = self.process.num_threads()
                process_id = self.process.pid
            else:
                # Fallback without psutil
                memory_mb = 0.0
                cpu_percent = 0.0
                thread_count = threading.active_count()
                process_id = 0
            
            # Garbage collection stats
            gc_stats = {
                "collections": gc.get_stats(),
                "objects": len(gc.get_objects()),
                "garbage": len(gc.garbage)
            }
            
            return SystemState(
                timestamp=time.time(),
                memory_usage_mb=memory_mb,
                cpu_percent=cpu_percent,
                thread_count=thread_count,
                process_id=process_id,
                python_version=sys.version,
                gc_stats=gc_stats
            )
        except Exception as e:
            # Fallback to basic state if detailed monitoring fails
            return SystemState(
                timestamp=time.time(),
                memory_usage_mb=0.0,
                cpu_percent=0.0,
                thread_count=threading.active_count(),
                process_id=0,
                python_version=sys.version
            )
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            if HAS_PSUTIL and self.process:
                memory_info = self.process.memory_info()
                return memory_info.rss / 1024 / 1024  # Convert to MB
            else:
                return 0.0
        except Exception:
            return 0.0
    
    def _serialize_parameters(self, data: Any) -> Any:
        """
        Safely serialize function parameters and results for storage.
        Handles complex objects, circular references, and size limits.
        """
        if not data:
            return data
        
        try:
            # Convert to string representation and check size
            str_repr = str(data)
            if len(str_repr) > self.max_parameter_size:
                return f"<Data too large: {len(str_repr)} chars, truncated>"
            
            # Handle common types
            if isinstance(data, (str, int, float, bool, type(None))):
                return data
            elif isinstance(data, (list, tuple)):
                return [self._serialize_parameters(item) for item in data[:100]]  # Limit list size
            elif isinstance(data, dict):
                return {k: self._serialize_parameters(v) for k, v in list(data.items())[:50]}  # Limit dict size
            else:
                # For complex objects, use repr but with size limit
                repr_str = repr(data)
                if len(repr_str) > self.max_parameter_size:
                    return f"<{type(data).__name__}: {repr_str[:100]}...>"
                return repr_str
                
        except Exception as e:
            return f"<Serialization error: {str(e)}>"