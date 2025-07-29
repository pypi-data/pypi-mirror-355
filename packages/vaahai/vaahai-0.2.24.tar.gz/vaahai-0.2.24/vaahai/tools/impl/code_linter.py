"""
Code linter tool for VaahAI.

This module provides a tool for linting code and identifying potential issues.
"""

import re
from typing import Any, Dict, List, Optional, Union

from vaahai.tools.base import ToolBase, ToolRegistry


@ToolRegistry.register("code_linter")
class CodeLinterTool(ToolBase):
    """
    Tool for linting code and identifying potential issues.
    
    This tool analyzes code for style issues, potential bugs, and other problems
    based on configurable rules.
    """
    
    # Tool metadata
    input_type = "code"
    output_type = "lint_results"
    version = "0.1.0"
    author = "VaahAI"
    tags = ["code_quality", "linting", "static_analysis"]
    requirements = ["flake8>=6.0.0"]
    
    # Simple patterns for demonstration purposes
    PATTERNS = {
        "error": [
            (r"except\s*:", "Bare except clause"),
            (r"from\s+\S+\s+import\s+\*", "Wildcard import"),
            (r"exec\(", "Use of exec()"),
        ],
        "warning": [
            (r"print\s*\(", "Use of print() statement"),
            (r"#\s*TODO", "TODO comment"),
            (r"global\s+\w+", "Use of global statement"),
        ],
        "info": [
            (r"#\s*FIXME", "FIXME comment"),
            (r"#\s*NOTE", "NOTE comment"),
            (r"#\s*HACK", "HACK comment"),
        ],
    }
    
    def _validate_config(self) -> None:
        """
        Validate the tool configuration.
        
        Raises:
            ValueError: If the configuration is invalid.
        """
        if "severity_levels" in self.config:
            severity_levels = self.config["severity_levels"]
            if not isinstance(severity_levels, list):
                raise ValueError("severity_levels must be a list")
            
            valid_levels = ["error", "warning", "info"]
            for level in severity_levels:
                if level not in valid_levels:
                    raise ValueError(f"Invalid severity level: {level}. Valid levels are: {', '.join(valid_levels)}")
        
        if "ignore_patterns" in self.config and not isinstance(self.config["ignore_patterns"], list):
            raise ValueError("ignore_patterns must be a list")
    
    def execute(self, input_data: Union[str, Dict[str, str]]) -> Dict[str, Any]:
        """
        Execute the linter on the given code.
        
        Args:
            input_data: The code to lint, either as a string or a dictionary mapping
                file names to code content.
            
        Returns:
            Dict[str, Any]: The linting results.
            
        Raises:
            ValueError: If the input data is invalid.
        """
        # Determine which severity levels to check
        severity_levels = self.config.get("severity_levels", ["error", "warning", "info"])
        ignore_patterns = self.config.get("ignore_patterns", [])
        
        # Convert ignore patterns to compiled regexes
        ignore_regexes = [re.compile(pattern) for pattern in ignore_patterns]
        
        # Process the input data
        if isinstance(input_data, str):
            # Single code string
            results = self._lint_code(input_data, severity_levels, ignore_regexes)
            return {
                "issues": results,
                "summary": {
                    "total": len(results),
                    "by_severity": self._count_by_severity(results),
                }
            }
        elif isinstance(input_data, dict):
            # Multiple files
            all_results = {}
            for file_name, code in input_data.items():
                file_results = self._lint_code(code, severity_levels, ignore_regexes)
                all_results[file_name] = file_results
            
            # Flatten results for summary
            flat_results = [issue for file_results in all_results.values() for issue in file_results]
            
            return {
                "issues_by_file": all_results,
                "summary": {
                    "total": len(flat_results),
                    "by_severity": self._count_by_severity(flat_results),
                    "by_file": {file_name: len(results) for file_name, results in all_results.items()},
                }
            }
        else:
            raise ValueError("Input data must be a string or a dictionary mapping file names to code content")
    
    def _lint_code(self, code: str, severity_levels: List[str], ignore_regexes: List[re.Pattern]) -> List[Dict[str, Any]]:
        """
        Lint the given code.
        
        Args:
            code: The code to lint.
            severity_levels: The severity levels to check.
            ignore_regexes: Patterns to ignore.
            
        Returns:
            List[Dict[str, Any]]: The linting results.
        """
        results = []
        
        # Split the code into lines
        lines = code.split("\n")
        
        # Check each line
        for line_number, line in enumerate(lines, 1):
            # Skip lines that match ignore patterns
            if any(ignore_regex.search(line) for ignore_regex in ignore_regexes):
                continue
            
            # Check each pattern for each severity level
            for severity in severity_levels:
                for pattern, message in self.PATTERNS.get(severity, []):
                    if re.search(pattern, line):
                        results.append({
                            "line": line_number,
                            "column": line.find(re.search(pattern, line).group(0)) + 1,
                            "severity": severity,
                            "message": message,
                            "code": line.strip(),
                        })
        
        return results
    
    def _count_by_severity(self, results: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Count issues by severity.
        
        Args:
            results: The linting results.
            
        Returns:
            Dict[str, int]: Counts by severity.
        """
        counts = {"error": 0, "warning": 0, "info": 0}
        for result in results:
            severity = result.get("severity", "info")
            counts[severity] = counts.get(severity, 0) + 1
        return counts
