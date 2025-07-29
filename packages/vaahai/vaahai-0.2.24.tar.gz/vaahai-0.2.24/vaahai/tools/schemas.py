"""
Tool schemas for VaahAI.

This module provides schemas and validation functions for tool configurations.
"""

from typing import Any, Dict, List, Optional

# Default configurations for different tool types
DEFAULT_CONFIGS = {
    # Default configuration for all tools
    "default": {
        "type": "",
        "enabled": True,
        "timeout": 60,  # seconds
        "retry": {
            "attempts": 1,
            "backoff": 1.0,
        },
        "cache": {
            "enabled": False,
            "ttl": 3600,  # seconds
        },
    },
    # Default configurations for specific tool types can be added here
    "code_linter": {
        "severity_levels": ["error", "warning", "info"],
        "ignore_patterns": [],
        "config_file": None,
    },
    "static_analyzer": {
        "depth": 3,
        "include_patterns": ["*.py", "*.js", "*.java", "*.c", "*.cpp", "*.h", "*.hpp"],
        "exclude_patterns": ["**/node_modules/**", "**/.git/**", "**/venv/**", "**/__pycache__/**"],
    },
    "security_scanner": {
        "scan_dependencies": True,
        "scan_secrets": True,
        "severity_threshold": "medium",
    },
    "code_metrics": {
        "metrics": ["complexity", "maintainability", "duplication"],
        "threshold": {
            "complexity": 10,
            "maintainability": 65,
            "duplication": 5,
        },
    },
}


def get_default_config(tool_type: str) -> Dict[str, Any]:
    """
    Get the default configuration for a tool type.
    
    Args:
        tool_type: The type identifier for the tool.
        
    Returns:
        Dict[str, Any]: The default configuration for the tool type.
    """
    # Start with the base default config
    config = DEFAULT_CONFIGS["default"].copy()
    
    # Merge with tool-specific default config if available
    if tool_type in DEFAULT_CONFIGS:
        for key, value in DEFAULT_CONFIGS[tool_type].items():
            if isinstance(value, dict) and isinstance(config.get(key), dict):
                config[key].update(value)
            else:
                config[key] = value
    
    return config


def validate_tool_config(tool_type: str, config: Dict[str, Any]) -> List[str]:
    """
    Validate a tool configuration against its schema.
    
    Args:
        tool_type: The type identifier for the tool.
        config: The configuration to validate.
        
    Returns:
        List[str]: A list of validation error messages, empty if valid.
    """
    errors = []
    
    # Check required fields
    if "type" not in config:
        errors.append("Missing required field: type")
    elif config["type"] != tool_type:
        errors.append(f"Tool type mismatch: expected {tool_type}, got {config['type']}")
    
    # Validate common fields
    if "enabled" in config and not isinstance(config["enabled"], bool):
        errors.append("Field 'enabled' must be a boolean")
    
    if "timeout" in config:
        if not isinstance(config["timeout"], (int, float)):
            errors.append("Field 'timeout' must be a number")
        elif config["timeout"] <= 0:
            errors.append("Field 'timeout' must be positive")
    
    if "retry" in config:
        retry = config["retry"]
        if not isinstance(retry, dict):
            errors.append("Field 'retry' must be an object")
        else:
            if "attempts" in retry:
                if not isinstance(retry["attempts"], int):
                    errors.append("Field 'retry.attempts' must be an integer")
                elif retry["attempts"] < 0:
                    errors.append("Field 'retry.attempts' must be non-negative")
            
            if "backoff" in retry:
                if not isinstance(retry["backoff"], (int, float)):
                    errors.append("Field 'retry.backoff' must be a number")
                elif retry["backoff"] <= 0:
                    errors.append("Field 'retry.backoff' must be positive")
    
    if "cache" in config:
        cache = config["cache"]
        if not isinstance(cache, dict):
            errors.append("Field 'cache' must be an object")
        else:
            if "enabled" in cache and not isinstance(cache["enabled"], bool):
                errors.append("Field 'cache.enabled' must be a boolean")
            
            if "ttl" in cache:
                if not isinstance(cache["ttl"], (int, float)):
                    errors.append("Field 'cache.ttl' must be a number")
                elif cache["ttl"] <= 0:
                    errors.append("Field 'cache.ttl' must be positive")
    
    # Validate tool-specific fields
    if tool_type == "code_linter":
        _validate_code_linter_config(config, errors)
    elif tool_type == "static_analyzer":
        _validate_static_analyzer_config(config, errors)
    elif tool_type == "security_scanner":
        _validate_security_scanner_config(config, errors)
    elif tool_type == "code_metrics":
        _validate_code_metrics_config(config, errors)
    
    return errors


