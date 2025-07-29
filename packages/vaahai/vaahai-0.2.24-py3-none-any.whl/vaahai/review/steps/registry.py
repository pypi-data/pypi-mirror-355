"""
Review steps registry implementation.

This module provides a registry for managing and accessing review steps
in the VaahAI code review system.
"""

import functools
import logging
from typing import Any, Callable, Dict, List, Optional, Set, Type, Union

from vaahai.review.steps.base import ReviewStep, ReviewStepCategory, ReviewStepSeverity
from vaahai.review.steps.schema import validate_step_config

# Setup logging
logger = logging.getLogger(__name__)


class ReviewStepRegistry:
    """
    Registry for managing and accessing review steps.
    
    This class provides a centralized registry for all review steps in the system.
    It supports registration, lookup, and filtering of review steps.
    
    Attributes:
        _steps (Dict[str, Type[ReviewStep]]): Dictionary mapping step IDs to step classes
    """
    
    _instance = None
    _steps: Dict[str, Type[ReviewStep]] = {}
    
    def __new__(cls):
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super(ReviewStepRegistry, cls).__new__(cls)
        return cls._instance
    
    @classmethod
    def register(cls, step_id: Optional[str] = None) -> Callable:
        """
        Register a review step class with the registry.
        
        This method can be used as a decorator to register review step classes.
        
        Args:
            step_id: Optional ID for the review step. If not provided,
                    the class name will be used.
        
        Returns:
            Decorator function that registers the class.
        """
        def decorator(step_class: Type[ReviewStep]) -> Type[ReviewStep]:
            nonlocal step_id
            if step_id is None:
                step_id = step_class.__name__
            
            if step_id in cls._steps:
                logger.warning(f"Review step with ID '{step_id}' already registered. Overwriting.")
            
            cls._steps[step_id] = step_class
            logger.debug(f"Registered review step: {step_id}")
            return step_class
        
        return decorator
    
    @classmethod
    def get_step(cls, step_id: str) -> Optional[Type[ReviewStep]]:
        """
        Get a review step class by ID.
        
        Args:
            step_id: ID of the review step to retrieve.
        
        Returns:
            The review step class, or None if not found.
        """
        return cls._steps.get(step_id)
    
    @classmethod
    def get_all_steps(cls) -> Dict[str, Type[ReviewStep]]:
        """
        Get all registered review steps.
        
        Returns:
            Dictionary mapping step IDs to step classes.
        """
        return cls._steps.copy()
    
    @classmethod
    def filter_steps(
        cls,
        category: Optional[Union[ReviewStepCategory, List[ReviewStepCategory]]] = None,
        severity: Optional[Union[ReviewStepSeverity, List[ReviewStepSeverity]]] = None,
        tags: Optional[Union[str, List[str]]] = None,
        enabled_only: bool = True,
    ) -> Dict[str, Type[ReviewStep]]:
        """
        Filter review steps based on criteria.
        
        Args:
            category: Filter by category or list of categories.
            severity: Filter by severity or list of severities.
            tags: Filter by tag or list of tags.
            enabled_only: If True, only return enabled steps.
        
        Returns:
            Dictionary mapping step IDs to step classes that match the criteria.
        """
        # Convert single values to lists for consistent handling
        if category and not isinstance(category, list):
            category = [category]
        if severity and not isinstance(severity, list):
            severity = [severity]
        if tags and not isinstance(tags, list):
            tags = [tags]
        
        # Start with all steps
        filtered_steps = cls._steps.copy()
        
        # Apply filters
        if category:
            filtered_steps = {
                step_id: step_class
                for step_id, step_class in filtered_steps.items()
                if any(
                    hasattr(step_class, "category") and step_class.category == cat
                    for cat in category
                )
            }
        
        if severity:
            filtered_steps = {
                step_id: step_class
                for step_id, step_class in filtered_steps.items()
                if any(
                    hasattr(step_class, "severity") and step_class.severity == sev
                    for sev in severity
                )
            }
        
        if tags:
            filtered_steps = {
                step_id: step_class
                for step_id, step_class in filtered_steps.items()
                if hasattr(step_class, "tags") and any(
                    tag in step_class.tags for tag in tags
                )
            }
        
        if enabled_only:
            filtered_steps = {
                step_id: step_class
                for step_id, step_class in filtered_steps.items()
                if hasattr(step_class, "enabled") and step_class.enabled
            }
        
        return filtered_steps
    
    @classmethod
    def create_step_instance(cls, step_id: str, **kwargs) -> Optional[ReviewStep]:
        """
        Create an instance of a review step with the given ID and configuration.
        
        Args:
            step_id: ID of the review step to create
            **kwargs: Configuration parameters for the review step
        
        Returns:
            Instance of the review step, or None if the step ID is not found
            or if the configuration is invalid
        """
        if step_id not in cls._steps:
            logger.warning(f"Review step '{step_id}' not found in registry")
            return None
        
        step_class = cls._steps[step_id]
        
        # Validate the configuration if schema validation is available
        try:
            from vaahai.review.steps.schema import validate_step_config
            
            # Only validate if kwargs are provided
            if kwargs:
                is_valid = validate_step_config(step_id, kwargs, is_instance_config=True)
                if not is_valid:
                    logger.error(f"Invalid configuration for review step '{step_id}'")
                    return None
        except ImportError:
            logger.warning("Schema validation not available, skipping configuration validation")
        except Exception as e:
            logger.error(f"Configuration validation error for step '{step_id}': {e}")
            # Continue with instance creation even if validation fails
        
        try:
            return step_class(**kwargs)
        except Exception as e:
            logger.error(f"Error creating review step '{step_id}': {e}")
            return None
    
    @classmethod
    def validate_step_config(cls, step_id: str, config: Dict[str, Any]) -> List[str]:
        """
        Validate a review step configuration.
        
        Args:
            step_id: ID of the review step.
            config: Configuration to validate.
        
        Returns:
            List of validation error messages, empty if valid.
        """
        return validate_step_config(step_id, config)
