"""
Data collection and organization for AgentDebugger SDK.

Collects, enriches, and organizes trace data for analysis by the AI system.
Handles both successful executions and error scenarios.
"""

import os
import platform
import sys
import traceback
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone
from .tracer import TraceResult
from .config import DebugConfig


@dataclass
class CollectedData:
    """Comprehensive collected data for an agent execution."""
    
    # Core execution data
    trace_result: TraceResult
    
    # Environment context
    environment_info: Dict[str, Any] = field(default_factory=dict)
    system_info: Dict[str, Any] = field(default_factory=dict)
    
    # Performance analysis
    performance_metrics: Dict[str, Any] = field(default_factory=dict)
    
    # Framework-specific data
    framework_data: Dict[str, Any] = field(default_factory=dict)
    
    # Aggregated insights
    summary: Dict[str, Any] = field(default_factory=dict)
    
    # Collection metadata
    collected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    collector_version: str = "1.0.0"


@dataclass
class ErrorData:
    """Specialized data structure for error scenarios."""
    
    # Error details
    error: Exception
    error_type: str
    error_message: str
    error_traceback: str
    
    # Context when error occurred
    trace_result: TraceResult
    execution_context: Dict[str, Any] = field(default_factory=dict)
    system_context: Dict[str, Any] = field(default_factory=dict)
    
    # Error classification
    error_category: Optional[str] = None
    potential_causes: List[str] = field(default_factory=list)
    suggested_fixes: List[str] = field(default_factory=list)
    
    # Collection metadata
    collected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class PerformanceData:
    """Performance metrics extracted from execution traces."""
    
    # Timing metrics
    total_duration_ms: float
    step_durations: List[float] = field(default_factory=list)
    longest_step_ms: float = 0.0
    shortest_step_ms: float = 0.0
    
    # Memory metrics
    initial_memory_mb: float = 0.0
    final_memory_mb: float = 0.0
    peak_memory_mb: float = 0.0
    memory_growth_mb: float = 0.0
    
    # CPU metrics (if available)
    cpu_usage_percent: float = 0.0
    
    # Step analysis
    step_count: int = 0
    successful_steps: int = 0
    failed_steps: int = 0
    
    # Performance flags
    is_slow: bool = False
    is_memory_intensive: bool = False
    has_performance_issues: bool = False


