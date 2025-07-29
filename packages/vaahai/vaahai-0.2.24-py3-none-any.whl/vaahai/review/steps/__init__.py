"""
Review steps package for the VaahAI code review system.

This package provides components for defining, registering, and executing
code review steps in the VaahAI system.
"""

# Import and expose base classes and registry
from vaahai.review.steps.base import ReviewStep, ReviewStepCategory, ReviewStepSeverity
from vaahai.review.steps.registry import ReviewStepRegistry
from vaahai.review.steps.schema import validate_step_config, get_step_schema

# Import built-in review steps to register them
import vaahai.review.steps.built_in

# Export public API
__all__ = [
    "ReviewStep",
    "ReviewStepCategory",
    "ReviewStepSeverity",
    "ReviewStepRegistry",
    "validate_step_config",
    "get_step_schema",
]
