"""
Utility functions for VaahAI configuration management.

This module provides utility functions for working with configuration files,
including path resolution, directory creation, and environment variable handling.
"""

import os
import platform
from pathlib import Path
from typing import Optional, Dict, Any


def get_user_config_dir() -> Path:
    """
    Get the user's configuration directory.
    
    Returns:
        Path: Path to the user's configuration directory (~/.vaahai)
    """
    home = Path.home()
    return home / ".vaahai"


def get_project_config_dir() -> Path:
    """
    Get the project's configuration directory.
    
    Returns:
        Path: Path to the project's configuration directory (./.vaahai)
    """
    return Path.cwd() / ".vaahai"


def ensure_config_dir(path: Path) -> None:
    """
    Ensure the configuration directory exists.
    
    Args:
        path (Path): Path to the configuration directory
    """
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        # Set appropriate permissions
        if platform.system() != "Windows":
            os.chmod(path, 0o700)  # Only user can read/write/execute


def get_env_var_name(key: str) -> str:
    """
    Convert a configuration key to an environment variable name.
    
    Args:
        key (str): Configuration key (e.g., "llm.provider")
    
    Returns:
        str: Environment variable name (e.g., "VAAHAI_LLM_PROVIDER")
    """
    return f"VAAHAI_{key.upper().replace('.', '_')}"


def get_env_var(key: str) -> Optional[str]:
    """
    Get the value of an environment variable for a configuration key.
    
    Args:
        key (str): Configuration key (e.g., "llm.provider")
    
    Returns:
        Optional[str]: Environment variable value or None if not set
    """
    env_var_name = get_env_var_name(key)
    return os.environ.get(env_var_name)


def set_nested_value(config: dict, key: str, value) -> None:
    """
    Set a nested value in a dictionary using dot notation.
    
    Args:
        config (dict): Configuration dictionary
        key (str): Key in dot notation (e.g., "llm.provider")
        value: Value to set
    """
    keys = key.split(".")
    current = config
    
    # Navigate to the correct nested dictionary
    for k in keys[:-1]:
        if k not in current or not isinstance(current[k], dict):
            current[k] = {}
        current = current[k]
    
    # Set the value
    current[keys[-1]] = value


def get_nested_value(config: dict, key: str, default=None):
    """
    Get a nested value from a dictionary using dot notation.
    
    Args:
        config (dict): Configuration dictionary
        key (str): Key in dot notation (e.g., "llm.provider")
        default: Default value to return if key not found
    
    Returns:
        Any: Value or default if not found
    """
    keys = key.split(".")
    current = config
    
    for k in keys:
        if isinstance(current, dict) and k in current:
            current = current[k]
        else:
            return default
    
    return current
