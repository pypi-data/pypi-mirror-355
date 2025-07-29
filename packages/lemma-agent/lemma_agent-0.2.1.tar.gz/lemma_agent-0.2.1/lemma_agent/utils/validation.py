"""
Validation utilities for AgentDebugger SDK.

Provides validation functions for configuration, trace data, and other
components to ensure data integrity and prevent runtime errors.
"""

from typing import Any, Dict, List, Optional, Union, Tuple
from dataclasses import dataclass
import inspect
import re


@dataclass
class ValidationResult:
    """Result of a validation operation."""
    is_valid: bool
    errors: List[str] = None
    warnings: List[str] = None
    suggestions: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
        if self.suggestions is None:
            self.suggestions = []
    
    def add_error(self, error: str, suggestion: str = None) -> None:
        """Add an error and optional suggestion."""
        self.errors.append(error)
        self.is_valid = False
        if suggestion:
            self.suggestions.append(suggestion)
    
    def add_warning(self, warning: str, suggestion: str = None) -> None:
        """Add a warning and optional suggestion."""
        self.warnings.append(warning)
        if suggestion:
            self.suggestions.append(suggestion)
    
    def get_summary(self) -> str:
        """Get a human-readable summary of validation results."""
        if self.is_valid:
            summary = "✅ Validation passed"
            if self.warnings:
                summary += f" with {len(self.warnings)} warnings"
        else:
            summary = f"❌ Validation failed with {len(self.errors)} errors"
            if self.warnings:
                summary += f" and {len(self.warnings)} warnings"
        
        return summary


def validate_debug_config(config_dict: Dict[str, Any], 
                         schema: Optional[Dict[str, Any]] = None) -> ValidationResult:
    """
    Validate debugging configuration dictionary.
    
    Args:
        config_dict: Configuration dictionary to validate
        schema: Optional schema for custom validation rules
        
    Returns:
        ValidationResult with detailed validation information
    """
    result = ValidationResult(is_valid=True)
    
    # Define validation schema if not provided
    if schema is None:
        schema = _get_default_config_schema()
    
    # Validate required fields
    required_fields = schema.get("required", [])
    for field in required_fields:
        if field not in config_dict or config_dict[field] is None:
            result.add_error(
                f"Required field '{field}' is missing",
                f"Add '{field}' to your configuration"
            )
    
    # Validate field types and values
    field_specs = schema.get("fields", {})
    for field_name, field_spec in field_specs.items():
        if field_name in config_dict:
            value = config_dict[field_name]
            _validate_field(field_name, value, field_spec, result)
    
    # Check for unknown fields
    known_fields = set(field_specs.keys())
    config_fields = set(config_dict.keys())
    unknown_fields = config_fields - known_fields
    
    for field in unknown_fields:
        result.add_warning(
            f"Unknown configuration field '{field}'",
            "This field will be ignored"
        )
    
    # Validate field combinations and dependencies
    _validate_config_dependencies(config_dict, result)
    
    return result


def validate_trace_data(trace_data: Dict[str, Any], 
                       expected_schema: Optional[Dict[str, Any]] = None) -> ValidationResult:
    """
    Validate trace data structure and content.
    
    Args:
        trace_data: Trace data dictionary to validate
        expected_schema: Expected schema for trace data
        
    Returns:
        ValidationResult with validation details
    """
    result = ValidationResult(is_valid=True)
    
    # Define expected schema if not provided
    if expected_schema is None:
        expected_schema = _get_default_trace_schema()
    
    # Validate required trace fields
    required_fields = expected_schema.get("required", [])
    for field in required_fields:
        if field not in trace_data:
            result.add_error(
                f"Required trace field '{field}' is missing",
                f"Ensure trace includes '{field}' field"
            )
    
    # Validate trace ID format
    if "trace_id" in trace_data:
        trace_id = trace_data["trace_id"]
        if not isinstance(trace_id, str) or len(trace_id) == 0:
            result.add_error(
                "trace_id must be a non-empty string",
                "Use a UUID or other unique identifier for trace_id"
            )
    
    # Validate timestamps
    timestamp_fields = ["start_time", "end_time"]
    for field in timestamp_fields:
        if field in trace_data:
            timestamp = trace_data[field]
            if not isinstance(timestamp, (int, float)) or timestamp <= 0:
                result.add_error(
                    f"{field} must be a positive number (Unix timestamp)",
                    f"Use time.time() to generate valid {field}"
                )
    
    # Validate timing consistency
    if "start_time" in trace_data and "end_time" in trace_data:
        start_time = trace_data["start_time"]
        end_time = trace_data["end_time"]
        if isinstance(start_time, (int, float)) and isinstance(end_time, (int, float)):
            if end_time < start_time:
                result.add_error(
                    "end_time cannot be before start_time",
                    "Check timestamp generation logic"
                )
    
    # Validate steps array
    if "steps" in trace_data:
        steps = trace_data["steps"]
        if not isinstance(steps, list):
            result.add_error(
                "steps must be a list",
                "Ensure steps is an array of step objects"
            )
        else:
            for i, step in enumerate(steps):
                _validate_step_data(step, i, result)
    
    # Validate performance metrics
    if "duration_ms" in trace_data:
        duration = trace_data["duration_ms"]
        if not isinstance(duration, (int, float)) or duration < 0:
            result.add_error(
                "duration_ms must be a non-negative number",
                "Calculate duration as (end_time - start_time) * 1000"
            )
    
    # Validate memory metrics
    memory_fields = ["initial_memory_mb", "final_memory_mb", "peak_memory_mb"]
    for field in memory_fields:
        if field in trace_data:
            memory_value = trace_data[field]
            if not isinstance(memory_value, (int, float)) or memory_value < 0:
                result.add_error(
                    f"{field} must be a non-negative number",
                    f"Ensure {field} represents memory in megabytes"
                )
    
    # Validate error information
    if "error" in trace_data and trace_data["error"] is not None:
        error_data = trace_data["error"]
        if isinstance(error_data, dict):
            if "error_type" not in error_data:
                result.add_warning(
                    "Error data missing error_type",
                    "Include error_type for better error classification"
                )
            if "error_message" not in error_data:
                result.add_warning(
                    "Error data missing error_message", 
                    "Include error_message for debugging context"
                )
    
    return result


