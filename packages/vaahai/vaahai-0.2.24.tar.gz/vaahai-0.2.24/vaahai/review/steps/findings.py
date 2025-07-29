"""
Key findings reporter for code reviews.

This module provides utilities for extracting and reporting key findings
from code review results, highlighting the most important issues that
require attention.
"""

from typing import Dict, List, Any, Optional
from collections import defaultdict

from vaahai.review.steps.base import ReviewStepCategory, ReviewStepSeverity
from vaahai.review.steps.statistics import ReviewStatistics


class KeyFindingsReporter:
    """
    Extracts and reports key findings from code review results.
    
    This class analyzes review statistics and results to identify the most
    important issues that require attention, categorizing them by type,
    severity, and impact.
    """
    
    def __init__(self, statistics: Optional[ReviewStatistics] = None):
        """
        Initialize the key findings reporter.
        
        Args:
            statistics: Optional ReviewStatistics instance to use for analysis
        """
        self.statistics = statistics or ReviewStatistics()
        self.findings = []
    
    def set_statistics(self, statistics: ReviewStatistics) -> None:
        """
        Set the statistics instance to use for analysis.
        
        Args:
            statistics: ReviewStatistics instance
        """
        self.statistics = statistics
    
    def generate_findings(self, max_findings: int = 10) -> List[Dict[str, Any]]:
        """
        Generate key findings from the review statistics.
        
        This method analyzes the review statistics and identifies the most
        important issues that require attention, categorizing them by type,
        severity, and impact.
        
        Args:
            max_findings: Maximum number of findings to generate
            
        Returns:
            List of dictionaries containing key findings
        """
        self.findings = []
        
        # Get basic findings from statistics
        if self.statistics:
            self.findings.extend(self.statistics.get_key_findings(max_findings=max_findings))
        
        # Add security findings
        self._add_security_findings()
        
        # Add performance findings
        self._add_performance_findings()
        
        # Add maintainability findings
        self._add_maintainability_findings()
        
        # Add best practice findings
        self._add_best_practice_findings()
        
        # Sort findings by priority
        self._sort_findings_by_priority()
        
        # Limit to max_findings
        return self.findings[:max_findings]
    
    def _add_security_findings(self) -> None:
        """Add security-related findings."""
        if not self.statistics:
            return
        
        # Check for security issues
        security_issues = 0
        for category, count in self.statistics.issues_by_category.items():
            if category.lower() == "security":
                security_issues = count
                break
        
        if security_issues > 0:
            self.findings.append({
                "type": "category",
                "category": "security",
                "count": security_issues,
                "message": f"Found {security_issues} security issues that may pose risks",
                "priority": 1,  # High priority for security issues
            })
    
    def _add_performance_findings(self) -> None:
        """Add performance-related findings."""
        if not self.statistics:
            return
        
        # Check for performance issues
        performance_issues = 0
        for category, count in self.statistics.issues_by_category.items():
            if category.lower() == "performance":
                performance_issues = count
                break
        
        if performance_issues > 0:
            self.findings.append({
                "type": "category",
                "category": "performance",
                "count": performance_issues,
                "message": f"Found {performance_issues} performance issues that may affect efficiency",
                "priority": 2,  # Medium priority for performance issues
            })
    
    def _add_maintainability_findings(self) -> None:
        """Add maintainability-related findings."""
        if not self.statistics:
            return
        
        # Check for maintainability issues (style, complexity, etc.)
        maintainability_issues = 0
        for category, count in self.statistics.issues_by_category.items():
            if category.lower() in ["style", "complexity", "maintainability"]:
                maintainability_issues += count
        
        if maintainability_issues > 0:
            self.findings.append({
                "type": "category",
                "category": "maintainability",
                "count": maintainability_issues,
                "message": f"Found {maintainability_issues} maintainability issues that may affect code quality",
                "priority": 3,  # Lower priority for maintainability issues
            })
    
    def _add_best_practice_findings(self) -> None:
        """Add best practice-related findings."""
        if not self.statistics:
            return
        
        # Check for best practice issues
        best_practice_issues = 0
        for category, count in self.statistics.issues_by_category.items():
            if category.lower() in ["best_practice", "convention"]:
                best_practice_issues += count
        
        if best_practice_issues > 0:
            self.findings.append({
                "type": "category",
                "category": "best_practice",
                "count": best_practice_issues,
                "message": f"Found {best_practice_issues} best practice violations",
                "priority": 4,  # Lowest priority for best practice issues
            })
    
    def _sort_findings_by_priority(self) -> None:
        """Sort findings by priority."""
        # Define priority order for finding types
        type_priority = {
            "severity": 1,
            "category": 2,
            "common_issue": 3,
        }
        
        # Define priority order for severities
        severity_priority = {
            "critical": 1,
            "high": 2,
            "medium": 3,
            "low": 4,
            "info": 5,
        }
        
        def get_priority(finding):
            # Use explicit priority if available
            if "priority" in finding:
                return finding["priority"]
            
            # Otherwise calculate based on type and severity
            type_prio = type_priority.get(finding.get("type", ""), 999)
            
            if finding.get("type") == "severity":
                severity_prio = severity_priority.get(finding.get("severity", ""), 999)
                return type_prio * 10 + severity_prio
            
            return type_prio * 100 + finding.get("count", 0) * -1  # Higher counts get lower (better) priority
        
        self.findings.sort(key=get_priority)
    
    def get_actionable_recommendations(self) -> List[str]:
        """
        Generate actionable recommendations based on key findings.
        
        Returns:
            List of recommendation strings
        """
        recommendations = []
        # Track categories and severities we've already added recommendations for
        added_categories = set()
        added_severities = set()
        # Find if a critical security finding exists and cache its count
        critical_security_finding = next(
            (f for f in self.findings if f.get("type") == "severity" and f.get("severity") == "critical" and f.get("category", "").lower() == "security"),
            None
        )
        has_critical_security = critical_security_finding is not None
        
        # Generate findings first if not already generated
        if not self.findings:
            self.generate_findings()
            
        # Process findings to generate recommendations
        for finding in self.findings:
            if finding.get("type") == "severity":
                severity = finding.get("severity", "")
                count = finding.get("count", 0)
                
                # Skip if we already added a recommendation for this severity
                if severity in added_severities:
                    continue
                added_severities.add(severity)
                
                if severity == "critical":
                    # If this is a critical security issue, mention security in the message
                    if finding.get("category", "").lower() == "security":
                        recommendations.append(f"Address {count} critical security issues immediately to prevent security vulnerabilities")
                    else:
                        recommendations.append(f"Address {count} critical issues immediately")
            
            elif finding.get("type") == "category":
                category = finding.get("category", "")
                count = finding.get("count", 0)
                
                # Skip if we already added a recommendation for this category
                if category in added_categories:
                    continue
                added_categories.add(category)
                
                if category == "security":
                    # If a critical security issue already recommended, skip category-based recommendation
                    if has_critical_security:
                        continue
                    recommendations.append(f"Review and fix {count} security issues to improve code safety")
                elif category == "performance":
                    recommendations.append(f"Optimize {count} performance issues to improve application efficiency")
                elif category == "maintainability":
                    recommendations.append(f"Refactor code to address {count} maintainability issues")
            
            elif finding.get("type") == "common_issue":
                message = finding.get("message", "")
                count = finding.get("count", 0)
                
                if count > 2:  # Only recommend fixing issues that appear multiple times
                    recommendations.append(f"Fix recurring issue: {message} (found {count} times)")
        
        return recommendations[:5]  # Limit to top 5 recommendations
