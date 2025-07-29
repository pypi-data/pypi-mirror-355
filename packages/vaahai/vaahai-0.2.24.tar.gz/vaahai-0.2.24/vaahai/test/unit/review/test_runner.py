"""
Unit tests for the ReviewRunner class.
"""

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from vaahai.review.runner import ReviewRunner
from vaahai.review.steps.base import ReviewStep, ReviewStepCategory, ReviewStepSeverity
from vaahai.review.steps.registry import ReviewStepRegistry


class MockReviewStep(ReviewStep):
    """Mock review step for testing."""
    
    def __init__(
        self,
        id="mock_step",
        name="Mock Step",
        description="Mock step for testing",
        category=ReviewStepCategory.STYLE,
        severity=ReviewStepSeverity.LOW,
        tags=None,
        enabled=True,
        issues=None,
        should_fail=False,
    ):
        """Initialize the mock review step."""
        super().__init__(
            id=id,
            name=name,
            description=description,
            category=category,
            severity=severity,
            tags=tags or {"test"},
            enabled=enabled,
        )
        self.issues = issues or []
        self.should_fail = should_fail
    
    def execute(self, context):
        """Execute the mock review step."""
        if self.should_fail:
            raise Exception("Mock step failure")
        
        return {
            "status": "success",
            "message": f"Found {len(self.issues)} issues",
            "issues": self.issues,
        }