class DataCollector:
    """
    Main data collector that organizes and enriches trace data for analysis.
    """
    
    def __init__(self, config: DebugConfig):
        """
        Initialize the data collector.
        
        Args:
            config: Debug configuration
        """
        self.config = config
        
        # Performance thresholds for analysis
        self.slow_execution_threshold_ms = 5000  # 5 seconds
        self.high_memory_threshold_mb = 100      # 100 MB
        self.memory_growth_threshold_mb = 50     # 50 MB growth
    
    def collect_execution_data(self, trace_result: TraceResult, 
                             context: Dict[str, Any]) -> CollectedData:
        """
        Collect comprehensive execution data for successful or failed agent runs.
        
        Args:
            trace_result: Complete trace result from execution
            context: Additional context information
            
        Returns:
            Comprehensive collected data ready for analysis
        """
        # Create collected data structure
        collected_data = CollectedData(trace_result=trace_result)
        
        # Collect environment information
        collected_data.environment_info = self._collect_environment_info(context)
        
        # Collect system information
        collected_data.system_info = self._collect_system_info()
        
        # Extract and analyze performance metrics
        collected_data.performance_metrics = self._extract_performance_metrics(trace_result)
        
        # Collect framework-specific data
        collected_data.framework_data = self._collect_framework_data(trace_result, context)
        
        # Generate execution summary
        collected_data.summary = self._generate_execution_summary(trace_result, collected_data)
        
        return collected_data
    
    def collect_error_data(self, error: Exception, context: Dict[str, Any], 
                          trace_result: TraceResult) -> ErrorData:
        """
        Collect specialized error information for debugging failed agent executions.
        
        Args:
            error: Exception that occurred
            context: Execution context when error occurred
            trace_result: Trace result up to the point of failure
            
        Returns:
            Detailed error data for analysis
        """
        # Create error data structure
        error_data = ErrorData(
            error=error,
            error_type=type(error).__name__,
            error_message=str(error),
            error_traceback=traceback.format_exc(),
            trace_result=trace_result
        )
        
        # Collect execution context
        error_data.execution_context = {
            "function_name": trace_result.function_name,
            "execution_step": len(trace_result.steps),
            "duration_before_error_ms": trace_result.get_total_duration_ms(),
            "environment": context.get("environment", "unknown"),
            "project_id": context.get("project_id", "unknown")
        }
        
        # Collect system context
        error_data.system_context = self._collect_system_info()
        
        # Classify error and suggest fixes
        error_data.error_category = self._classify_error(error)
        error_data.potential_causes = self._identify_potential_causes(error, trace_result)
        error_data.suggested_fixes = self._generate_fix_suggestions(error, trace_result)
        
        return error_data
    
    def collect_performance_data(self, trace_result: TraceResult) -> PerformanceData:
        """
        Extract detailed performance metrics from a trace result.
        
        Args:
            trace_result: Trace result to analyze
            
        Returns:
            Detailed performance analysis
        """
        perf_data = PerformanceData(
            total_duration_ms=trace_result.get_total_duration_ms(),
            step_count=len(trace_result.steps),
            successful_steps=len([s for s in trace_result.steps if s.error is None]),
            failed_steps=len([s for s in trace_result.steps if s.error is not None])
        )
        
        # Analyze step timings
        if trace_result.steps:
            step_durations = [s.duration_ms or 0 for s in trace_result.steps]
            perf_data.step_durations = step_durations
            perf_data.longest_step_ms = max(step_durations) if step_durations else 0
            perf_data.shortest_step_ms = min(step_durations) if step_durations else 0
        
        # Analyze memory usage
        if trace_result.initial_state and trace_result.final_state:
            perf_data.initial_memory_mb = trace_result.initial_state.memory_usage_mb
            perf_data.final_memory_mb = trace_result.final_state.memory_usage_mb
            perf_data.memory_growth_mb = trace_result.memory_growth_mb or 0
            perf_data.peak_memory_mb = trace_result.peak_memory_mb or perf_data.final_memory_mb
            
            # CPU usage (if available)
            if hasattr(trace_result.final_state, 'cpu_percent'):
                perf_data.cpu_usage_percent = trace_result.final_state.cpu_percent
        
        # Set performance flags
        perf_data.is_slow = perf_data.total_duration_ms > self.slow_execution_threshold_ms
        perf_data.is_memory_intensive = perf_data.peak_memory_mb > self.high_memory_threshold_mb
        perf_data.has_performance_issues = (
            perf_data.is_slow or 
            perf_data.is_memory_intensive or 
            perf_data.memory_growth_mb > self.memory_growth_threshold_mb
        )
        
        return perf_data
    
    def _collect_environment_info(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Collect environment and configuration information."""
        env_info = {
            "project_id": context.get("project_id", ""),
            "environment": context.get("environment", "development"),
            "trace_level": context.get("trace_level", "basic"),
            "framework_type": context.get("framework_type"),
            "agent_type": context.get("agent_type"),
            "config_source": "decorator",  # Could be file, env, etc.
        }
        
        # Add relevant environment variables (without sensitive data)
        relevant_env_vars = [
            "OPENAI_API_BASE", "ANTHROPIC_API_URL", "LANGCHAIN_TRACING",
            "PYTHONPATH", "VIRTUAL_ENV", "CONDA_DEFAULT_ENV"
        ]
        
        env_vars = {}
        for var in relevant_env_vars:
            value = os.getenv(var)
            if value:
                # Anonymize sensitive-looking values
                if "key" in var.lower() or "token" in var.lower():
                    env_vars[var] = f"***{value[-4:]}" if len(value) > 4 else "***"
                else:
                    env_vars[var] = value
        
        env_info["environment_variables"] = env_vars
        
        return env_info
    
    def _collect_system_info(self) -> Dict[str, Any]:
        """Collect system and runtime information."""
        system_info = {
            "platform": platform.platform(),
            "python_version": sys.version,
            "python_executable": sys.executable,
            "architecture": platform.architecture(),
            "processor": platform.processor(),
            "hostname": platform.node(),
            "user": os.getenv("USER", "unknown"),
        }
        
        # Add Python package information for relevant packages
        try:
            import pkg_resources
            relevant_packages = [
                "langchain", "openai", "anthropic", "crewai", "autogen",
                "numpy", "pandas", "requests", "asyncio"
            ]
            
            installed_packages = {}
            for package in relevant_packages:
                try:
                    version = pkg_resources.get_distribution(package).version
                    installed_packages[package] = version
                except pkg_resources.DistributionNotFound:
                    pass
            
            system_info["installed_packages"] = installed_packages
            
        except ImportError:
            system_info["installed_packages"] = {}
        
        return system_info
    
    def _extract_performance_metrics(self, trace_result: TraceResult) -> Dict[str, Any]:
        """Extract comprehensive performance metrics from trace result."""
        metrics = {
            "execution_time": {
                "total_ms": trace_result.get_total_duration_ms(),
                "start_time": trace_result.start_time,
                "end_time": trace_result.end_time
            },
            "step_analysis": trace_result.get_step_summary(),
            "success_rate": 1.0 if trace_result.is_successful() else 0.0
        }
        
        # Memory metrics
        if trace_result.initial_state and trace_result.final_state:
            metrics["memory"] = {
                "initial_mb": trace_result.initial_state.memory_usage_mb,
                "final_mb": trace_result.final_state.memory_usage_mb,
                "peak_mb": trace_result.peak_memory_mb,
                "growth_mb": trace_result.memory_growth_mb,
                "efficiency_score": self._calculate_memory_efficiency(trace_result)
            }
        
        # Performance scoring
        metrics["performance_score"] = self._calculate_performance_score(trace_result)
        
        return metrics
    
    def _collect_framework_data(self, trace_result: TraceResult, 
                               context: Dict[str, Any]) -> Dict[str, Any]:
        """Collect framework-specific data and insights."""
        framework_data = {
            "framework_type": context.get("framework_type", "unknown"),
            "framework_version": context.get("framework_version"),
            "agent_class": context.get("agent_class"),
            "tool_usage": [],  # To be populated by framework adapters
            "llm_calls": [],   # To be populated by framework adapters
            "memory_usage": [] # To be populated by framework adapters
        }
        
        # Extract framework-specific patterns from steps
        for step in trace_result.steps:
            step_data = step.step_data
            
            # Look for LLM-related steps
            if any(keyword in step.step_name.lower() for keyword in ["llm", "openai", "anthropic", "chat"]):
                framework_data["llm_calls"].append({
                    "step_name": step.step_name,
                    "duration_ms": step.duration_ms,
                    "data": step_data
                })
            
            # Look for tool usage
            if any(keyword in step.step_name.lower() for keyword in ["tool", "function", "api"]):
                framework_data["tool_usage"].append({
                    "step_name": step.step_name,
                    "duration_ms": step.duration_ms,
                    "data": step_data
                })
        
        return framework_data
    
    def _generate_execution_summary(self, trace_result: TraceResult, 
                                   collected_data: CollectedData) -> Dict[str, Any]:
        """Generate high-level summary of execution for quick analysis."""
        summary = {
            "execution_id": trace_result.trace_id,
            "function_name": trace_result.function_name,
            "status": "success" if trace_result.is_successful() else "failed",
            "duration_ms": trace_result.get_total_duration_ms(),
            "step_count": len(trace_result.steps),
            "framework": collected_data.framework_data.get("framework_type", "unknown"),
            "environment": collected_data.environment_info.get("environment", "unknown")
        }
        
        # Add performance flags
        perf_metrics = collected_data.performance_metrics
        summary["performance_flags"] = {
            "is_slow": perf_metrics.get("execution_time", {}).get("total_ms", 0) > self.slow_execution_threshold_ms,
            "high_memory": perf_metrics.get("memory", {}).get("peak_mb", 0) > self.high_memory_threshold_mb,
            "memory_growth": perf_metrics.get("memory", {}).get("growth_mb", 0) > self.memory_growth_threshold_mb
        }
        
        # Add insights
        summary["insights"] = self._generate_insights(trace_result, collected_data)
        
        return summary
    
    def _classify_error(self, error: Exception) -> str:
        """Classify error into categories for targeted analysis."""
        error_type = type(error).__name__
        error_message = str(error).lower()
        
        # API-related errors
        if any(keyword in error_message for keyword in ["api", "connection", "timeout", "rate limit"]):
            return "api_error"
        
        # Memory-related errors
        if error_type in ["MemoryError", "OutOfMemoryError"] or "memory" in error_message:
            return "memory_error"
        
        # Token/context limit errors
        if any(keyword in error_message for keyword in ["token", "context", "limit", "maximum"]):
            return "context_limit_error"
        
        # Authentication errors
        if any(keyword in error_message for keyword in ["auth", "key", "unauthorized", "forbidden"]):
            return "authentication_error"
        
        # Configuration errors
        if error_type in ["ValueError", "TypeError", "AttributeError"] and any(
            keyword in error_message for keyword in ["config", "parameter", "argument", "missing"]
        ):
            return "configuration_error"
        
        # Import/dependency errors
        if error_type in ["ImportError", "ModuleNotFoundError"]:
            return "dependency_error"
        
        # Network errors
        if any(keyword in error_message for keyword in ["network", "dns", "host", "unreachable"]):
            return "network_error"
        
        # Generic classification based on error type
        if error_type in ["TimeoutError", "ConnectionError"]:
            return "connection_error"
        elif error_type in ["KeyError", "IndexError", "AttributeError"]:
            return "data_error"
        elif error_type in ["ValueError", "TypeError"]:
            return "validation_error"
        else:
            return "unknown_error"
    
    def _identify_potential_causes(self, error: Exception, trace_result: TraceResult) -> List[str]:
        """Identify potential causes of the error based on context."""
        causes = []
        error_category = self._classify_error(error)
        error_message = str(error).lower()
        
        if error_category == "api_error":
            causes.extend([
                "API endpoint is down or unreachable",
                "Invalid API key or authentication credentials",
                "Rate limiting from API provider",
                "Network connectivity issues",
                "API request format is incorrect"
            ])
        
        elif error_category == "memory_error":
            causes.extend([
                "Agent processing too much data at once",
                "Memory leak in agent implementation",
                "Insufficient system memory",
                "Large conversation history not being managed",
                "Inefficient data structures or algorithms"
            ])
        
        elif error_category == "context_limit_error":
            causes.extend([
                "Conversation context exceeds LLM token limit",
                "Input prompt is too long",
                "Accumulated conversation history too large",
                "Document processing exceeds context window",
                "Inefficient prompt engineering"
            ])
        
        elif error_category == "authentication_error":
            causes.extend([
                "Missing or invalid API key",
                "API key has insufficient permissions",
                "API key has expired or been revoked",
                "Incorrect authentication method used",
                "API endpoint requires different authentication"
            ])
        
        elif error_category == "configuration_error":
            causes.extend([
                "Missing required configuration parameters",
                "Invalid configuration values",
                "Configuration file not found or corrupted",
                "Environment variables not set correctly",
                "Conflicting configuration settings"
            ])
        
        elif error_category == "dependency_error":
            causes.extend([
                "Required Python package not installed",
                "Package version incompatibility",
                "Virtual environment not activated",
                "PYTHONPATH configuration issues",
                "Missing system dependencies"
            ])
        
        # Add context-specific causes based on execution trace
        if trace_result.steps:
            last_step = trace_result.steps[-1]
            if last_step.error:
                causes.append(f"Error occurred during step: {last_step.step_name}")
        
        if trace_result.get_total_duration_ms() > 30000:  # 30 seconds
            causes.append("Operation timed out due to long execution time")
        
        return causes
    
    def _generate_fix_suggestions(self, error: Exception, trace_result: TraceResult) -> List[str]:
        """Generate specific fix suggestions based on error analysis."""
        suggestions = []
        error_category = self._classify_error(error)
        error_message = str(error).lower()
        
        if error_category == "api_error":
            suggestions.extend([
                "Check API endpoint URL and network connectivity",
                "Verify API key is valid and has necessary permissions",
                "Implement exponential backoff for rate limit handling",
                "Add proper error handling and retry logic",
                "Check API provider status page for outages"
            ])
        
        elif error_category == "memory_error":
            suggestions.extend([
                "Reduce batch size or process data in smaller chunks",
                "Implement conversation memory management and summarization",
                "Use memory-efficient data structures (generators, streaming)",
                "Add memory monitoring and garbage collection",
                "Consider using a machine with more RAM"
            ])
        
        elif error_category == "context_limit_error":
            suggestions.extend([
                "Implement conversation summarization to reduce context size",
                "Use truncation strategies for long inputs",
                "Switch to a model with larger context window",
                "Break large tasks into smaller sub-tasks",
                "Implement sliding window approach for conversation history"
            ])
        
        elif error_category == "authentication_error":
            suggestions.extend([
                "Set OPENAI_API_KEY or relevant API key environment variable",
                "Verify API key format and permissions",
                "Check if API key supports the specific endpoint being used",
                "Regenerate API key if it may have been compromised",
                "Review API provider documentation for authentication requirements"
            ])
        
        elif error_category == "configuration_error":
            suggestions.extend([
                "Check all required configuration parameters are set",
                "Validate configuration file syntax (JSON/YAML)",
                "Set missing environment variables",
                "Review configuration documentation and examples",
                "Use configuration validation before starting agent"
            ])
        
        elif error_category == "dependency_error":
            suggestions.extend([
                "Install missing package: pip install <package_name>",
                "Check package version compatibility requirements",
                "Activate correct virtual environment",
                "Update requirements.txt with all dependencies",
                "Check PYTHONPATH includes necessary directories"
            ])
        
        # Add specific suggestions based on error message patterns
        if "openai" in error_message:
            suggestions.append("Install OpenAI package: pip install openai")
        elif "langchain" in error_message:
            suggestions.append("Install LangChain: pip install langchain")
        elif "anthropic" in error_message:
            suggestions.append("Install Anthropic package: pip install anthropic")
        
        return suggestions
    
    def _calculate_memory_efficiency(self, trace_result: TraceResult) -> float:
        """Calculate memory efficiency score (0.0 to 1.0)."""
        if not (trace_result.initial_state and trace_result.final_state):
            return 0.5  # Unknown, assume average
        
        memory_growth = trace_result.memory_growth_mb or 0
        execution_time_minutes = trace_result.get_total_duration_ms() / 60000
        
        if execution_time_minutes == 0:
            return 1.0
        
        # Memory growth rate per minute
        growth_rate = memory_growth / max(execution_time_minutes, 0.1)
        
        # Score based on growth rate (lower is better)
        if growth_rate < 1:     # < 1MB per minute - excellent
            return 1.0
        elif growth_rate < 5:   # < 5MB per minute - good
            return 0.8
        elif growth_rate < 10:  # < 10MB per minute - fair
            return 0.6
        elif growth_rate < 20:  # < 20MB per minute - poor
            return 0.4
        else:                   # > 20MB per minute - very poor
            return 0.2
    
    def _calculate_performance_score(self, trace_result: TraceResult) -> float:
        """Calculate overall performance score (0.0 to 1.0)."""
        score = 1.0
        
        # Duration penalty
        duration_ms = trace_result.get_total_duration_ms()
        if duration_ms > 1000:    # > 1 second
            score -= 0.1
        if duration_ms > 5000:    # > 5 seconds
            score -= 0.2
        if duration_ms > 10000:   # > 10 seconds
            score -= 0.3
        
        # Memory penalty
        if trace_result.memory_growth_mb:
            if trace_result.memory_growth_mb > 50:    # > 50MB growth
                score -= 0.2
            elif trace_result.memory_growth_mb > 100: # > 100MB growth
                score -= 0.4
        
        # Error penalty
        if not trace_result.is_successful():
            score -= 0.5
        
        # Step efficiency
        if trace_result.steps:
            failed_steps = len([s for s in trace_result.steps if s.error])
            if failed_steps > 0:
                score -= 0.1 * (failed_steps / len(trace_result.steps))
        
        return max(0.0, score)
    
    def _generate_insights(self, trace_result: TraceResult, 
                          collected_data: CollectedData) -> List[str]:
        """Generate actionable insights from collected data."""
        insights = []
        
        # Performance insights
        duration_ms = trace_result.get_total_duration_ms()
        if duration_ms > 5000:
            insights.append(f"Execution took {duration_ms/1000:.1f}s - consider optimization")
        
        # Memory insights
        memory_data = collected_data.performance_metrics.get("memory", {})
        memory_growth = memory_data.get("growth_mb", 0)
        if memory_growth > 50:
            insights.append(f"High memory growth ({memory_growth:.1f}MB) - check for memory leaks")
        
        # Step analysis insights
        if trace_result.steps:
            step_durations = [s.duration_ms or 0 for s in trace_result.steps]
            if step_durations:
                max_duration = max(step_durations)
                if max_duration > duration_ms * 0.5:  # One step took >50% of total time
                    longest_step = max(trace_result.steps, key=lambda s: s.duration_ms or 0)
                    insights.append(f"Step '{longest_step.step_name}' is a bottleneck ({max_duration:.0f}ms)")
        
        # Framework-specific insights
        framework_type = collected_data.framework_data.get("framework_type")
        if framework_type == "langchain":
            llm_calls = collected_data.framework_data.get("llm_calls", [])
            if len(llm_calls) > 5:
                insights.append(f"Many LLM calls ({len(llm_calls)}) - consider batching or caching")
        
        # Error patterns
        if not trace_result.is_successful():
            error_type = type(trace_result.error).__name__ if trace_result.error else "Unknown"
            insights.append(f"Failed with {error_type} - check error handling")
        
        return insights