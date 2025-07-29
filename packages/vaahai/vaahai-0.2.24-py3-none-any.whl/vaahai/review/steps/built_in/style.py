"""
Style-related review steps.

This module contains review steps that check code style and formatting.
"""

import re
from typing import Any, Dict, List, Optional

from vaahai.review.steps.base import ReviewStep, ReviewStepCategory, ReviewStepSeverity
from vaahai.review.steps.registry import ReviewStepRegistry


@ReviewStepRegistry.register("line_length")
class LineLength(ReviewStep):
    """
    Check if any lines exceed the maximum line length.
    
    This review step checks if any lines in the code exceed a specified
    maximum length, which is configurable.
    """
    
    def __init__(
        self,
        max_length: int = 100,
        id: str = "line_length",
        name: str = "Line Length",
        description: str = "Check if any lines exceed the maximum line length",
        category: ReviewStepCategory = ReviewStepCategory.STYLE,
        severity: ReviewStepSeverity = ReviewStepSeverity.LOW,
        tags: Optional[set] = None,
        enabled: bool = True,
    ):
        """
        Initialize the line length review step.
        
        Args:
            max_length: Maximum allowed line length
            id: Unique identifier for the review step
            name: Human-readable name of the review step
            description: Detailed description of what the step checks for
            category: Category of the review step
            severity: Severity level of issues found by this step
            tags: Optional tags for filtering and organization
            enabled: Whether this step is enabled by default
        """
        super().__init__(
            id=id,
            name=name,
            description=description,
            category=category,
            severity=severity,
            tags=tags or {"style", "formatting", "pep8"},
            enabled=enabled,
        )
        self.max_length = max_length
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the line length review step.
        
        Args:
            context: Dictionary containing the context for the review step,
                    including 'file_path' and 'content' keys.
        
        Returns:
            Dictionary containing the results of the review step,
            including any issues found.
        """
        file_path = context.get("file_path")
        content = context.get("content")
        
        if not content:
            return {
                "status": "error",
                "message": "No content provided for review",
                "issues": [],
            }
        
        lines = content.splitlines()
        issues = []
        
        for i, line in enumerate(lines):
            if len(line.rstrip()) > self.max_length:
                issues.append({
                    "line": i + 1,
                    "column": self.max_length + 1,
                    "message": f"Line exceeds maximum length of {self.max_length} characters",
                    "severity": self.severity.value,
                    "line_content": line,
                })
        
        return {
            "status": "success",
            "message": f"Found {len(issues)} line length issues",
            "issues": issues,
        }


@ReviewStepRegistry.register("indentation_consistency")
class IndentationConsistency(ReviewStep):
    """
    Check if indentation is consistent throughout the code.
    
    This review step checks if the code uses a consistent indentation style
    (spaces or tabs) and size.
    """
    
    def __init__(
        self,
        id: str = "indentation_consistency",
        name: str = "Indentation Consistency",
        description: str = "Check if indentation is consistent throughout the code",
        category: ReviewStepCategory = ReviewStepCategory.STYLE,
        severity: ReviewStepSeverity = ReviewStepSeverity.MEDIUM,
        tags: Optional[set] = None,
        enabled: bool = True,
    ):
        """
        Initialize the indentation consistency review step.
        
        Args:
            id: Unique identifier for the review step
            name: Human-readable name of the review step
            description: Detailed description of what the step checks for
            category: Category of the review step
            severity: Severity level of issues found by this step
            tags: Optional tags for filtering and organization
            enabled: Whether this step is enabled by default
        """
        super().__init__(
            id=id,
            name=name,
            description=description,
            category=category,
            severity=severity,
            tags=tags or {"style", "formatting", "indentation", "pep8"},
            enabled=enabled,
        )
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the indentation consistency review step.
        
        Args:
            context: Dictionary containing the context for the review step,
                    including 'file_path' and 'content' keys.
        
        Returns:
            Dictionary containing the results of the review step,
            including any issues found.
        """
        file_path = context.get("file_path")
        content = context.get("content")
        
        if not content:
            return {
                "status": "error",
                "message": "No content provided for review",
                "issues": [],
            }
        
        lines = content.splitlines()
        issues = []
        
        # Detect indentation type and size
        space_indents = []
        tab_indents = []
        
        for i, line in enumerate(lines):
            if line.strip() == "":
                continue
            
            # Count leading spaces and tabs
            leading_spaces = len(line) - len(line.lstrip(" "))
            leading_tabs = len(line) - len(line.lstrip("\t"))
            
            if leading_spaces > 0:
                space_indents.append((i + 1, leading_spaces))
            elif leading_tabs > 0:
                tab_indents.append((i + 1, leading_tabs))
        
        # Determine the dominant indentation style
        if len(space_indents) > len(tab_indents):
            # Spaces are dominant
            if len(tab_indents) > 0:
                for line_num, _ in tab_indents:
                    issues.append({
                        "line": line_num,
                        "column": 1,
                        "message": "Inconsistent indentation: tab used instead of spaces",
                        "severity": self.severity.value,
                        "line_content": lines[line_num - 1],
                    })
            
            # Check for consistent space indentation size
            if space_indents:
                # Find the most common indentation size
                indent_sizes = [indent for _, indent in space_indents if indent > 0]
                if indent_sizes:
                    # Get the most common non-zero indentation size
                    from collections import Counter
                    common_indent = Counter(indent_sizes).most_common(1)[0][0]
                    
                    for line_num, indent in space_indents:
                        if indent > 0 and indent % common_indent != 0:
                            issues.append({
                                "line": line_num,
                                "column": 1,
                                "message": f"Inconsistent indentation size: {indent} spaces instead of multiple of {common_indent}",
                                "severity": self.severity.value,
                                "line_content": lines[line_num - 1],
                            })
        
        elif len(tab_indents) > len(space_indents):
            # Tabs are dominant
            if len(space_indents) > 0:
                for line_num, _ in space_indents:
                    issues.append({
                        "line": line_num,
                        "column": 1,
                        "message": "Inconsistent indentation: spaces used instead of tabs",
                        "severity": self.severity.value,
                        "line_content": lines[line_num - 1],
                    })
        
        return {
            "status": "success",
            "message": f"Found {len(issues)} indentation consistency issues",
            "issues": issues,
        }
