"""
Agent configuration schemas for VaahAI.

This module provides JSON schemas for validating agent configurations.
"""

import json
from typing import Any, Dict, List, Optional, Union


# Base schema for all agents
BASE_AGENT_SCHEMA = {
    "type": "object",
    "properties": {
        "type": {"type": "string"},
        "name": {"type": "string"},
        "description": {"type": "string"},
        "enabled": {"type": "boolean"},
        "config": {"type": "object"},
        "llm": {
            "type": "object",
            "properties": {
                "provider": {"type": "string"},
                "model": {"type": "string"},
                "temperature": {"type": "number", "minimum": 0, "maximum": 1},
                "max_tokens": {"type": "integer", "minimum": 1},
                "top_p": {"type": "number", "minimum": 0, "maximum": 1},
                "frequency_penalty": {"type": "number", "minimum": -2, "maximum": 2},
                "presence_penalty": {"type": "number", "minimum": -2, "maximum": 2}
            }
        },
        "system_message": {"type": "string"},
        "tools": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "enabled": {"type": "boolean"}
                },
                "required": ["name"]
            }
        }
    },
    "required": ["type"]
}


# AutoGen agent schema
AUTOGEN_AGENT_SCHEMA = {
    "type": "object",
    "properties": {
        **BASE_AGENT_SCHEMA["properties"],
        "autogen_config": {
            "type": "object",
            "properties": {
                "human_input_mode": {"type": "string", "enum": ["ALWAYS", "NEVER", "TERMINATE"]},
                "max_consecutive_auto_reply": {"type": "integer", "minimum": 0},
                "is_termination_msg": {"type": "boolean"},
                "code_execution_config": {"type": "object"}
            }
        }
    },
    "required": BASE_AGENT_SCHEMA["required"]
}


# Schema for specific agent types
AGENT_TYPE_SCHEMAS = {
    "hello_world": {
        "type": "object",
        "properties": {
            **BASE_AGENT_SCHEMA["properties"],
            "greeting_style": {"type": "string", "enum": ["formal", "casual", "humorous"]},
            "include_emoji": {"type": "boolean"}
        },
        "required": BASE_AGENT_SCHEMA["required"] + ["greeting_style"]
    },
    "code_executor": {
        "type": "object",
        "properties": {
            **AUTOGEN_AGENT_SCHEMA["properties"],
            "execution_environment": {"type": "string", "enum": ["docker", "local", "sandbox"]},
            "allowed_languages": {"type": "array", "items": {"type": "string"}},
            "timeout_seconds": {"type": "integer", "minimum": 1}
        },
        "required": AUTOGEN_AGENT_SCHEMA["required"] + ["execution_environment"]
    },
    "code_formatter": {
        "type": "object",
        "properties": {
            **BASE_AGENT_SCHEMA["properties"],
            "formatting_rules": {"type": "object"},
            "supported_languages": {"type": "array", "items": {"type": "string"}}
        },
        "required": BASE_AGENT_SCHEMA["required"]
    },
    "code_analyzer": {
        "type": "object",
        "properties": {
            **BASE_AGENT_SCHEMA["properties"],
            "analysis_types": {"type": "array", "items": {"type": "string"}},
            "severity_levels": {"type": "array", "items": {"type": "string"}}
        },
        "required": BASE_AGENT_SCHEMA["required"]
    }
}


def get_schema_for_agent_type(agent_type: str) -> Dict[str, Any]:
    """
    Get the schema for a specific agent type.
    
    Args:
        agent_type: The type identifier for the agent.
        
    Returns:
        Dict[str, Any]: The JSON schema for the agent type.
        
    Raises:
        ValueError: If the agent type has no specific schema.
    """
    if agent_type in AGENT_TYPE_SCHEMAS:
        return AGENT_TYPE_SCHEMAS[agent_type]
    return BASE_AGENT_SCHEMA


def validate_agent_config(agent_type: str, config: Dict[str, Any]) -> List[str]:
    """
    Validate an agent configuration against its schema.
    
    Args:
        agent_type: The type identifier for the agent.
        config: The configuration to validate.
        
    Returns:
        List[str]: A list of validation error messages. Empty if valid.
    """
    try:
        import jsonschema
    except ImportError:
        return ["jsonschema package is required for validation"]
    
    schema = get_schema_for_agent_type(agent_type)
    validator = jsonschema.Draft7Validator(schema)
    errors = list(validator.iter_errors(config))
    
    return [f"{error.path}: {error.message}" for error in errors]


def get_default_config(agent_type: str) -> Dict[str, Any]:
    """
    Get the default configuration for an agent type.
    
    Args:
        agent_type: The type identifier for the agent.
        
    Returns:
        Dict[str, Any]: The default configuration for the agent type.
    """
    defaults = {
        "hello_world": {
            "greeting_style": "casual",
            "include_emoji": True,
            "llm": {
                "temperature": 0.7,
                "max_tokens": 100
            }
        },
        "code_executor": {
            "execution_environment": "docker",
            "timeout_seconds": 30,
            "allowed_languages": ["python", "javascript", "bash"],
            "llm": {
                "temperature": 0.1,
                "max_tokens": 1000
            }
        },
        "code_formatter": {
            "supported_languages": ["python", "javascript", "typescript", "java", "c", "cpp"],
            "llm": {
                "temperature": 0.1,
                "max_tokens": 2000
            }
        },
        "code_analyzer": {
            "analysis_types": ["security", "performance", "style"],
            "severity_levels": ["high", "medium", "low", "info"],
            "llm": {
                "temperature": 0.1,
                "max_tokens": 2000
            }
        }
    }
    
    return defaults.get(agent_type, {})
