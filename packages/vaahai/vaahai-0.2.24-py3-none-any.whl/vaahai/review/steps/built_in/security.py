"""
Security-related review steps.

This module contains review steps that check for security issues in code.
"""

import re
from typing import Any, Dict, List, Optional, Pattern

from vaahai.review.steps.base import ReviewStep, ReviewStepCategory, ReviewStepSeverity
from vaahai.review.steps.registry import ReviewStepRegistry


# Common security patterns to check for
HARDCODED_SECRET_PATTERNS = [
    r'(?i)(\bapi_?key\b|\bauth_?token\b|\bsecret\b|\bpassword\b|\baccess_?key\b)(\s*=\s*|\s*:\s*)(["\'])(?!.*\{\{)(?!.*\$)(?!.*env)([^\'"\s]+)(["\'])',
    r'(?i)(\bapi_?key\b|\bauth_?token\b|\bsecret\b|\bpassword\b|\baccess_?key\b)(\s*=\s*|\s*:\s*)([^\'"\s]+)(?!\s*\()',
]


@ReviewStepRegistry.register("hardcoded_secrets")
class HardcodedSecrets(ReviewStep):
    """
    Check for hardcoded secrets in code.
    
    This review step looks for patterns that might indicate hardcoded
    API keys, passwords, tokens, or other secrets.
    """
    
    def __init__(
        self,
        patterns: Optional[List[str]] = None,
        id: str = "hardcoded_secrets",
        name: str = "Hardcoded Secrets",
        description: str = "Check for hardcoded API keys, passwords, tokens, or other secrets",
        category: ReviewStepCategory = ReviewStepCategory.SECURITY,
        severity: ReviewStepSeverity = ReviewStepSeverity.CRITICAL,
        tags: Optional[set] = None,
        enabled: bool = True,
    ):
        """
        Initialize the hardcoded secrets review step.
        
        Args:
            patterns: Optional list of regex patterns to check for
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
            tags=tags or {"security", "secrets", "credentials"},
            enabled=enabled,
        )
        self.patterns = patterns or HARDCODED_SECRET_PATTERNS
        self.compiled_patterns = [re.compile(pattern) for pattern in self.patterns]
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the hardcoded secrets review step.
        
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
            for pattern in self.compiled_patterns:
                matches = pattern.finditer(line)
                for match in matches:
                    # Extract the variable name and the secret value
                    # Handle different pattern groups safely
                    var_name = "unknown"
                    secret_value = "unknown"
                    
                    # Try to extract variable name and secret value if available in the match
                    if match.lastindex is not None and match.lastindex >= 1:
                        var_name = match.group(1)
                    
                    # For custom patterns that might not have the expected groups
                    if match.lastindex is not None and match.lastindex >= 4:
                        secret_value = match.group(4)
                    elif match.lastindex is not None and match.lastindex >= 3:
                        secret_value = match.group(3)
                    else:
                        # For custom patterns, use the entire match as the secret value
                        secret_value = match.group(0)
                    
                    # Mask the secret value for display
                    if len(secret_value) > 4:
                        masked_value = secret_value[:2] + "*" * (len(secret_value) - 4) + secret_value[-2:]
                    else:
                        masked_value = "****"
                    
                    issues.append({
                        "line": i + 1,
                        "column": match.start() + 1,
                        "message": f"Potential hardcoded secret found: '{var_name}' with value '{masked_value}'",
                        "severity": self.severity.value,
                        "line_content": line,
                        "recommendation": "Store secrets in environment variables or a secure vault",
                    })
        
        return {
            "status": "success",
            "message": f"Found {len(issues)} potential hardcoded secrets",
            "issues": issues,
        }


@ReviewStepRegistry.register("sql_injection")
class SQLInjection(ReviewStep):
    """
    Check for potential SQL injection vulnerabilities.
    
    This review step looks for patterns that might indicate SQL injection
    vulnerabilities, such as string concatenation in SQL queries.
    """
    
    def __init__(
        self,
        id: str = "sql_injection",
        name: str = "SQL Injection",
        description: str = "Check for potential SQL injection vulnerabilities",
        category: ReviewStepCategory = ReviewStepCategory.SECURITY,
        severity: ReviewStepSeverity = ReviewStepSeverity.HIGH,
        tags: Optional[set] = None,
        enabled: bool = True,
    ):
        """
        Initialize the SQL injection review step.
        
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
            tags=tags or {"security", "sql", "injection"},
            enabled=enabled,
        )
        
        # Patterns that might indicate SQL injection vulnerabilities
        self.patterns = [
            # String concatenation in SQL queries
            r'(?i)(select|insert|update|delete|alter|drop|create|truncate).*\+\s*(?![\'"]\s*\+)',
            r'(?i)(select|insert|update|delete|alter|drop|create|truncate).*\%.*\%',
            r'(?i)(select|insert|update|delete|alter|drop|create|truncate).*\{.*\}',
            r'(?i)(select|insert|update|delete|alter|drop|create|truncate).*\$\{.*\}',
            r'(?i)(select|insert|update|delete|alter|drop|create|truncate).*\%s.*\)',
            r'(?i)(select|insert|update|delete|alter|drop|create|truncate).*\%d.*\)',
            r'(?i)(execute|exec)\s*\(\s*[\'"].*\+',
            r'(?i)cursor\.execute\s*\(\s*[\'"].*\+',
            r'(?i)cursor\.execute\s*\(\s*f[\'"]',
        ]
        
        # Patterns for safe SQL usage (to exclude from detection)
        self.safe_patterns = [
            r'cursor\.execute\s*\(\s*[\'"].*[\'"]\s*,\s*\(',  # Parameterized query with tuple
            r'cursor\.execute\s*\(\s*[\'"].*[\'"]\s*,\s*\[',  # Parameterized query with list
            r'cursor\.execute\s*\(\s*[\'"].*[\'"]\s*\)',      # Simple query with no parameters
        ]
        
        self.compiled_patterns = [re.compile(pattern) for pattern in self.patterns]
        self.compiled_safe_patterns = [re.compile(pattern) for pattern in self.safe_patterns]
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the SQL injection review step.
        
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
            # Skip if line matches a safe pattern
            if any(safe_pattern.search(line) for safe_pattern in self.compiled_safe_patterns):
                continue
                
            # Check for vulnerable patterns
            for pattern in self.compiled_patterns:
                if pattern.search(line):
                    issues.append({
                        "line": i + 1,
                        "column": 1,
                        "message": "Potential SQL injection vulnerability detected",
                        "severity": self.severity.value,
                        "line_content": line,
                        "recommendation": "Use parameterized queries or prepared statements",
                    })
                    break  # Only report one issue per line
        
        return {
            "status": "success",
            "message": f"Found {len(issues)} potential SQL injection vulnerabilities",
            "issues": issues,
        }