def validate_function_signature(func: callable) -> ValidationResult:
    """
    Validate that a function can be safely wrapped with debugging.
    
    Args:
        func: Function to validate
        
    Returns:
        ValidationResult indicating if function can be wrapped
    """
    result = ValidationResult(is_valid=True)
    
    if not callable(func):
        result.add_error(
            "Object is not callable",
            "Only functions and methods can be wrapped"
        )
        return result
    
    # Check function signature
    try:
        sig = inspect.signature(func)
    except (ValueError, TypeError) as e:
        result.add_error(
            f"Cannot inspect function signature: {e}",
            "Function may not be compatible with debugging wrapper"
        )
        return result
    
    # Check for problematic parameter types
    for param_name, param in sig.parameters.items():
        if param.kind == param.VAR_POSITIONAL and param_name != "args":
            result.add_warning(
                f"Function uses *{param_name} instead of *args",
                "Consider using standard *args for better compatibility"
            )
        elif param.kind == param.VAR_KEYWORD and param_name != "kwargs":
            result.add_warning(
                f"Function uses **{param_name} instead of **kwargs",
                "Consider using standard **kwargs for better compatibility"
            )
    
    # Check if function is already wrapped
    if hasattr(func, '_agentdebugger_wrapped'):
        result.add_warning(
            "Function is already wrapped with @smart_debug",
            "Remove duplicate decorator to avoid double wrapping"
        )
    
    # Check for conflicting decorators
    if hasattr(func, '__wrapped__'):
        result.add_warning(
            "Function appears to be wrapped by another decorator",
            "Ensure @smart_debug is the outermost decorator"
        )
    
    return result


def validate_api_endpoint(endpoint: str) -> ValidationResult:
    """
    Validate API endpoint URL format.
    
    Args:
        endpoint: API endpoint URL to validate
        
    Returns:
        ValidationResult with validation details
    """
    result = ValidationResult(is_valid=True)
    
    if not isinstance(endpoint, str):
        result.add_error(
            "API endpoint must be a string",
            "Provide endpoint as a string URL"
        )
        return result
    
    if not endpoint:
        result.add_error(
            "API endpoint cannot be empty",
            "Provide a valid API endpoint URL"
        )
        return result
    
    # Basic URL format validation
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)'
        , re.IGNORECASE)
    
    if not url_pattern.match(endpoint):
        result.add_error(
            "Invalid URL format",
            "Use format: https://api.example.com or http://localhost:8080"
        )
    
    # Security recommendations
    if endpoint.startswith("http://") and "localhost" not in endpoint and "127.0.0.1" not in endpoint:
        result.add_warning(
            "Using HTTP instead of HTTPS for external endpoint",
            "Consider using HTTPS for secure communication"
        )
    
    return result


