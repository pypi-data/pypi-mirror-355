"""
Agent configuration loader for VaahAI.

This module provides utilities for loading and processing agent configurations.
"""

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

from vaahai.agents.schemas import get_default_config, validate_agent_config


class AgentConfigLoader:
    """
    Loader for agent configurations from various sources.
    """
    
    ENV_VAR_PATTERN = re.compile(r"\$\{([A-Za-z0-9_]+)(?::([^}]*))?\}")
    
    @staticmethod
    def load_from_file(file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Load agent configuration from a file.
        
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
                
                return AgentConfigLoader.ENV_VAR_PATTERN.sub(_replace_env_var, value)
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
                result[key] = AgentConfigLoader.merge_configs(result[key], override_value)
            else:
                result[key] = override_value
        
        return result
    
    @staticmethod
    def prepare_agent_config(agent_type: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Prepare a complete agent configuration by merging defaults with provided config.
        
        Args:
            agent_type: The type identifier for the agent.
            config: The user-provided configuration (optional).
            
        Returns:
            Dict[str, Any]: The complete agent configuration.
        """
        # Start with default config for the agent type
        default_config = get_default_config(agent_type)
        
        # Add the agent type to the config
        default_config["type"] = agent_type
        
        # If no user config provided, just return the default
        if not config:
            return default_config
        
        # Merge the user config with the default
        merged_config = AgentConfigLoader.merge_configs(default_config, config)
        
        # Process any environment variables
        processed_config = AgentConfigLoader.process_env_vars(merged_config)
        
        return processed_config
    
    @staticmethod
    def validate_and_prepare_config(agent_type: str, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Validate and prepare a complete agent configuration.
        
        Args:
            agent_type: The type identifier for the agent.
            config: The user-provided configuration (optional).
            
        Returns:
            Dict[str, Any]: The validated and prepared configuration.
            
        Raises:
            ValueError: If the configuration is invalid.
        """
        prepared_config = AgentConfigLoader.prepare_agent_config(agent_type, config)
        
        # Validate the prepared config
        errors = validate_agent_config(agent_type, prepared_config)
        if errors:
            error_msg = "\n".join(errors)
            raise ValueError(f"Invalid agent configuration for {agent_type}:\n{error_msg}")
        
        return prepared_config
