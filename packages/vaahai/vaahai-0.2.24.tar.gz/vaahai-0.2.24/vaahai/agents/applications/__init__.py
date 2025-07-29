"""
VaahAI application-specific agent implementations.

This package contains the application-specific agent implementations for the VaahAI project.
Each agent is implemented in its own subpackage with a consistent structure.
"""

# Import commonly used agents for convenience
from vaahai.agents.applications.framework_detection import FrameworkDetectionAgent
from vaahai.agents.applications.language_detection import LanguageDetectionAgent

__all__ = [
    "FrameworkDetectionAgent",
    "LanguageDetectionAgent",
]
