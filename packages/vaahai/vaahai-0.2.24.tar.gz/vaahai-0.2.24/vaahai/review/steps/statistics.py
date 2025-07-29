"""
Review statistics collection.

This module provides utilities for collecting and aggregating statistics
during code reviews, such as issues found, severity levels, and other metrics.
"""

from collections import Counter, defaultdict
from typing import Dict, List, Any, Optional, Set

from vaahai.review.steps.base import ReviewStepCategory, ReviewStepSeverity


class ReviewStatistics:
    """
    Collects and aggregates statistics during code reviews.
    
    This class provides utilities for tracking and analyzing statistics
    related to issues found during code reviews, such as counts by severity,
    category, and step.
    """
    
    def __init__(self):
        """Initialize the review statistics collector."""
        # Initialize counters for various statistics
        self.total_files = 0
        self.files_with_issues = 0
        self.total_issues = 0
        
        # Counters for issues by severity, category, and step
        self.issues_by_severity: Dict[str, int] = defaultdict(int)
        self.issues_by_category: Dict[str, int] = defaultdict(int)
        self.issues_by_step: Dict[str, int] = defaultdict(int)
        
        # Track unique issues to avoid double-counting
        self.unique_issues: Set[str] = set()
        
        # Track file-specific statistics
        self.file_statistics: Dict[str, Dict[str, Any]] = {}
        
        # Track step-specific statistics
        self.step_statistics: Dict[str, Dict[str, Any]] = {}
        
        # Track most common issues
        self.common_issues: Counter = Counter()
    
    def reset(self) -> None:
        """Reset all statistics."""
        self.__init__()
    
    def add_file(self, file_path: str) -> None:
        """
        Register a file for statistics tracking.
        
        Args:
            file_path: Path to the file being reviewed
        """
        self.total_files += 1
        self.file_statistics[file_path] = {
            "issues": 0,
            "issues_by_severity": defaultdict(int),
            "issues_by_category": defaultdict(int),
            "issues_by_step": defaultdict(int),
        }
    
    def add_issue(
        self,
        step_id: str,
        step_category: str,
        step_severity: str,
        issue: Dict[str, Any],
        file_path: Optional[str] = None,
    ) -> None:
        """
        Add an issue to the statistics.
        
        Args:
            step_id: ID of the review step that found the issue
            step_category: Category of the review step
            step_severity: Severity of the review step
            issue: Dictionary containing issue details
            file_path: Optional path to the file where the issue was found
        """
        # Generate a unique identifier for the issue to avoid double-counting
        issue_id = f"{file_path}:{issue.get('line', 0)}:{issue.get('column', 0)}:{step_id}"
        
        # Skip if we've already counted this issue
        if issue_id in self.unique_issues:
            return
        
        self.unique_issues.add(issue_id)
        
        # Update global counters
        self.total_issues += 1
        
        # Update severity counters
        issue_severity = issue.get("severity", step_severity).lower()
        self.issues_by_severity[issue_severity] += 1
        
        # Update category counters
        self.issues_by_category[step_category] += 1
        
        # Update step counters
        self.issues_by_step[step_id] += 1
        
        # Update common issues counter
        issue_message = issue.get("message", "")
        if issue_message:
            self.common_issues[issue_message] += 1
        
        # Update file-specific statistics if file_path is provided
        if file_path:
            if file_path not in self.file_statistics:
                self.add_file(file_path)
            
            file_stats = self.file_statistics[file_path]
            file_stats["issues"] += 1
            
            if file_stats["issues"] == 1:
                self.files_with_issues += 1
            
            file_stats["issues_by_severity"][issue_severity] += 1
            file_stats["issues_by_category"][step_category] += 1
            file_stats["issues_by_step"][step_id] += 1
        
        # Update step-specific statistics
        if step_id not in self.step_statistics:
            self.step_statistics[step_id] = {
                "issues": 0,
                "category": step_category,
                "severity": step_severity,
            }
        
        self.step_statistics[step_id]["issues"] += 1
    
    def add_step_result(
        self,
        step_id: str,
        step_category: str,
        step_severity: str,
        step_result: Dict[str, Any],
        file_path: Optional[str] = None,
    ) -> None:
        """
        Add a step result to the statistics.
        
        Args:
            step_id: ID of the review step
            step_category: Category of the review step
            step_severity: Severity of the review step
            step_result: Dictionary containing step result details
            file_path: Optional path to the file being reviewed
        """
        # Extract issues from the step result
        issues = step_result.get("issues", [])
        
        # Add each issue to the statistics
        for issue in issues:
            self.add_issue(step_id, step_category, step_severity, issue, file_path)
    
    def get_statistics_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the review statistics.
        
        Returns:
            Dictionary containing the statistics summary
        """
        # Calculate derived statistics
        issues_per_file = self.total_issues / self.total_files if self.total_files > 0 else 0
        files_with_issues_percentage = (self.files_with_issues / self.total_files * 100) if self.total_files > 0 else 0
        
        # Get most common issues (top 10)
        most_common_issues = self.common_issues.most_common(10)
        
        # Sort issues by severity for better reporting
        severity_order = {
            "critical": 0,
            "high": 1,
            "medium": 2,
            "low": 3,
            "info": 4,
        }
        
        sorted_by_severity = sorted(
            self.issues_by_severity.items(),
            key=lambda x: severity_order.get(x[0], 999)
        )
        
        # Create the summary dictionary
        return {
            "total_files": self.total_files,
            "files_with_issues": self.files_with_issues,
            "files_with_issues_percentage": files_with_issues_percentage,
            "total_issues": self.total_issues,
            "issues_per_file": issues_per_file,
            "issues_by_severity": dict(sorted_by_severity),
            "issues_by_category": dict(self.issues_by_category),
            "issues_by_step": dict(self.issues_by_step),
            "most_common_issues": most_common_issues,
            "step_statistics": self.step_statistics,
        }
    
    def get_file_statistics(self, file_path: str) -> Dict[str, Any]:
        """
        Get statistics for a specific file.
        
        Args:
            file_path: Path to the file
        
        Returns:
            Dictionary containing file-specific statistics
        """
        if file_path not in self.file_statistics:
            return {}
        
        return self.file_statistics[file_path]
    
    def get_step_statistics(self, step_id: str) -> Dict[str, Any]:
        """
        Get statistics for a specific review step.
        
        Args:
            step_id: ID of the review step
        
        Returns:
            Dictionary containing step-specific statistics
        """
        if step_id not in self.step_statistics:
            return {}
        
        return self.step_statistics[step_id]
    
    def get_key_findings(self, max_findings: int = 5) -> List[Dict[str, Any]]:
        """
        Get key findings from the review.
        
        This method identifies the most important issues based on severity
        and frequency.
        
        Args:
            max_findings: Maximum number of key findings to return
        
        Returns:
            List of dictionaries containing key findings
        """
        # Prioritize critical and high severity issues
        key_findings = []
        
        # First, add critical issues
        if "critical" in self.issues_by_severity and self.issues_by_severity["critical"] > 0:
            key_findings.append({
                "type": "severity",
                "severity": "critical",
                "count": self.issues_by_severity["critical"],
                "message": f"Found {self.issues_by_severity['critical']} critical issues that require immediate attention",
            })
        
        # Then, add high severity issues
        if "high" in self.issues_by_severity and self.issues_by_severity["high"] > 0:
            key_findings.append({
                "type": "severity",
                "severity": "high",
                "count": self.issues_by_severity["high"],
                "message": f"Found {self.issues_by_severity['high']} high severity issues that should be addressed soon",
            })
        
        # Add most common issues
        for issue_message, count in self.common_issues.most_common(max_findings - len(key_findings)):
            if count > 1:  # Only include issues that appear multiple times
                key_findings.append({
                    "type": "common_issue",
                    "message": issue_message,
                    "count": count,
                })
            
            if len(key_findings) >= max_findings:
                break
        
        # If we still have slots and no duplicates met the threshold, include single-occurrence issues
        if len(key_findings) < max_findings:
            for issue_message, count in self.common_issues.most_common(max_findings - len(key_findings)):
                if count == 1:
                    key_findings.append({
                        "type": "common_issue",
                        "message": issue_message,
                        "count": count,
                    })
                if len(key_findings) >= max_findings:
                    break
        
        return key_findings
