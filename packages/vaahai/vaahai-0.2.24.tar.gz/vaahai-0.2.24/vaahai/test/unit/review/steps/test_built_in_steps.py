"""
Unit tests for the built-in review steps.

This module contains tests for the built-in review steps in the VaahAI code review system.
"""

import unittest

from vaahai.review.steps import ReviewStepCategory, ReviewStepSeverity
from vaahai.review.steps.built_in import LineLength, IndentationConsistency


class TestLineLength(unittest.TestCase):
    """Test cases for the LineLength review step."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.step = LineLength(max_length=80)
    
    def test_initialization(self):
        """Test initialization of the LineLength step."""
        self.assertEqual(self.step.id, "line_length")
        self.assertEqual(self.step.name, "Line Length")
        self.assertEqual(self.step.category, ReviewStepCategory.STYLE)
        self.assertEqual(self.step.severity, ReviewStepSeverity.LOW)
        self.assertEqual(self.step.max_length, 80)
        self.assertTrue(self.step.enabled)
        self.assertIn("style", self.step.tags)
        self.assertIn("formatting", self.step.tags)
        self.assertIn("pep8", self.step.tags)
    
    def test_execute_with_no_issues(self):
        """Test executing the step with code that has no issues."""
        context = {
            "file_path": "test.py",
            "content": "def test():\n    return True\n",
        }
        
        result = self.step.execute(context)
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["message"], "Found 0 line length issues")
        self.assertEqual(len(result["issues"]), 0)
    
    def test_execute_with_issues(self):
        """Test executing the step with code that has line length issues."""
        context = {
            "file_path": "test.py",
            "content": "def test():\n    return 'This is a very long line that exceeds the maximum line length limit of 80 characters'\n",
        }
        
        result = self.step.execute(context)
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["message"], "Found 1 line length issues")
        self.assertEqual(len(result["issues"]), 1)
        
        issue = result["issues"][0]
        self.assertEqual(issue["line"], 2)
        self.assertEqual(issue["column"], 81)
        self.assertEqual(issue["severity"], "low")
        self.assertIn("exceeds maximum length", issue["message"])
    
    def test_execute_with_no_content(self):
        """Test executing the step with no content."""
        context = {
            "file_path": "test.py",
            "content": None,
        }
        
        result = self.step.execute(context)
        
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["message"], "No content provided for review")
        self.assertEqual(len(result["issues"]), 0)
    
    def test_custom_max_length(self):
        """Test the step with a custom maximum line length."""
        step = LineLength(max_length=40)
        
        context = {
            "file_path": "test.py",
            "content": "def test():\n    return 'This line exceeds 40 characters for sure'\n",
        }
        
        result = step.execute(context)
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["message"], "Found 1 line length issues")
        self.assertEqual(len(result["issues"]), 1)
        
        issue = result["issues"][0]
        self.assertEqual(issue["line"], 2)
        self.assertEqual(issue["column"], 41)
        self.assertIn("exceeds maximum length of 40", issue["message"])


class TestIndentationConsistency(unittest.TestCase):
    """Test cases for the IndentationConsistency review step."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.step = IndentationConsistency()
    
    def test_initialization(self):
        """Test initialization of the IndentationConsistency step."""
        self.assertEqual(self.step.id, "indentation_consistency")
        self.assertEqual(self.step.name, "Indentation Consistency")
        self.assertEqual(self.step.category, ReviewStepCategory.STYLE)
        self.assertEqual(self.step.severity, ReviewStepSeverity.MEDIUM)
        self.assertTrue(self.step.enabled)
        self.assertIn("style", self.step.tags)
        self.assertIn("formatting", self.step.tags)
        self.assertIn("indentation", self.step.tags)
        self.assertIn("pep8", self.step.tags)
    
    def test_execute_with_consistent_spaces(self):
        """Test executing the step with code that has consistent space indentation."""
        context = {
            "file_path": "test.py",
            "content": "def test():\n    if True:\n        return True\n    return False\n",
        }
        
        result = self.step.execute(context)
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["message"], "Found 0 indentation consistency issues")
        self.assertEqual(len(result["issues"]), 0)
    
    def test_execute_with_consistent_tabs(self):
        """Test executing the step with code that has consistent tab indentation."""
        context = {
            "file_path": "test.py",
            "content": "def test():\n\tif True:\n\t\treturn True\n\treturn False\n",
        }
        
        result = self.step.execute(context)
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["message"], "Found 0 indentation consistency issues")
        self.assertEqual(len(result["issues"]), 0)
    
    def test_execute_with_mixed_indentation(self):
        """Test executing the step with code that has mixed indentation."""
        context = {
            "file_path": "test.py",
            "content": "def test():\n    if True:\n\t\treturn True\n    return False\n",
        }
        
        result = self.step.execute(context)
        
        self.assertEqual(result["status"], "success")
        self.assertIn("indentation consistency issues", result["message"])
        self.assertGreater(len(result["issues"]), 0)
        
        issue = result["issues"][0]
        self.assertEqual(issue["line"], 3)
        self.assertEqual(issue["column"], 1)
        self.assertEqual(issue["severity"], "medium")
        self.assertIn("Inconsistent indentation", issue["message"])
    
    def test_execute_with_inconsistent_space_size(self):
        """Test executing the step with code that has inconsistent space indentation size."""
        context = {
            "file_path": "test.py",
            "content": "def test():\n    if True:\n       return True\n    return False\n",
        }
        
        result = self.step.execute(context)
        
        self.assertEqual(result["status"], "success")
        self.assertIn("indentation consistency issues", result["message"])
        self.assertGreater(len(result["issues"]), 0)
    
    def test_execute_with_no_content(self):
        """Test executing the step with no content."""
        context = {
            "file_path": "test.py",
            "content": None,
        }
        
        result = self.step.execute(context)
        
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["message"], "No content provided for review")
        self.assertEqual(len(result["issues"]), 0)


if __name__ == "__main__":
    unittest.main()
