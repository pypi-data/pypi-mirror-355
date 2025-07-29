"""
VaahAI Configuration Management.

This package provides configuration management for VaahAI, including:
- Configuration file loading and saving
- Configuration merging from multiple sources
- Environment variable overrides
- Command-line option overrides
"""

from vaahai.config.manager import ConfigManager

__all__ = ["ConfigManager"]
