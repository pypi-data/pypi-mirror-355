"""
Configuration utilities for VaahAI CLI.

This module provides utility functions for loading and saving VaahAI configuration.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

import tomli
import tomli_w

# Default configuration directory
DEFAULT_CONFIG_DIR = os.path.expanduser("~/.vaahai")
DEFAULT_CONFIG_FILE = os.path.join(DEFAULT_CONFIG_DIR, "config.toml")


def ensure_config_dir() -> str:
    """
    Ensure the configuration directory exists.

    Returns:
        Path to the configuration directory
    """
    os.makedirs(DEFAULT_CONFIG_DIR, exist_ok=True)
    return DEFAULT_CONFIG_DIR


def get_default_config() -> Dict[str, Any]:
    """
    Get the default configuration.

    Returns:
        Dictionary containing default configuration values
    """
    return {
        "llm": {
            "provider": "openai",
            "model": "gpt-4",
            "api_key": "",
            "temperature": 0.7,
        },
        "agents": {
            "use_docker": False,
            "docker_image": "vaahai/agent-runner:latest",
            "timeout_seconds": 60,
        },
        "output": {
            "format": "terminal",
            "color_enabled": True,
            "verbose": False,
        },
        "paths": {
            "workspace": "",
            "output_dir": "",
        },
    }


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from a TOML file.

    Args:
        config_path: Path to the configuration file (uses default if None)

    Returns:
        Dictionary containing configuration values
    """
    config_path = config_path or DEFAULT_CONFIG_FILE

    # If config doesn't exist, return default config
    if not os.path.exists(config_path):
        return get_default_config()

    # Load and parse the TOML file
    try:
        with open(config_path, "rb") as f:
            config = tomli.load(f)

        # Merge with defaults to ensure all keys exist
        defaults = get_default_config()
        for section in defaults:
            if section not in config:
                config[section] = {}
            for key, value in defaults[section].items():
                if key not in config[section]:
                    config[section][key] = value

        return config
    except Exception as e:
        raise ValueError(f"Error loading configuration: {str(e)}")


def save_config(config: Dict[str, Any], config_path: Optional[str] = None) -> None:
    """
    Save configuration to a TOML file.

    Args:
        config: Dictionary containing configuration values
        config_path: Path to save the configuration file (uses default if None)
    """
    config_path = config_path or DEFAULT_CONFIG_FILE
    ensure_config_dir()

    try:
        with open(config_path, "wb") as f:
            tomli_w.dump(config, f)
    except Exception as e:
        raise ValueError(f"Error saving configuration: {str(e)}")


def get_config_value(key_path: str, config: Optional[Dict[str, Any]] = None) -> Any:
    """
    Get a configuration value using a dot-notation path.

    Args:
        key_path: Dot-notation path to the configuration value (e.g., "llm.provider")
        config: Configuration dictionary (loads from file if None)

    Returns:
        The configuration value at the specified path
    """
    if config is None:
        config = load_config()

    keys = key_path.split(".")
    value = config

    for key in keys:
        if key not in value:
            return None
        value = value[key]

    return value


def set_config_value(
    key_path: str, new_value: Any, config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Set a configuration value using a dot-notation path.

    Args:
        key_path: Dot-notation path to the configuration value (e.g., "llm.provider")
        new_value: The new value to set
        config: Configuration dictionary (loads from file if None)

    Returns:
        Updated configuration dictionary
    """
    if config is None:
        config = load_config()

    keys = key_path.split(".")
    current = config

    # Navigate to the nested dictionary containing the key
    for i, key in enumerate(keys[:-1]):
        if key not in current:
            current[key] = {}
        current = current[key]

    # Set the value
    current[keys[-1]] = new_value

    return config
