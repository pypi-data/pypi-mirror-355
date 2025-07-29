"""
Built-in review steps for the VaahAI code review system.

This package contains built-in review steps that can be used
to check code for various issues.
"""

# Import all built-in review steps to register them
from vaahai.review.steps.built_in.style import LineLength, IndentationConsistency
from vaahai.review.steps.built_in.security import HardcodedSecrets, SQLInjection
from vaahai.review.steps.built_in.performance import InefficientLoops, LargeMemoryUsage

# Export all built-in review steps
__all__ = [
    # Style review steps
    "LineLength",
    "IndentationConsistency",
    
    # Security review steps
    "HardcodedSecrets",
    "SQLInjection",
    
    # Performance review steps
    "InefficientLoops",
    "LargeMemoryUsage",
]
