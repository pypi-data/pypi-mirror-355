"""
Configuration management for AgentDebugger SDK.

Handles loading, validation, and management of debugging configuration
from multiple sources including files, environment variables, and defaults.
"""

import os
import json
from typing import Dict, Any, List, Tuple, Optional, Union
from dataclasses import dataclass, field
from pathlib import Path

# Try to import yaml, but make it optional
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


@dataclass
class ValidationError:
    """Represents a configuration validation error."""
    field: str
    message: str
    suggestion: Optional[str] = None
    error_code: str = "VALIDATION_ERROR"


@dataclass
class DebugConfig:
    """Main configuration class for AgentDebugger."""
    
    # Core settings
    project_id: str = ""
    environment: str = "development"
    
    # Tracing configuration
    trace_level: str = "basic"  # basic, detailed, verbose
    max_trace_size: int = 10000  # Maximum trace entries
    step_tracking: bool = True
    capture_parameters: bool = True
    capture_results: bool = True
    
    # Performance monitoring
    memory_tracking: bool = True
    timing_precision: str = "milliseconds"  # microseconds, milliseconds, seconds
    sampling_rate: float = 1.0  # 0.0 to 1.0
    
    # Storage settings
    local_cache: bool = True
    cache_directory: str = "~/.agentdebugger/cache"
    data_retention_days: int = 30
    compression_enabled: bool = True
    
    # API settings
    api_endpoint: str = "https://api.agentdebugger.pro"
    api_key: Optional[str] = None
    timeout_seconds: int = 30
    retry_attempts: int = 3
    
    # Feature flags
    auto_fix: bool = False
    cost_tracking: bool = True
    real_time_analysis: bool = False
    anonymize_data: bool = False
    
    # Framework specific
    framework_adapters: Dict[str, bool] = field(default_factory=lambda: {
        "langchain": True,
        "crewai": True,
        "autogen": True,
        "custom": True
    })
    
    # Logging configuration
    log_level: str = "INFO"
    log_format: str = "json"  # json, text, colored
    log_to_file: bool = True
    
    @classmethod
    def load_config(cls, config_path: Optional[Union[str, Path]] = None, 
                   env_vars: bool = True, 
                   override_values: Optional[Dict[str, Any]] = None) -> 'DebugConfig':
        """
        Load configuration from multiple sources with priority order:
        1. override_values (highest priority)
        2. Explicit config file
        3. Environment variables
        4. Default config files (~/.agentdebugger/config.json, ./agentdebugger.json)
        5. Default values (lowest priority)
        
        Args:
            config_path: Explicit path to configuration file
            env_vars: Whether to load from environment variables
            override_values: Dictionary of values to override with highest priority
            
        Returns:
            DebugConfig instance with merged configuration
        """
        config_data = {}
        
        # Start with defaults
        default_config = cls()
        config_data.update(default_config.__dict__)
        
        # Load from default config files
        default_paths = [
            Path.home() / ".agentdebugger" / "config.json",
            Path.home() / ".agentdebugger" / "config.yaml", 
            Path("./agentdebugger.json"),
            Path("./agentdebugger.yaml")
        ]
        
        for path in default_paths:
            if path.exists():
                file_config = cls._load_config_file(path)
                if file_config:
                    config_data.update(file_config)
                    break
        
        # Load from environment variables
        if env_vars:
            env_config = cls._load_env_config()
            config_data.update(env_config)
        
        # Load from explicit config file (high priority)
        if config_path:
            file_config = cls._load_config_file(Path(config_path))
            if file_config:
                config_data.update(file_config)
        
        # Apply override values (highest priority)
        if override_values:
            config_data.update(override_values)
        
        # Create config instance
        config = cls(**{k: v for k, v in config_data.items() 
                       if k in cls.__dataclass_fields__})
        
        # Validate configuration
        is_valid, errors = config.validate_config(config_data)
        if not is_valid:
            error_messages = [f"{err.field}: {err.message}" for err in errors]
            raise ValueError(f"Invalid configuration:\n" + "\n".join(error_messages))
        
        return config
    
    @staticmethod
    def _load_config_file(config_path: Path) -> Optional[Dict[str, Any]]:
        """Load configuration from a JSON or YAML file."""
        try:
            with open(config_path, 'r') as f:
                if config_path.suffix.lower() in ['.yaml', '.yml']:
                    if not HAS_YAML:
                        print(f"Warning: YAML file {config_path} found but PyYAML not installed. Install with: pip install pyyaml")
                        return None
                    return yaml.safe_load(f)
                else:
                    return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load config from {config_path}: {e}")
            return None
    
    @staticmethod
    def _load_env_config() -> Dict[str, Any]:
        """Load configuration from environment variables with AGENTDEBUGGER_ prefix."""
        env_config = {}
        prefix = "AGENTDEBUGGER_"
        
        env_mappings = {
            f"{prefix}PROJECT_ID": "project_id",
            f"{prefix}ENVIRONMENT": "environment", 
            f"{prefix}TRACE_LEVEL": "trace_level",
            f"{prefix}API_ENDPOINT": "api_endpoint",
            f"{prefix}API_KEY": "api_key",
            f"{prefix}AUTO_FIX": "auto_fix",
            f"{prefix}COST_TRACKING": "cost_tracking",
            f"{prefix}LOG_LEVEL": "log_level",
            f"{prefix}CACHE_DIRECTORY": "cache_directory"
        }
        
        for env_var, config_key in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Convert string values to appropriate types
                if config_key in ["auto_fix", "cost_tracking", "memory_tracking", 
                                "step_tracking", "local_cache"]:
                    env_config[config_key] = value.lower() in ['true', '1', 'yes', 'on']
                elif config_key in ["max_trace_size", "timeout_seconds", "retry_attempts"]:
                    try:
                        env_config[config_key] = int(value)
                    except ValueError:
                        pass
                elif config_key == "sampling_rate":
                    try:
                        env_config[config_key] = float(value)
                    except ValueError:
                        pass
                else:
                    env_config[config_key] = value
        
        return env_config
    
    def validate_config(self, config_dict: Dict[str, Any]) -> Tuple[bool, List[ValidationError]]:
        """
        Validate configuration parameters and return detailed validation results.
        
        Args:
            config_dict: Configuration dictionary to validate
            
        Returns:
            Tuple of (is_valid: bool, errors: List[ValidationError])
        """
        errors = []
        
        # Validate required fields
        if not config_dict.get("project_id"):
            errors.append(ValidationError(
                field="project_id",
                message="Project ID is required",
                suggestion="Set project_id to a unique identifier for your agent project",
                error_code="REQUIRED_FIELD"
            ))
        
        # Validate trace_level
        valid_trace_levels = ["basic", "detailed", "verbose"]
        trace_level = config_dict.get("trace_level", "basic")
        if trace_level not in valid_trace_levels:
            errors.append(ValidationError(
                field="trace_level", 
                message=f"Invalid trace_level '{trace_level}'. Must be one of: {valid_trace_levels}",
                suggestion=f"Use 'basic' for lightweight tracing, 'detailed' for comprehensive debugging",
                error_code="INVALID_VALUE"
            ))
        
        # Validate environment
        valid_environments = ["development", "staging", "production", "test"]
        environment = config_dict.get("environment", "development")
        if environment not in valid_environments:
            errors.append(ValidationError(
                field="environment",
                message=f"Invalid environment '{environment}'. Must be one of: {valid_environments}",
                suggestion="Use 'development' for local dev, 'production' for live systems",
                error_code="INVALID_VALUE"
            ))
        
        # Validate sampling_rate
        sampling_rate = config_dict.get("sampling_rate", 1.0)
        if not isinstance(sampling_rate, (int, float)) or not 0.0 <= sampling_rate <= 1.0:
            errors.append(ValidationError(
                field="sampling_rate",
                message=f"Invalid sampling_rate '{sampling_rate}'. Must be between 0.0 and 1.0",
                suggestion="Use 1.0 for all traces, 0.1 for 10% sampling to reduce overhead",
                error_code="INVALID_RANGE"
            ))
        
        # Validate max_trace_size
        max_trace_size = config_dict.get("max_trace_size", 10000)
        if not isinstance(max_trace_size, int) or max_trace_size < 100:
            errors.append(ValidationError(
                field="max_trace_size", 
                message=f"Invalid max_trace_size '{max_trace_size}'. Must be integer >= 100",
                suggestion="Use 10000 for detailed tracing, 1000 for lightweight tracing",
                error_code="INVALID_RANGE"
            ))
        
        # Validate timing_precision
        valid_timing = ["microseconds", "milliseconds", "seconds"]
        timing_precision = config_dict.get("timing_precision", "milliseconds")
        if timing_precision not in valid_timing:
            errors.append(ValidationError(
                field="timing_precision",
                message=f"Invalid timing_precision '{timing_precision}'. Must be one of: {valid_timing}",
                suggestion="Use 'milliseconds' for most cases, 'microseconds' for high-precision timing",
                error_code="INVALID_VALUE"
            ))
        
        # Validate log_level
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        log_level = config_dict.get("log_level", "INFO")
        if log_level not in valid_log_levels:
            errors.append(ValidationError(
                field="log_level",
                message=f"Invalid log_level '{log_level}'. Must be one of: {valid_log_levels}",
                suggestion="Use 'INFO' for normal operation, 'DEBUG' for detailed logs",
                error_code="INVALID_VALUE"
            ))
        
        # Validate log_format
        valid_log_formats = ["json", "text", "colored"]
        log_format = config_dict.get("log_format", "json")
        if log_format not in valid_log_formats:
            errors.append(ValidationError(
                field="log_format",
                message=f"Invalid log_format '{log_format}'. Must be one of: {valid_log_formats}",
                suggestion="Use 'json' for production, 'colored' for development",
                error_code="INVALID_VALUE"
            ))
        
        # Validate timeout_seconds
        timeout_seconds = config_dict.get("timeout_seconds", 30)
        if not isinstance(timeout_seconds, int) or timeout_seconds < 1:
            errors.append(ValidationError(
                field="timeout_seconds",
                message=f"Invalid timeout_seconds '{timeout_seconds}'. Must be integer >= 1",
                suggestion="Use 30 for most APIs, increase for slow endpoints",
                error_code="INVALID_RANGE"
            ))
        
        # Validate retry_attempts
        retry_attempts = config_dict.get("retry_attempts", 3)
        if not isinstance(retry_attempts, int) or retry_attempts < 0:
            errors.append(ValidationError(
                field="retry_attempts",
                message=f"Invalid retry_attempts '{retry_attempts}'. Must be integer >= 0",
                suggestion="Use 3 for reliable APIs, 0 to disable retries",
                error_code="INVALID_RANGE"
            ))
        
        # Validate data_retention_days
        retention_days = config_dict.get("data_retention_days", 30)
        if not isinstance(retention_days, int) or retention_days < 1:
            errors.append(ValidationError(
                field="data_retention_days",
                message=f"Invalid data_retention_days '{retention_days}'. Must be integer >= 1",
                suggestion="Use 30 for development, 90+ for production analysis",
                error_code="INVALID_RANGE"
            ))
        
        # Validate cache_directory path
        cache_dir = config_dict.get("cache_directory", "~/.agentdebugger/cache")
        try:
            expanded_path = Path(cache_dir).expanduser()
            # Try to create directory if it doesn't exist
            expanded_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            errors.append(ValidationError(
                field="cache_directory",
                message=f"Invalid cache_directory '{cache_dir}': {str(e)}",
                suggestion="Use absolute path or ensure directory is writable",
                error_code="INVALID_PATH"
            ))
        
        # Validate API endpoint format
        api_endpoint = config_dict.get("api_endpoint", "")
        if api_endpoint and not (api_endpoint.startswith("http://") or 
                               api_endpoint.startswith("https://")):
            errors.append(ValidationError(
                field="api_endpoint",
                message=f"Invalid api_endpoint '{api_endpoint}'. Must start with http:// or https://",
                suggestion="Use 'https://api.agentdebugger.pro' for cloud service",
                error_code="INVALID_FORMAT"
            ))
        
        return len(errors) == 0, errors
    
    def get_effective_config(self) -> Dict[str, Any]:
        """
        Get the final merged configuration as a dictionary.
        Useful for debugging configuration issues or passing to other components.
        
        Returns:
            Dictionary containing all effective configuration values
        """
        config_dict = self.__dict__.copy()
        
        # Expand paths
        config_dict["cache_directory"] = str(Path(self.cache_directory).expanduser())
        
        # Add computed values
        config_dict["_computed"] = {
            "cache_path": Path(config_dict["cache_directory"]),
            "is_production": self.environment == "production",
            "is_development": self.environment == "development",
            "trace_sampling_enabled": self.sampling_rate < 1.0,
            "api_enabled": bool(self.api_key and self.api_endpoint)
        }
        
        return config_dict
    
    def save_config(self, config_path: Union[str, Path], format: str = "json") -> bool:
        """
        Save current configuration to a file.
        
        Args:
            config_path: Path where to save the configuration
            format: Format to save in ('json' or 'yaml')
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            config_dict = {k: v for k, v in self.__dict__.items() 
                          if not k.startswith('_')}
            
            path = Path(config_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(path, 'w') as f:
                if format.lower() == 'yaml':
                    if not HAS_YAML:
                        print("Warning: PyYAML not installed. Saving as JSON instead. Install with: pip install pyyaml")
                        json.dump(config_dict, f, indent=2)
                    else:
                        yaml.dump(config_dict, f, default_flow_style=False, indent=2)
                else:
                    json.dump(config_dict, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error saving config to {config_path}: {e}")
            return False
    
    def __str__(self) -> str:
        """String representation of configuration for debugging."""
        return f"DebugConfig(project_id='{self.project_id}', environment='{self.environment}', trace_level='{self.trace_level}')"
    
    def __repr__(self) -> str:
        """Detailed representation of configuration."""
        return (f"DebugConfig(project_id='{self.project_id}', environment='{self.environment}', "
                f"trace_level='{self.trace_level}', auto_fix={self.auto_fix}, "
                f"cost_tracking={self.cost_tracking})")