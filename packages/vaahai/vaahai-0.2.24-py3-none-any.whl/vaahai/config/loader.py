"""
Configuration file loading and saving utilities.

This module provides functions for loading and saving TOML configuration files,
with support for atomic file operations to ensure configuration integrity.
"""

import tempfile
import os
import shutil
from pathlib import Path
from typing import Dict, Any

import tomli
import tomli_w


def load_toml(path: Path) -> Dict[str, Any]:
    """
    Load a TOML file.
    
    Args:
        path (Path): Path to the TOML file
    
    Returns:
        Dict[str, Any]: Parsed TOML content or empty dict if file doesn't exist
    """
    if not path.exists():
        return {}

    try:
        with open(path, "rb") as f:
            return tomli.load(f)
    except Exception as e:
        # Log error but don't crash
        print(f"Error loading configuration from {path}: {e}")
        return {}


def save_toml(path: Path, data: Dict[str, Any]) -> bool:
    """
    Save data to a TOML file atomically.
    
    Args:
        path (Path): Path to the TOML file
        data (Dict[str, Any]): Data to save
    
    Returns:
        bool: True if successful, False otherwise
    """
    # Ensure directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    # Create a temporary file
    fd, temp_path = tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as f:
            tomli_w.dump(data, f)

        # Atomically replace the target file
        shutil.move(temp_path, path)
        return True
    except Exception as e:
        # Clean up the temp file
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        # Log error but don't crash
        print(f"Error saving configuration to {path}: {e}")
        return False
