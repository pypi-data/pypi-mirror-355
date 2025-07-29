"""
VaahAI code review module.

This module provides components for code review functionality in the VaahAI system.
"""

# Import and expose base classes and registry
from vaahai.review.steps.base import ReviewStep, ReviewStepCategory, ReviewStepSeverity
from vaahai.review.steps.registry import ReviewStepRegistry
from vaahai.review.steps.schema import validate_step_config
from vaahai.review.runner import ReviewRunner

# Import and expose built-in review steps
from vaahai.review.steps.built_in import (
    # Style review steps
    LineLength,
    IndentationConsistency,
    
    # Security review steps
    HardcodedSecrets,
    SQLInjection,
    
    # Performance review steps
    InefficientLoops,
    LargeMemoryUsage,
)

# Export public API
__all__ = [
    # Base classes and registry
    "ReviewStep",
    "ReviewStepCategory",
    "ReviewStepSeverity",
    "ReviewStepRegistry",
    "validate_step_config",
    "ReviewRunner",
    
    # Built-in review steps - Style
    "LineLength",
    "IndentationConsistency",
    
    # Built-in review steps - Security
    "HardcodedSecrets",
    "SQLInjection",
    
    # Built-in review steps - Performance
    "InefficientLoops",
    "LargeMemoryUsage",
]