def _validate_field(field_name: str, value: Any, field_spec: Dict[str, Any], 
                   result: ValidationResult) -> None:
    """Validate a single configuration field."""
    
    # Type validation
    expected_type = field_spec.get("type")
    if expected_type and not isinstance(value, expected_type):
        if expected_type == bool and isinstance(value, str):
            # Allow string boolean values
            if value.lower() not in ["true", "false", "1", "0", "yes", "no"]:
                result.add_error(
                    f"Field '{field_name}' must be boolean or boolean string",
                    f"Use true/false or 1/0 for {field_name}"
                )
        else:
            result.add_error(
                f"Field '{field_name}' must be of type {expected_type.__name__}",
                f"Convert {field_name} to {expected_type.__name__}"
            )
            return
    
    # Value validation
    allowed_values = field_spec.get("allowed_values")
    if allowed_values and value not in allowed_values:
        result.add_error(
            f"Field '{field_name}' has invalid value '{value}'",
            f"Use one of: {', '.join(map(str, allowed_values))}"
        )
    
    # Range validation
    min_value = field_spec.get("min_value")
    max_value = field_spec.get("max_value")
    
    if min_value is not None and isinstance(value, (int, float)) and value < min_value:
        result.add_error(
            f"Field '{field_name}' value {value} is below minimum {min_value}",
            f"Set {field_name} to at least {min_value}"
        )
    
    if max_value is not None and isinstance(value, (int, float)) and value > max_value:
        result.add_error(
            f"Field '{field_name}' value {value} exceeds maximum {max_value}",
            f"Set {field_name} to at most {max_value}"
        )
    
    # Pattern validation for strings
    pattern = field_spec.get("pattern")
    if pattern and isinstance(value, str):
        if not re.match(pattern, value):
            result.add_error(
                f"Field '{field_name}' does not match required pattern",
                f"Ensure {field_name} follows the expected format"
            )


def _validate_step_data(step: Any, index: int, result: ValidationResult) -> None:
    """Validate a single step in trace data."""
    
    if not isinstance(step, dict):
        result.add_error(
            f"Step {index} must be a dictionary",
            f"Ensure step {index} is a valid step object"
        )
        return
    
    # Required step fields
    required_step_fields = ["step_id", "step_name", "start_time"]
    for field in required_step_fields:
        if field not in step:
            result.add_error(
                f"Step {index} missing required field '{field}'",
                f"Add '{field}' to step {index}"
            )
    
    # Validate step timing
    if "start_time" in step and "end_time" in step:
        start_time = step["start_time"]
        end_time = step["end_time"]
        if (isinstance(start_time, (int, float)) and 
            isinstance(end_time, (int, float)) and 
            end_time < start_time):
            result.add_error(
                f"Step {index} end_time before start_time",
                f"Fix timing logic for step {index}"
            )


def _validate_config_dependencies(config_dict: Dict[str, Any], 
                                result: ValidationResult) -> None:
    """Validate configuration field dependencies and combinations."""
    
    # API configuration dependencies
    if config_dict.get("api_key") and not config_dict.get("api_endpoint"):
        result.add_warning(
            "API key provided but no API endpoint configured",
            "Set api_endpoint to use API features"
        )
    
    # Cost tracking dependencies
    if config_dict.get("cost_tracking", True) and not config_dict.get("api_key"):
        result.add_warning(
            "Cost tracking enabled but no API key configured",
            "Set api_key to enable cloud-based cost analysis"
        )
    
    # Trace level and performance
    if config_dict.get("trace_level") == "verbose" and config_dict.get("sampling_rate", 1.0) == 1.0:
        result.add_warning(
            "Verbose tracing with 100% sampling may impact performance",
            "Consider reducing sampling_rate for production use"
        )
    
    # Memory tracking and performance
    if (config_dict.get("memory_tracking", True) and 
        config_dict.get("environment") == "production"):
        result.add_warning(
            "Memory tracking enabled in production environment",
            "Consider disabling memory_tracking for better performance"
        )


def _get_default_config_schema() -> Dict[str, Any]:
    """Get the default configuration validation schema."""
    return {
        "required": ["project_id"],
        "fields": {
            "project_id": {
                "type": str,
                "pattern": r"^[a-zA-Z0-9_-]+$"
            },
            "environment": {
                "type": str,
                "allowed_values": ["development", "staging", "production", "test"]
            },
            "trace_level": {
                "type": str,
                "allowed_values": ["basic", "detailed", "verbose"]
            },
            "sampling_rate": {
                "type": (int, float),
                "min_value": 0.0,
                "max_value": 1.0
            },
            "max_trace_size": {
                "type": int,
                "min_value": 100,
                "max_value": 100000
            },
            "timeout_seconds": {
                "type": int,
                "min_value": 1,
                "max_value": 300
            },
            "retry_attempts": {
                "type": int,
                "min_value": 0,
                "max_value": 10
            },
            "log_level": {
                "type": str,
                "allowed_values": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            },
            "log_format": {
                "type": str,
                "allowed_values": ["json", "text", "colored"]
            }
        }
    }


def _get_default_trace_schema() -> Dict[str, Any]:
    """Get the default trace data validation schema."""
    return {
        "required": ["trace_id", "function_name", "start_time"],
        "fields": {
            "trace_id": {"type": str},
            "function_name": {"type": str},
            "start_time": {"type": (int, float)},
            "end_time": {"type": (int, float)},
            "duration_ms": {"type": (int, float)},
            "steps": {"type": list},
            "environment": {"type": str},
            "framework_type": {"type": str}
        }
    }