def _validate_code_linter_config(config: Dict[str, Any], errors: List[str]) -> None:
    """
    Validate a code linter tool configuration.
    
    Args:
        config: The configuration to validate.
        errors: List to append validation errors to.
    """
    if "severity_levels" in config:
        severity_levels = config["severity_levels"]
        if not isinstance(severity_levels, list):
            errors.append("Field 'severity_levels' must be an array")
        else:
            valid_levels = ["error", "warning", "info"]
            for level in severity_levels:
                if level not in valid_levels:
                    errors.append(f"Invalid severity level: {level}. Valid levels are: {', '.join(valid_levels)}")
    
    if "ignore_patterns" in config and not isinstance(config["ignore_patterns"], list):
        errors.append("Field 'ignore_patterns' must be an array")
    
    if "config_file" in config and config["config_file"] is not None and not isinstance(config["config_file"], str):
        errors.append("Field 'config_file' must be a string or null")


def _validate_static_analyzer_config(config: Dict[str, Any], errors: List[str]) -> None:
    """
    Validate a static analyzer tool configuration.
    
    Args:
        config: The configuration to validate.
        errors: List to append validation errors to.
    """
    if "depth" in config:
        if not isinstance(config["depth"], int):
            errors.append("Field 'depth' must be an integer")
        elif config["depth"] <= 0:
            errors.append("Field 'depth' must be positive")
    
    if "include_patterns" in config and not isinstance(config["include_patterns"], list):
        errors.append("Field 'include_patterns' must be an array")
    
    if "exclude_patterns" in config and not isinstance(config["exclude_patterns"], list):
        errors.append("Field 'exclude_patterns' must be an array")


def _validate_security_scanner_config(config: Dict[str, Any], errors: List[str]) -> None:
    """
    Validate a security scanner tool configuration.
    
    Args:
        config: The configuration to validate.
        errors: List to append validation errors to.
    """
    if "scan_dependencies" in config and not isinstance(config["scan_dependencies"], bool):
        errors.append("Field 'scan_dependencies' must be a boolean")
    
    if "scan_secrets" in config and not isinstance(config["scan_secrets"], bool):
        errors.append("Field 'scan_secrets' must be a boolean")
    
    if "severity_threshold" in config:
        valid_thresholds = ["critical", "high", "medium", "low", "info"]
        if config["severity_threshold"] not in valid_thresholds:
            errors.append(f"Invalid severity threshold: {config['severity_threshold']}. "
                         f"Valid thresholds are: {', '.join(valid_thresholds)}")


def _validate_code_metrics_config(config: Dict[str, Any], errors: List[str]) -> None:
    """
    Validate a code metrics tool configuration.
    
    Args:
        config: The configuration to validate.
        errors: List to append validation errors to.
    """
    if "metrics" in config:
        if not isinstance(config["metrics"], list):
            errors.append("Field 'metrics' must be an array")
        else:
            valid_metrics = ["complexity", "maintainability", "duplication", "coverage", "lines", "comments"]
            for metric in config["metrics"]:
                if metric not in valid_metrics:
                    errors.append(f"Invalid metric: {metric}. Valid metrics are: {', '.join(valid_metrics)}")
    
    if "threshold" in config:
        if not isinstance(config["threshold"], dict):
            errors.append("Field 'threshold' must be an object")
        else:
            for key, value in config["threshold"].items():
                if not isinstance(value, (int, float)):
                    errors.append(f"Threshold '{key}' must be a number")