class TestReviewRunner(unittest.TestCase):
    """Test cases for the ReviewRunner class."""
    
    def setUp(self):
        """Set up the test case."""
        # Create mock review steps
        self.style_step = MockReviewStep(
            id="mock_style",
            name="Mock Style",
            category=ReviewStepCategory.STYLE,
            severity=ReviewStepSeverity.LOW,
            tags={"style", "test"},
            issues=[{"line": 1, "message": "Style issue"}],
        )
        
        self.security_step = MockReviewStep(
            id="mock_security",
            name="Mock Security",
            category=ReviewStepCategory.SECURITY,
            severity=ReviewStepSeverity.HIGH,
            tags={"security", "test"},
            issues=[{"line": 2, "message": "Security issue"}],
        )
        
        self.failing_step = MockReviewStep(
            id="mock_failing",
            name="Mock Failing",
            category=ReviewStepCategory.STYLE,
            severity=ReviewStepSeverity.LOW,
            should_fail=True,
        )
        
        # Create temporary directory and files for testing
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_file_path = os.path.join(self.temp_dir.name, "test.py")
        with open(self.test_file_path, "w") as f:
            f.write("print('Hello, world!')\n")
        
        # Create subdirectory with a file
        self.sub_dir = os.path.join(self.temp_dir.name, "subdir")
        os.makedirs(self.sub_dir)
        self.sub_file_path = os.path.join(self.sub_dir, "subfile.py")
        with open(self.sub_file_path, "w") as f:
            f.write("print('Hello from subdir!')\n")
    
    def tearDown(self):
        """Clean up after the test case."""
        self.temp_dir.cleanup()
    
    @patch.object(ReviewStepRegistry, "create_step_instance")
    def test_init_with_step_ids(self, mock_create_step_instance):
        """Test initializing the runner with step IDs."""
        mock_create_step_instance.side_effect = lambda step_id: {
            "mock_style": self.style_step,
            "mock_security": self.security_step,
        }.get(step_id)
        
        runner = ReviewRunner(steps=["mock_style", "mock_security"])
        
        self.assertEqual(len(runner.step_instances), 2)
        self.assertIn(self.style_step, runner.step_instances)
        self.assertIn(self.security_step, runner.step_instances)
    
    def test_init_with_step_instances(self):
        """Test initializing the runner with step instances."""
        runner = ReviewRunner(steps=[self.style_step, self.security_step])
        
        self.assertEqual(len(runner.step_instances), 2)
        self.assertIn(self.style_step, runner.step_instances)
        self.assertIn(self.security_step, runner.step_instances)
    
    @patch.object(ReviewStepRegistry, "filter_steps")
    @patch.object(ReviewStepRegistry, "create_step_instance")
    def test_init_with_filters(self, mock_create_step_instance, mock_filter_steps):
        """Test initializing the runner with filters."""
        mock_filter_steps.return_value = {
            "mock_style": MockReviewStep,
            "mock_security": MockReviewStep,
        }
        mock_create_step_instance.side_effect = lambda step_id: {
            "mock_style": self.style_step,
            "mock_security": self.security_step,
        }.get(step_id)
        
        runner = ReviewRunner(
            categories=[ReviewStepCategory.STYLE],
            severities=[ReviewStepSeverity.LOW],
            tags=["test"],
        )
        
        mock_filter_steps.assert_called_once()
        self.assertEqual(len(runner.step_instances), 2)
    
    def test_run_on_content(self):
        """Test running review steps on content."""
        runner = ReviewRunner(steps=[self.style_step, self.security_step])
        
        result = runner.run_on_content("print('Hello, world!')", "test.py")
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(len(result["results"]), 2)
        self.assertEqual(result["total_issues"], 2)
        
        # Check that step results include step metadata
        for step_result in result["results"]:
            self.assertIn("step_id", step_result)
            self.assertIn("step_name", step_result)
            self.assertIn("step_category", step_result)
            self.assertIn("step_severity", step_result)
    
    def test_run_on_content_with_failing_step(self):
        """Test running review steps on content with a failing step."""
        runner = ReviewRunner(steps=[self.style_step, self.failing_step])
        
        result = runner.run_on_content("print('Hello, world!')", "test.py")
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(len(result["results"]), 2)
        
        # Check that the failing step result has error status
        failing_result = next(r for r in result["results"] if r["step_id"] == "mock_failing")
        self.assertEqual(failing_result["status"], "error")
        self.assertTrue("Error running review step" in failing_result["message"])
    
    def test_run_on_content_with_empty_content(self):
        """Test running review steps on empty content."""
        runner = ReviewRunner(steps=[self.style_step])
        
        # Empty string with whitespace should be treated as empty
        result = runner.run_on_content("   \n  ")
        
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["message"], "No content provided for review")
        
        # None should be treated as empty
        result = runner.run_on_content(None)
        
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["message"], "No content provided for review")
    
    def test_run_on_file(self):
        """Test running review steps on a file."""
        runner = ReviewRunner(steps=[self.style_step, self.security_step])
        
        result = runner.run_on_file(self.test_file_path)
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(len(result["results"]), 2)
        self.assertEqual(result["total_issues"], 2)
    
    def test_run_on_file_not_found(self):
        """Test running review steps on a non-existent file."""
        runner = ReviewRunner(steps=[self.style_step])
        
        result = runner.run_on_file("non_existent_file.py")
        
        self.assertEqual(result["status"], "error")
        self.assertTrue("File not found" in result["message"])
    
    def test_run_on_directory(self):
        """Test running review steps on a directory."""
        runner = ReviewRunner(steps=[self.style_step, self.security_step])
        
        result = runner.run_on_directory(self.temp_dir.name, file_extensions=[".py"])
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(len(result["file_results"]), 2)  # Two Python files
        self.assertEqual(result["total_issues"], 4)  # 2 issues per file
    
    def test_run_on_directory_non_recursive(self):
        """Test running review steps on a directory without recursion."""
        runner = ReviewRunner(steps=[self.style_step])
        
        result = runner.run_on_directory(
            self.temp_dir.name, file_extensions=[".py"], recursive=False
        )
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(len(result["file_results"]), 1)  # Only the top-level Python file
    
    def test_run_on_directory_with_exclude(self):
        """Test running review steps on a directory with excluded directories."""
        runner = ReviewRunner(steps=[self.style_step])
        
        result = runner.run_on_directory(
            self.temp_dir.name,
            file_extensions=[".py"],
            exclude_dirs=["subdir"],
        )
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(len(result["file_results"]), 1)  # Only the top-level Python file
    
    def test_run_on_directory_not_found(self):
        """Test running review steps on a non-existent directory."""
        runner = ReviewRunner(steps=[self.style_step])
        
        result = runner.run_on_directory("non_existent_directory")
        
        self.assertEqual(result["status"], "error")
        self.assertTrue("Directory not found" in result["message"])


if __name__ == "__main__":
    unittest.main()
