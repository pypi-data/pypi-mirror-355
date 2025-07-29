"""
Static analyzer tool for VaahAI.

This module provides a tool for static analysis of code to identify patterns,
dependencies, and structure.
"""

import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

from vaahai.tools.base import ToolBase, ToolRegistry


@ToolRegistry.register("static_analyzer")
class StaticAnalyzerTool(ToolBase):
    """
    Tool for static analysis of code.
    
    This tool analyzes code structure, dependencies, and patterns without
    executing the code.
    """
    
    # Tool metadata
    input_type = "code_structure"
    output_type = "analysis_results"
    version = "0.1.0"
    author = "VaahAI"
    tags = ["code_analysis", "static_analysis", "dependencies"]
    requirements = []
    
    # Simple patterns for demonstration purposes
    IMPORT_PATTERNS = {
        "python": r"^\s*(?:from\s+(\S+)\s+import|import\s+([^,]+))",
        "javascript": r"(?:import\s+.*\s+from\s+['\"]([^'\"]+)['\"]|require\s*\(\s*['\"]([^'\"]+)['\"])",
        "java": r"import\s+([^;]+);",
        "go": r"import\s+(?:\([^)]*\"([^\"]+)\"|\"([^\"]+)\")",
    }
    
    FUNCTION_PATTERNS = {
        "python": r"def\s+(\w+)\s*\(",
        "javascript": r"(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?function|\(.*\)\s*=>\s*{)",
        "java": r"(?:public|private|protected|static|\s) +[\w\<\>\[\]]+\s+(\w+) *\([^\)]*\)",
        "go": r"func\s+(\w+)\s*\(",
    }
    
    CLASS_PATTERNS = {
        "python": r"class\s+(\w+)",
        "javascript": r"class\s+(\w+)",
        "java": r"class\s+(\w+)",
        "go": r"type\s+(\w+)\s+struct",
    }
    
    def _validate_config(self) -> None:
        """
        Validate the tool configuration.
        
        Raises:
            ValueError: If the configuration is invalid.
        """
        if "depth" in self.config:
            if not isinstance(self.config["depth"], int):
                raise ValueError("depth must be an integer")
            if self.config["depth"] <= 0:
                raise ValueError("depth must be positive")
        
        if "include_patterns" in self.config and not isinstance(self.config["include_patterns"], list):
            raise ValueError("include_patterns must be a list")
        
        if "exclude_patterns" in self.config and not isinstance(self.config["exclude_patterns"], list):
            raise ValueError("exclude_patterns must be a list")
    
    def execute(self, input_data: Union[str, Dict[str, str], Dict[str, Any]]) -> Dict[str, Any]:
        """
        Execute the static analyzer on the given code or directory structure.
        
        Args:
            input_data: The code to analyze, either as a string, a dictionary mapping
                file names to code content, or a directory structure representation.
            
        Returns:
            Dict[str, Any]: The analysis results.
            
        Raises:
            ValueError: If the input data is invalid.
        """
        # Get configuration values
        depth = self.config.get("depth", 3)
        include_patterns = self.config.get("include_patterns", ["*.py", "*.js", "*.java", "*.go"])
        exclude_patterns = self.config.get("exclude_patterns", ["**/node_modules/**", "**/.git/**"])
        
        # Process the input data
        if isinstance(input_data, str):
            # Single code string, assume Python for simplicity
            return self._analyze_code(input_data, "python")
        elif isinstance(input_data, dict):
            if all(isinstance(v, str) for v in input_data.values()):
                # Dictionary of file names to code content
                results = {}
                for file_name, code in input_data.items():
                    language = self._detect_language(file_name)
                    results[file_name] = self._analyze_code(code, language)
                
                # Aggregate results
                return self._aggregate_results(results)
            elif "structure" in input_data:
                # Directory structure representation
                return self._analyze_structure(input_data["structure"], depth, include_patterns, exclude_patterns)
            else:
                raise ValueError("Invalid input data format")
        else:
            raise ValueError("Input data must be a string or a dictionary")
    
    def _detect_language(self, file_name: str) -> str:
        """
        Detect the programming language from a file name.
        
        Args:
            file_name: The file name.
            
        Returns:
            str: The detected language.
        """
        ext = os.path.splitext(file_name)[1].lower()
        if ext in [".py", ".pyw"]:
            return "python"
        elif ext in [".js", ".jsx", ".ts", ".tsx"]:
            return "javascript"
        elif ext in [".java"]:
            return "java"
        elif ext in [".go"]:
            return "go"
        else:
            return "unknown"
    
    def _analyze_code(self, code: str, language: str) -> Dict[str, Any]:
        """
        Analyze the given code.
        
        Args:
            code: The code to analyze.
            language: The programming language.
            
        Returns:
            Dict[str, Any]: The analysis results.
        """
        # Split the code into lines
        lines = code.split("\n")
        
        # Find imports
        imports = set()
        import_pattern = self.IMPORT_PATTERNS.get(language)
        if import_pattern:
            for line in lines:
                match = re.search(import_pattern, line)
                if match:
                    # Get the first non-None group
                    import_name = next((g for g in match.groups() if g), "")
                    if import_name:
                        imports.add(import_name)
        
        # Find functions
        functions = []
        function_pattern = self.FUNCTION_PATTERNS.get(language)
        if function_pattern:
            for line_number, line in enumerate(lines, 1):
                match = re.search(function_pattern, line)
                if match:
                    # Get the first non-None group
                    function_name = next((g for g in match.groups() if g), "")
                    if function_name:
                        functions.append({
                            "name": function_name,
                            "line": line_number,
                            "code": line.strip(),
                        })
        
        # Find classes
        classes = []
        class_pattern = self.CLASS_PATTERNS.get(language)
        if class_pattern:
            for line_number, line in enumerate(lines, 1):
                match = re.search(class_pattern, line)
                if match:
                    class_name = match.group(1)
                    classes.append({
                        "name": class_name,
                        "line": line_number,
                        "code": line.strip(),
                    })
        
        # Calculate metrics
        metrics = {
            "lines_of_code": len(lines),
            "non_empty_lines": sum(1 for line in lines if line.strip()),
            "comment_lines": sum(1 for line in lines if line.strip().startswith("#") or line.strip().startswith("//") or line.strip().startswith("/*")),
            "function_count": len(functions),
            "class_count": len(classes),
            "import_count": len(imports),
        }
        
        return {
            "language": language,
            "imports": list(imports),
            "functions": functions,
            "classes": classes,
            "metrics": metrics,
        }
    
    def _analyze_structure(self, structure: Dict[str, Any], depth: int, include_patterns: List[str], exclude_patterns: List[str]) -> Dict[str, Any]:
        """
        Analyze a directory structure.
        
        Args:
            structure: The directory structure representation.
            depth: The maximum depth to analyze.
            include_patterns: Patterns of files to include.
            exclude_patterns: Patterns of files to exclude.
            
        Returns:
            Dict[str, Any]: The analysis results.
        """
        # This is a simplified implementation for demonstration purposes
        results = {
            "file_count": 0,
            "directory_count": 0,
            "languages": {},
            "file_types": {},
            "largest_files": [],
            "deepest_paths": [],
        }
        
        def should_include(path: str) -> bool:
            """Check if a path should be included based on patterns."""
            # Check exclude patterns first
            if any(Path(path).match(pattern) for pattern in exclude_patterns):
                return False
            # Then check include patterns
            return any(Path(path).match(pattern) for pattern in include_patterns)
        
        def process_node(node: Dict[str, Any], path: str, current_depth: int) -> None:
            """Process a node in the directory structure."""
            if current_depth > depth:
                return
            
            if node.get("type") == "directory":
                results["directory_count"] += 1
                for name, child in node.get("children", {}).items():
                    process_node(child, f"{path}/{name}", current_depth + 1)
            elif node.get("type") == "file":
                if should_include(path):
                    results["file_count"] += 1
                    
                    # Track file extension
                    ext = os.path.splitext(path)[1].lower() or "no_extension"
                    results["file_types"][ext] = results["file_types"].get(ext, 0) + 1
                    
                    # Track language
                    language = self._detect_language(path)
                    if language != "unknown":
                        results["languages"][language] = results["languages"].get(language, 0) + 1
                    
                    # Track file size
                    size = node.get("size", 0)
                    if len(results["largest_files"]) < 10:
                        results["largest_files"].append({"path": path, "size": size})
                        results["largest_files"].sort(key=lambda x: x["size"], reverse=True)
                    elif size > results["largest_files"][-1]["size"]:
                        results["largest_files"][-1] = {"path": path, "size": size}
                        results["largest_files"].sort(key=lambda x: x["size"], reverse=True)
                    
                    # Track path depth
                    path_depth = len(path.split("/"))
                    if len(results["deepest_paths"]) < 10:
                        results["deepest_paths"].append({"path": path, "depth": path_depth})
                        results["deepest_paths"].sort(key=lambda x: x["depth"], reverse=True)
                    elif path_depth > results["deepest_paths"][-1]["depth"]:
                        results["deepest_paths"][-1] = {"path": path, "depth": path_depth}
                        results["deepest_paths"].sort(key=lambda x: x["depth"], reverse=True)
        
        # Start processing from the root
        process_node(structure, "", 0)
        
        return results
    
    def _aggregate_results(self, file_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate results from multiple files.
        
        Args:
            file_results: Results for individual files.
            
        Returns:
            Dict[str, Any]: Aggregated results.
        """
        languages = {}
        total_lines = 0
        total_functions = 0
        total_classes = 0
        total_imports = set()
        
        for file_name, result in file_results.items():
            language = result.get("language", "unknown")
            languages[language] = languages.get(language, 0) + 1
            
            metrics = result.get("metrics", {})
            total_lines += metrics.get("lines_of_code", 0)
            total_functions += metrics.get("function_count", 0)
            total_classes += metrics.get("class_count", 0)
            
            # Add imports to the set
            total_imports.update(result.get("imports", []))
        
        return {
            "file_count": len(file_results),
            "languages": languages,
            "metrics": {
                "total_lines_of_code": total_lines,
                "total_functions": total_functions,
                "total_classes": total_classes,
                "total_unique_imports": len(total_imports),
            },
            "files": file_results,
        }
