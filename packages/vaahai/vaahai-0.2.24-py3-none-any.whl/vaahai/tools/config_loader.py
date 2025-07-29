"""
Tool configuration loader for VaahAI.

This module provides utilities for loading and processing tool configurations.
"""

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

from vaahai.tools.schemas import get_default_config, validate_tool_config


class ToolConfigLoader:
    """
    Loader for tool configurations from various sources.
    """
    
    ENV_VAR_PATTERN = re.compile(r"\$\{([A-Za-z0-9_]+)(?::([^}]*))?\}")
    
    @staticmethod
    def load_from_file(file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Load tool configuration from a file.
        
        Args:
            file_path: Path to the configuration file (YAML or JSON).
            
        Returns:
            Dict[str, Any]: The loaded configuration.
            
        Raises:
            FileNotFoundError: If the file doesn't exist.
            ValueError: If the file format is not supported or invalid.
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        
        with open(file_path, "r") as f:
            if file_path.suffix.lower() in [".yaml", ".yml"]:
                try:
                    return yaml.safe_load(f)
                except yaml.YAMLError as e:
                    raise ValueError(f"Invalid YAML format: {e}")
            elif file_path.suffix.lower() == ".json":
                try:
                    return json.load(f)
                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid JSON format: {e}")
            else:
                raise ValueError(f"Unsupported file format: {file_path.suffix}")
    
    @staticmethod
    def process_env_vars(config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process environment variables in configuration values.
        
        Args:
            config: The configuration dictionary.
            
        Returns:
            Dict[str, Any]: The processed configuration with environment variables substituted.
        """
        def _process_value(value):
            if isinstance(value, str):
                def _replace_env_var(match):
                    env_var = match.group(1)
                    default = match.group(2)
                    return os.environ.get(env_var, default or "")
                
                return ToolConfigLoader.ENV_VAR_PATTERN.sub(_replace_env_var, value)
            elif isinstance(value, dict):
                return {k: _process_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [_process_value(item) for item in value]
            else:
                return value
        
        return _process_value(config)
    
    @staticmethod
    def merge_configs(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge two configuration dictionaries.
        
        Args:
            base: The base configuration.
            override: The override configuration that takes precedence.
            
        Returns:
            Dict[str, Any]: The merged configuration.
        """
        result = base.copy()
        
        for key, override_value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(override_value, dict):
                result[key] = ToolConfigLoader.merge_configs(result[key], override_value)
            else:
                result[key] = override_value
        
        return result
    
    @staticmethod
    def prepare_tool_config(tool_type: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Prepare a complete tool configuration by merging defaults with provided config.
        
        Args:
            tool_type: The type identifier for the tool.
            config: The user-provided configuration (optional).
            
        Returns:
            Dict[str, Any]: The complete tool configuration.
        """
        # Start with default config for the tool type
        default_config = get_default_config(tool_type)
        
        # Add the tool type to the config
        default_config["type"] = tool_type
        
        # If no user config provided, just return the default
        if not config:
            return default_config
        
        # Merge the user config with the default
        merged_config = ToolConfigLoader.merge_configs(default_config, config)
        
        # Process any environment variables
        processed_config = ToolConfigLoader.process_env_vars(merged_config)
        
        return processed_config
    
    @staticmethod
    def validate_and_prepare_config(tool_type: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Validate and prepare a complete tool configuration.
        
        Args:
            tool_type: The type identifier for the tool.
            config: The user-provided configuration (optional).
            
        Returns:
            Dict[str, Any]: The validated and prepared configuration.
            
        Raises:
            ValueError: If the configuration is invalid.
        """
        prepared_config = ToolConfigLoader.prepare_tool_config(tool_type, config)
        
        # Validate the prepared config
        errors = validate_tool_config(tool_type, prepared_config)
        if errors:
            error_msg = "\n".join(errors)
            raise ValueError(f"Invalid tool configuration for {tool_type}:\n{error_msg}")
        
        return prepared_config
