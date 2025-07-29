"""
JSON schema validation for review step configurations.

This module provides schema definitions and validation functions for
review step configurations in the VaahAI code review system.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Union

# Setup logging
logger = logging.getLogger(__name__)

# Schema for review step base configuration
REVIEW_STEP_BASE_SCHEMA = {
    "type": "object",
    "required": ["id", "name", "description", "category", "severity"],
    "properties": {
        "id": {
            "type": "string",
            "description": "Unique identifier for the review step"
        },
        "name": {
            "type": "string",
            "description": "Human-readable name of the review step"
        },
        "description": {
            "type": "string",
            "description": "Detailed description of what the step checks for"
        },
        "category": {
            "type": "string",
            "enum": [
                "security", "style", "performance", "maintainability",
                "compatibility", "accessibility", "best_practice", "general"
            ],
            "description": "Category of the review step"
        },
        "severity": {
            "type": "string",
            "enum": ["critical", "high", "medium", "low", "info"],
            "description": "Severity level of issues found by this step"
        },
        "tags": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "description": "Tags for filtering and organization"
        },
        "enabled": {
            "type": "boolean",
            "description": "Whether this step is enabled by default",
            "default": True
        }
    },
    "additionalProperties": True
}

# Schema for line length step configuration
LINE_LENGTH_SCHEMA = {
    "type": "object",
    "required": ["max_length"],
    "properties": {
        "max_length": {
            "type": "integer",
            "minimum": 1,
            "description": "Maximum allowed line length"
        }
    }
}

# Schema for indentation consistency step configuration
INDENTATION_CONSISTENCY_SCHEMA = {
    "type": "object",
    "properties": {}  # No additional properties required
}

# Map of step IDs to their specific schemas
STEP_SCHEMAS = {
    "line_length": LINE_LENGTH_SCHEMA,
    "indentation_consistency": INDENTATION_CONSISTENCY_SCHEMA,
}


def validate_step_config(step_id: str, config: Dict[str, Any], is_instance_config: bool = True) -> Union[List[str], bool]:
    """
    Validate a review step configuration against its schema.
    
    Args:
        step_id: ID of the review step
        config: Configuration to validate
        is_instance_config: If True, only validate against step-specific schema,
                           otherwise validate against both base and step-specific schemas
    
    Returns:
        If is_instance_config is True: Boolean indicating if the configuration is valid
        If is_instance_config is False: List of validation error messages, empty if valid
    """
    try:
        import jsonschema
    except ImportError:
        logger.warning("jsonschema package not installed, skipping validation")
        return True if is_instance_config else []
    
    errors = []
    
    # Validate against base schema only if not an instance config
    if not is_instance_config:
        try:
            jsonschema.validate(config, REVIEW_STEP_BASE_SCHEMA)
        except jsonschema.exceptions.ValidationError as e:
            errors.append(f"Base schema validation error: {e.message}")
    
    # Validate against step-specific schema if available
    if step_id in STEP_SCHEMAS:
        try:
            # Extract only the properties relevant to the step-specific schema
            step_specific_config = {
                k: v for k, v in config.items()
                if k in STEP_SCHEMAS[step_id].get("properties", {})
            }
            jsonschema.validate(step_specific_config, STEP_SCHEMAS[step_id])
        except jsonschema.exceptions.ValidationError as e:
            if is_instance_config:
                logger.error(f"Step-specific schema validation error: {e.message}")
                return False
            else:
                errors.append(f"Step-specific schema validation error: {e.message}")
    
    return True if is_instance_config else errors


def get_step_schema(step_id: str) -> Dict[str, Any]:
    """
    Get the combined schema for a review step.
    
    Args:
        step_id: ID of the review step
    
    Returns:
        Combined schema for the review step
    """
    # Start with the base schema
    schema = REVIEW_STEP_BASE_SCHEMA.copy()
    
    # Add step-specific properties if available
    if step_id in STEP_SCHEMAS:
        step_schema = STEP_SCHEMAS[step_id]
        for prop_name, prop_schema in step_schema.get("properties", {}).items():
            schema["properties"][prop_name] = prop_schema
        
        # Add required properties from step-specific schema
        if "required" in step_schema:
            schema["required"].extend(step_schema["required"])
    
    return schema
