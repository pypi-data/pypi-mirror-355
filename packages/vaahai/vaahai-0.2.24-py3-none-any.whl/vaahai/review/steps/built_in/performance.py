"""
Performance-related review steps.

This module contains review steps that check for performance issues in code.
"""

import re
from typing import Any, Dict, List, Optional, Pattern, Set

from vaahai.review.steps.base import ReviewStep, ReviewStepCategory, ReviewStepSeverity
from vaahai.review.steps.registry import ReviewStepRegistry


@ReviewStepRegistry.register("inefficient_loops")
class InefficientLoops(ReviewStep):
    """
    Check for inefficient loop patterns in code.
    
    This review step looks for patterns that might indicate inefficient
    loop usage, such as modifying lists while iterating over them,
    using nested loops where a single loop would suffice, etc.
    """
    
    def __init__(
        self,
        id: str = "inefficient_loops",
        name: str = "Inefficient Loops",
        description: str = "Check for inefficient loop patterns",
        category: ReviewStepCategory = ReviewStepCategory.PERFORMANCE,
        severity: ReviewStepSeverity = ReviewStepSeverity.MEDIUM,
        tags: Optional[Set[str]] = None,
        enabled: bool = True,
    ):
        """
        Initialize the inefficient loops review step.
        
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
            tags=tags or {"performance", "loops", "optimization"},
            enabled=enabled,
        )
        
        # Patterns that might indicate inefficient loop usage
        self.patterns = [
            # Modifying a list while iterating over it
            r'for\s+\w+\s+in\s+(\w+).*\1\.(append|remove|pop|insert)',
            # Using range(len(list)) instead of enumerate
            r'for\s+\w+\s+in\s+range\s*\(\s*len\s*\(\s*\w+\s*\)\s*\)',
            # Nested loops with the same iterable
            r'for\s+\w+\s+in\s+(\w+).*for\s+\w+\s+in\s+\1',
            # Multiple iterations over the same list
            r'for\s+\w+\s+in\s+(\w+).*for\s+\w+\s+in\s+\1',
        ]
        self.compiled_patterns = [re.compile(pattern) for pattern in self.patterns]
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the inefficient loops review step.
        
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
        
        issues = []
        
        # Check for inefficient loop patterns in the entire content
        for i, pattern in enumerate(self.compiled_patterns):
            matches = pattern.finditer(content)
            for match in matches:
                # Find the line number by counting newlines up to the match position
                line_number = content[:match.start()].count('\n') + 1
                
                # Get the line content
                lines = content.splitlines()
                line_content = lines[line_number - 1] if line_number <= len(lines) else ""
                
                # Determine the specific issue and recommendation
                issue_type = i % len(self.patterns)
                if issue_type == 0:
                    message = "Modifying a list while iterating over it can cause unexpected behavior"
                    recommendation = "Use a copy of the list for iteration or create a new list"
                elif issue_type == 1:
                    message = "Using range(len(list)) is less readable and efficient than enumerate()"
                    recommendation = "Use 'for i, item in enumerate(my_list)' instead"
                elif issue_type == 2:
                    message = "Nested loops with the same iterable may indicate an O(n²) operation"
                    recommendation = "Consider using a more efficient algorithm or data structure"
                else:
                    message = "Potential inefficient loop pattern detected"
                    recommendation = "Review the loop logic for optimization opportunities"
                
                issues.append({
                    "line": line_number,
                    "column": match.start() - content.rfind('\n', 0, match.start()),
                    "message": message,
                    "severity": self.severity.value,
                    "line_content": line_content,
                    "recommendation": recommendation,
                })
        
        return {
            "status": "success",
            "message": f"Found {len(issues)} potential inefficient loop patterns",
            "issues": issues,
        }


@ReviewStepRegistry.register("large_memory_usage")
class LargeMemoryUsage(ReviewStep):
    """
    Check for patterns that might lead to excessive memory usage.
    
    This review step looks for patterns that might indicate excessive
    memory usage, such as large list comprehensions, loading large files
    into memory, etc.
    """
    
    def __init__(
        self,
        id: str = "large_memory_usage",
        name: str = "Large Memory Usage",
        description: str = "Check for patterns that might lead to excessive memory usage",
        category: ReviewStepCategory = ReviewStepCategory.PERFORMANCE,
        severity: ReviewStepSeverity = ReviewStepSeverity.MEDIUM,
        tags: Optional[Set[str]] = None,
        enabled: bool = True,
    ):
        """
        Initialize the large memory usage review step.
        
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
            tags=tags or {"performance", "memory", "optimization"},
            enabled=enabled,
        )
        
        # Patterns that might indicate excessive memory usage
        self.patterns = [
            # Reading entire file into memory
            r'(?:read|readlines)\s*\(\s*\)',
            # Large list comprehensions
            r'\[\s*.*\s+for\s+.*\s+in\s+.*\s+for\s+.*\s+in\s+.*\]',
            # Creating large dictionaries
            r'\{\s*.*\s+for\s+.*\s+in\s+.*\s+for\s+.*\s+in\s+.*\}',
            # Loading large JSON files
            r'json\.loads?\s*\(\s*.*read\s*\(\s*\)\s*\)',
        ]
        self.compiled_patterns = [re.compile(pattern) for pattern in self.patterns]
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the large memory usage review step.
        
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
        
        issues = []
        
        # Check for patterns that might indicate excessive memory usage
        for i, pattern in enumerate(self.compiled_patterns):
            matches = pattern.finditer(content)
            for match in matches:
                # Find the line number by counting newlines up to the match position
                line_number = content[:match.start()].count('\n') + 1
                
                # Get the line content
                lines = content.splitlines()
                line_content = lines[line_number - 1] if line_number <= len(lines) else ""
                
                # Determine the specific issue and recommendation
                issue_type = i % len(self.patterns)
                if issue_type == 0:
                    message = "Reading entire file into memory can lead to excessive memory usage"
                    recommendation = "Consider using a generator or iterating over the file line by line"
                elif issue_type == 1 or issue_type == 2:
                    message = "Nested comprehensions can create large intermediate data structures"
                    recommendation = "Consider using generators or itertools for memory efficiency"
                elif issue_type == 3:
                    message = "Loading large JSON files into memory can lead to excessive memory usage"
                    recommendation = "Consider using a streaming JSON parser for large files"
                else:
                    message = "Potential large memory usage pattern detected"
                    recommendation = "Review the code for memory optimization opportunities"
                
                issues.append({
                    "line": line_number,
                    "column": match.start() - content.rfind('\n', 0, match.start()),
                    "message": message,
                    "severity": self.severity.value,
                    "line_content": line_content,
                    "recommendation": recommendation,
                })
        
        return {
            "status": "success",
            "message": f"Found {len(issues)} potential large memory usage patterns",
            "issues": issues,
        }
