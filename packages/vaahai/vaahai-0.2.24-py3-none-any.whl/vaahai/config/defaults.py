"""
Default configuration values for VaahAI.

This module defines the default configuration values used when no user or project
configuration is available. These values serve as the base configuration that gets
overridden by user and project configurations.
"""

DEFAULT_CONFIG = {
    "llm": {
        "provider": "openai",
        "openai": {
            "api_key": "",
            "api_base": "",
            "organization": "",
            "model": "gpt-4",
            "temperature": 0.7,
            "max_tokens": 4000
        },
        "claude": {
            "api_key": "",
            "model": "claude-3-sonnet-20240229",
            "temperature": 0.7,
            "max_tokens": 4000
        },
        "junie": {
            "api_key": "",
            "model": "junie-8b",
            "temperature": 0.7,
            "max_tokens": 4000
        },
        "ollama": {
            "api_base": "http://localhost:11434",
            "model": "llama3",
            "temperature": 0.7,
            "max_tokens": 4000
        }
    },
    "docker": {
        "enabled": True,
        "image": "vaahai/execution:latest",
        "resource_limits": {
            "cpu": 2.0,
            "memory": "2g"
        }
    },
    "output": {
        "format": "terminal",
        "verbosity": "normal",
        "color": True
    },
    "agents": {
        "enabled": ["audit", "review", "security", "quality"],
        "timeout": 300,
        "cache": True,
        "cache_expiration": 24
    },
    "security": {
        "allow_external_code_sharing": False,
        "anonymize_code": True,
        "use_secure_storage": True
    }
}
