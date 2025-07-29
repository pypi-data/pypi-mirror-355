"""
Base classes and interfaces for review steps.

This module provides the foundation for creating and managing review steps
in the VaahAI code review system.
"""

from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Union


class ReviewStepCategory(Enum):
    """Categories for review steps."""
    SECURITY = "security"
    STYLE = "style"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    COMPATIBILITY = "compatibility"
    ACCESSIBILITY = "accessibility"
    BEST_PRACTICE = "best_practice"
    GENERAL = "general"


class ReviewStepSeverity(Enum):
    """Severity levels for review steps."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ReviewStep(ABC):
    """
    Base class for all review steps.
    
    A review step represents a specific check or analysis to be performed
    during a code review. Each step has a unique ID, name, description,
    category, and severity level.
    
    Attributes:
        id (str): Unique identifier for the review step
        name (str): Human-readable name of the review step
        description (str): Detailed description of what the step checks for
        category (ReviewStepCategory): Category of the review step
        severity (ReviewStepSeverity): Severity level of issues found by this step
        tags (Set[str]): Optional tags for filtering and organization
        enabled (bool): Whether this step is enabled by default
    """
    
    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        category: ReviewStepCategory,
        severity: ReviewStepSeverity,
        tags: Optional[Set[str]] = None,
        enabled: bool = True,
    ):
        """
        Initialize a review step.
        
        Args:
            id: Unique identifier for the review step
            name: Human-readable name of the review step
            description: Detailed description of what the step checks for
            category: Category of the review step
            severity: Severity level of issues found by this step
            tags: Optional tags for filtering and organization
            enabled: Whether this step is enabled by default
        """
        self.id = id
        self.name = name
        self.description = description
        self.category = category
        self.severity = severity
        self.tags = tags or set()
        self.enabled = enabled
    
    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the review step on the provided context.
        
        Args:
            context: Dictionary containing the context for the review step,
                    such as file paths, code content, etc.
        
        Returns:
            Dictionary containing the results of the review step,
            including any issues found, their locations, and recommendations.
        """
        pass
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the review step to a dictionary representation.
        
        Returns:
            Dictionary representation of the review step.
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "severity": self.severity.value,
            "tags": list(self.tags),
            "enabled": self.enabled,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReviewStep":
        """
        Create a review step from a dictionary representation.
        
        Args:
            data: Dictionary representation of the review step.
        
        Returns:
            A new ReviewStep instance.
        """
        # This is a stub that should be implemented by concrete subclasses
        raise NotImplementedError(
            "from_dict must be implemented by concrete subclasses"
        )
