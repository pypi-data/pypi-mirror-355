"""
Review steps runner.

This module provides utilities for running multiple review steps on code.
"""

import logging
import os
from typing import Any, Dict, List, Optional, Set, Union, Callable

from vaahai.review.steps.base import ReviewStep, ReviewStepCategory, ReviewStepSeverity
from vaahai.review.steps.registry import ReviewStepRegistry
from vaahai.review.steps.progress import ReviewProgress, ReviewStepStatus
from vaahai.review.steps.statistics import ReviewStatistics
from vaahai.review.steps.findings import KeyFindingsReporter

# For output format selection
from vaahai.reporting.formats import OutputFormat

# Setup logging
logger = logging.getLogger(__name__)


class ReviewRunner:
    """
    Runner for executing multiple review steps on code.
    
    This class provides utilities for running multiple review steps on code
    and aggregating the results.
    """
    
    def __init__(
        self,
        steps: Optional[List[Union[str, ReviewStep]]] = None,
        categories: Optional[List[ReviewStepCategory]] = None,
        severities: Optional[List[ReviewStepSeverity]] = None,
        tags: Optional[List[str]] = None,
        enabled_only: bool = True,
    ):
        """
        Initialize the review runner.
        
        Args:
            steps: Optional list of review step IDs or instances to run.
                  If not provided, all steps matching the other criteria will be used.
            categories: Optional list of categories to filter steps by.
            severities: Optional list of severities to filter steps by.
            tags: Optional list of tags to filter steps by.
            enabled_only: If True, only run enabled steps.
        """
        self.step_instances = []
        self.progress = ReviewProgress()
        self.statistics = ReviewStatistics()
        self.findings_reporter = KeyFindingsReporter(self.statistics)
        
        # Get the registry instance
        registry = ReviewStepRegistry()
        
        # If specific steps are provided, use those
        if steps:
            for step in steps:
                if isinstance(step, ReviewStep):
                    self.step_instances.append(step)
                elif isinstance(step, str):
                    step_instance = registry.create_step_instance(step)
                    if step_instance:
                        self.step_instances.append(step_instance)
                    else:
                        logger.warning(f"Review step '{step}' not found or could not be created")
        else:
            # Otherwise, filter steps based on criteria
            filtered_steps = registry.filter_steps(
                category=categories,
                severity=severities,
                tags=tags,
                enabled_only=enabled_only,
            )
            
            # Create instances of the filtered steps
            for step_id, step_class in filtered_steps.items():
                step_instance = registry.create_step_instance(step_id)
                if step_instance:
                    self.step_instances.append(step_instance)
        
        # Register all step instances with the progress tracker
        for step in self.step_instances:
            self.progress.register_step(step.id)
    
    def run_on_content(
        self,
        content: str,
        file_path: Optional[str] = None,
        output_format: OutputFormat = OutputFormat.RICH,
    ) -> Dict[str, Any]:
        """
        Run all review steps on the provided content.
        
        Args:
            content: The code content to review.
            file_path: Optional path to the file being reviewed.
            output_format: Optional output format for the results.
        
        Returns:
            Dictionary containing the aggregated results of all review steps.
        """
        if content is None or not content.strip():
            return {
                "status": "error",
                "message": "No content provided for review",
                "results": [],
                "total_issues": 0,
                "output_format": output_format.value,
            }
        
        context = {
            "content": content,
            "file_path": file_path,
        }
        
        results = []
        total_issues = 0
        
        # Register file with statistics collector if file_path is provided
        if file_path:
            self.statistics.add_file(file_path)
        
        for step in self.step_instances:
            try:
                # Mark step as in progress
                self.progress.start_step(step.id)
                
                # Execute the step
                step_result = step.execute(context)
                step_result["step_id"] = step.id
                step_result["step_name"] = step.name
                step_result["step_category"] = step.category.name
                step_result["step_severity"] = step.severity.name
                
                # Mark step as completed
                self.progress.complete_step(step.id)
                
                # Add duration to the result
                step_result["duration"] = self.progress.get_step_duration(step.id)
                
                # Update statistics with step result
                self.statistics.add_step_result(
                    step.id,
                    step.category.name,
                    step.severity.name,
                    step_result,
                    file_path
                )
                
                results.append(step_result)
                total_issues += len(step_result.get("issues", []))
            except Exception as e:
                logger.error(f"Error running review step '{step.id}': {e}")
                
                # Mark step as failed
                self.progress.fail_step(step.id)
                
                results.append({
                    "step_id": step.id,
                    "step_name": step.name,
                    "step_category": step.category.name if hasattr(step, "category") else "unknown",
                    "step_severity": step.severity.name if hasattr(step, "severity") else "unknown",
                    "status": "error",
                    "message": f"Error running review step: {str(e)}",
                    "issues": [],
                    "duration": self.progress.get_step_duration(step.id),
                })
        
        # Get progress summary
        progress_summary = self.progress.get_progress_summary()
        
        # Get statistics summary
        statistics_summary = self.statistics.get_statistics_summary()
        
        # Generate key findings
        key_findings = self.findings_reporter.generate_findings()
        
        # Generate actionable recommendations
        recommendations = self.findings_reporter.get_actionable_recommendations()
        
        return {
            "status": "success",
            "message": f"Ran {len(results)} review steps, found {total_issues} issues",
            "results": results,
            "total_issues": total_issues,
            "progress": progress_summary,
            "statistics": statistics_summary,
            "key_findings": key_findings,
            "recommendations": recommendations,
            "output_format": output_format.value,
        }
    
    def run_on_file(self, file_path: str, output_format: OutputFormat = OutputFormat.RICH) -> Dict[str, Any]:
        """
        Run all review steps on the specified file.
        
        Args:
            file_path: Path to the file to review.
            output_format: Optional output format for the results.
        
        Returns:
            Dictionary containing the aggregated results of all review steps.
        """
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            return {
                "status": "error",
                "message": f"File not found: {file_path}",
                "results": [],
                "total_issues": 0,
                "output_format": output_format.value,
            }
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            return self.run_on_content(content, file_path, output_format)
        except Exception as e:
            logger.error(f"Error reading file '{file_path}': {e}")
            return {
                "status": "error",
                "message": f"Error reading file: {str(e)}",
                "results": [],
                "total_issues": 0,
                "output_format": output_format.value,
            }
    
    def run_on_directory(
        self,
        directory_path: str,
        file_extensions: Optional[List[str]] = None,
        recursive: bool = True,
        exclude_dirs: Optional[List[str]] = None,
        output_format: OutputFormat = OutputFormat.RICH,
        file_callback: Optional[Callable[[str, str], None]] = None,
    ) -> Dict[str, Any]:
        """
        Run all review steps on files in the specified directory.
        
        Args:
            directory_path: Path to the directory to review.
            file_extensions: Optional list of file extensions to include (e.g., ['.py', '.js']).
                           If not provided, all files will be reviewed.
            recursive: If True, review files in subdirectories as well.
            exclude_dirs: Optional list of directory names to exclude (e.g., ['node_modules', '.git']).
            output_format: Optional output format for the results.
            file_callback: Optional callback function to report file processing progress.
                          The callback receives (file_path, status) where status is one of:
                          "processing", "completed", "failed", or "skipped".
        
        Returns:
            Dictionary containing the aggregated results of all review steps.
        """
        if not os.path.exists(directory_path) or not os.path.isdir(directory_path):
            return {
                "status": "error",
                "message": f"Directory not found: {directory_path}",
                "file_results": [],
                "total_issues": 0,
                "output_format": output_format.value,
            }
        
        # Default exclude dirs
        if exclude_dirs is None:
            exclude_dirs = [".git", "node_modules", "__pycache__", "venv", ".env"]
        
        # Find all files in the directory
        file_paths = []
        for root, dirs, files in os.walk(directory_path):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            # Skip hidden directories (starting with .)
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            
            if not recursive:
                # If not recursive, clear dirs to prevent further traversal
                dirs.clear()
            
            for file in files:
                # Skip hidden files
                if file.startswith("."):
                    continue
                
                file_path = os.path.join(root, file)
                
                # Filter by extension if provided
                if file_extensions:
                    ext = os.path.splitext(file)[1].lower()
                    if ext not in file_extensions:
                        continue
                
                file_paths.append(file_path)
        
        # Run review on each file
        file_results = []
        total_issues = 0
        
        for file_path in file_paths:
            try:
                # Notify about file processing start if callback provided
                if file_callback:
                    file_callback(file_path, "processing")
                
                # Run review on the file
                result = self.run_on_file(file_path, output_format)
                
                if result["status"] == "success":
                    file_results.append({
                        "file_path": file_path,
                        "issues": result.get("total_issues", 0),
                        "results": result.get("results", []),
                    })
                    total_issues += result.get("total_issues", 0)
                    
                    # Notify about file completion if callback provided
                    if file_callback:
                        file_callback(file_path, "completed")
                else:
                    # Notify about file failure if callback provided
                    if file_callback:
                        file_callback(file_path, "failed")
            except Exception as e:
                logger.error(f"Error reviewing file '{file_path}': {e}")
                # Notify about file failure if callback provided
                if file_callback:
                    file_callback(file_path, "failed")
        
        # Get progress summary
        progress_summary = self.progress.get_progress_summary()
        
        # Get statistics summary
        statistics_summary = self.statistics.get_summary()
        
        # Generate key findings
        key_findings = self.findings_reporter.generate_findings()
        
        # Generate actionable recommendations
        recommendations = self.findings_reporter.get_actionable_recommendations()
        
        return {
            "status": "success",
            "message": f"Reviewed {len(file_results)} files, found {total_issues} issues",
            "file_results": file_results,
            "total_issues": total_issues,
            "progress": progress_summary,
            "statistics": statistics_summary,
            "key_findings": key_findings,
            "recommendations": recommendations,
            "output_format": output_format.value,
        }
    
    def get_progress(self) -> ReviewProgress:
        """
        Get the progress tracker.
        
        Returns:
            The progress tracker instance.
        """
        return self.progress
    
    def get_statistics(self) -> ReviewStatistics:
        """
        Get the statistics collector.
        
        Returns:
            The statistics collector instance.
        """
        return self.statistics
    
    def get_key_findings(self, max_findings: int = 10) -> List[Dict[str, Any]]:
        """
        Get key findings from the review.
        
        Args:
            max_findings: Maximum number of findings to return
            
        Returns:
            List of key findings
        """
        return self.findings_reporter.generate_findings(max_findings=max_findings)
    
    def get_recommendations(self) -> List[str]:
        """
        Get actionable recommendations based on the review findings.
        
        Returns:
            List of recommendation strings
        """
        return self.findings_reporter.get_actionable_recommendations()
