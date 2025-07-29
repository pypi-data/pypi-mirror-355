"""
Configuration schema for the VaahAI Group Chat Manager.

This module defines the schema for group chat configuration in the VaahAI
configuration system.
"""

from typing import Dict, List, Any, Optional, Union, Callable

# Group chat configuration schema
GROUP_CHAT_SCHEMA = {
    "type": "object",
    "properties": {
        "type": {
            "type": "string",
            "enum": ["round_robin", "selector", "broadcast", "custom"],
            "default": "round_robin",
            "description": "The type of group chat to use"
        },
        "human_input_mode": {
            "type": "string",
            "enum": ["always", "never", "terminate", "feedback"],
            "default": "terminate",
            "description": "When to request human input during the conversation"
        },
        "max_rounds": {
            "type": "integer",
            "minimum": 1,
            "default": 10,
            "description": "Maximum number of conversation rounds"
        },
        "allow_repeat_speaker": {
            "type": "boolean",
            "default": False,
            "description": "Whether to allow the same agent to speak twice in a row"
        },
        "send_introductions": {
            "type": "boolean",
            "default": True,
            "description": "Whether to send agent introductions at the start"
        },
        "speaker_selection_method": {
            "type": "string",
            "enum": ["auto", "random", "manual"],
            "default": "auto",
            "description": "Method for selecting the next speaker"
        },
        "termination": {
            "type": "object",
            "properties": {
                "max_messages": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "Maximum number of messages before termination"
                },
                "completion_indicators": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "Phrases that indicate the conversation is complete"
                }
            },
            "description": "Configuration for conversation termination"
        },
        "message_filter": {
            "type": "object",
            "properties": {
                "excluded_agents": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "Agents whose messages should be filtered out"
                },
                "excluded_content": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "Content patterns that should be filtered out"
                }
            },
            "description": "Configuration for message filtering"
        }
    },
    "additionalProperties": False
}

# Default configuration for group chats
DEFAULT_GROUP_CHAT_CONFIG = {
    "type": "round_robin",
    "human_input_mode": "terminate",
    "max_rounds": 10,
    "allow_repeat_speaker": False,
    "send_introductions": True,
    "speaker_selection_method": "auto",
    "termination": {
        "max_messages": 50,
        "completion_indicators": [
            "Task completed",
            "Solution found"
        ]
    }
}

# Schema for specific group chat types
ROUND_ROBIN_SCHEMA = {
    "type": "object",
    "properties": {
        **GROUP_CHAT_SCHEMA["properties"]
    },
    "additionalProperties": False
}

SELECTOR_SCHEMA = {
    "type": "object",
    "properties": {
        **GROUP_CHAT_SCHEMA["properties"],
        "selector_agent": {
            "type": "string",
            "description": "Name of the agent responsible for selecting the next speaker"
        }
    },
    "required": ["selector_agent"],
    "additionalProperties": False
}

BROADCAST_SCHEMA = {
    "type": "object",
    "properties": {
        **GROUP_CHAT_SCHEMA["properties"]
    },
    "additionalProperties": False
}

CUSTOM_SCHEMA = {
    "type": "object",
    "properties": {
        **GROUP_CHAT_SCHEMA["properties"],
        "custom_class": {
            "type": "string",
            "description": "Fully qualified name of the custom group chat class"
        }
    },
    "required": ["custom_class"],
    "additionalProperties": False
}

# Map of group chat types to their schemas
GROUP_CHAT_TYPE_SCHEMAS = {
    "round_robin": ROUND_ROBIN_SCHEMA,
    "selector": SELECTOR_SCHEMA,
    "broadcast": BROADCAST_SCHEMA,
    "custom": CUSTOM_SCHEMA
}

def validate_group_chat_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate a group chat configuration against the appropriate schema.
    
    Args:
        config: The group chat configuration to validate
        
    Returns:
        The validated configuration with default values filled in
        
    Raises:
        ValueError: If the configuration is invalid
    """
    # Get the group chat type
    chat_type = config.get("type", "round_robin")
    
    # Ensure the type is valid
    if chat_type not in GROUP_CHAT_TYPE_SCHEMAS:
        raise ValueError(f"Invalid group chat type: {chat_type}")
    
    # Get the schema for this type
    schema = GROUP_CHAT_TYPE_SCHEMAS[chat_type]
    
    # TODO: Implement actual schema validation
    # For now, just return the config with defaults filled in
    result = DEFAULT_GROUP_CHAT_CONFIG.copy()
    result.update(config)
    
    return result
