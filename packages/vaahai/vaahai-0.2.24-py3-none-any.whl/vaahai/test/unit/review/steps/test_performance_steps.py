"""
Unit tests for performance review steps.
"""

import unittest
from vaahai.review.steps.built_in.performance import InefficientLoops, LargeMemoryUsage


class TestInefficientLoops(unittest.TestCase):
    """Test cases for the InefficientLoops review step."""
    
    def setUp(self):
        """Set up the test case."""
        self.step = InefficientLoops()
    
    def test_initialization(self):
        """Test that the step initializes correctly."""
        self.assertEqual(self.step.id, "inefficient_loops")
        self.assertEqual(self.step.name, "Inefficient Loops")
        self.assertEqual(self.step.category.name, "PERFORMANCE")
        self.assertEqual(self.step.severity.name, "MEDIUM")
        self.assertTrue("performance" in self.step.tags)
        self.assertTrue("loops" in self.step.tags)
        self.assertTrue("optimization" in self.step.tags)
        self.assertTrue(self.step.enabled)
    
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
    
    def test_execute_with_no_issues(self):
        """Test executing the step with code that has no inefficient loops."""
        context = {
            "file_path": "test.py",
            "content": """
def good_loop():
    # Using enumerate instead of range(len())
    for i, item in enumerate(my_list):
        print(i, item)
    
    # Using a list comprehension instead of modifying a list in a loop
    new_list = [item for item in my_list if item > 0]
    
    # Using a copy of the list when modifying
    for item in my_list[:]:
        if item < 0:
            my_list.remove(item)
""",
        }
        
        result = self.step.execute(context)
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["message"], "Found 0 potential inefficient loop patterns")
        self.assertEqual(len(result["issues"]), 0)
    
    def test_execute_with_inefficient_loops(self):
        """Test executing the step with code that has inefficient loops."""
        context = {
            "file_path": "test.py",
            "content": """
def bad_loop():
    # Modifying a list while iterating over it
    for item in my_list:
        if item < 0:
            my_list.remove(item)
    
    # Using range(len()) instead of enumerate
    for i in range(len(my_list)):
        print(i, my_list[i])
    
    # Nested loops with the same iterable
    for i in my_list:
        for j in my_list:
            print(i, j)
""",
        }
        
        result = self.step.execute(context)
        
        self.assertEqual(result["status"], "success")
        self.assertTrue(result["message"].startswith("Found"))
        self.assertTrue(len(result["issues"]) > 0)
        
        # Check that issues contain the expected information
        for issue in result["issues"]:
            self.assertIn("line", issue)
            self.assertIn("column", issue)
            self.assertIn("message", issue)
            self.assertIn("severity", issue)
            self.assertIn("line_content", issue)
            self.assertIn("recommendation", issue)


class TestLargeMemoryUsage(unittest.TestCase):
    """Test cases for the LargeMemoryUsage review step."""
    
    def setUp(self):
        """Set up the test case."""
        self.step = LargeMemoryUsage()
    
    def test_initialization(self):
        """Test that the step initializes correctly."""
        self.assertEqual(self.step.id, "large_memory_usage")
        self.assertEqual(self.step.name, "Large Memory Usage")
        self.assertEqual(self.step.category.name, "PERFORMANCE")
        self.assertEqual(self.step.severity.name, "MEDIUM")
        self.assertTrue("performance" in self.step.tags)
        self.assertTrue("memory" in self.step.tags)
        self.assertTrue("optimization" in self.step.tags)
        self.assertTrue(self.step.enabled)
    
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
    
    def test_execute_with_no_issues(self):
        """Test executing the step with code that has no large memory usage patterns."""
        context = {
            "file_path": "test.py",
            "content": """
def good_memory_usage():
    # Reading a file line by line
    with open('file.txt', 'r') as f:
        for line in f:
            process(line)
    
    # Using a generator expression
    sum_of_squares = sum(x*x for x in range(1000))
    
    # Using itertools for cartesian product
    import itertools
    for a, b in itertools.product(range(100), range(100)):
        print(a, b)
""",
        }
        
        result = self.step.execute(context)
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["message"], "Found 0 potential large memory usage patterns")
        self.assertEqual(len(result["issues"]), 0)
    
    def test_execute_with_large_memory_usage(self):
        """Test executing the step with code that has large memory usage patterns."""
        context = {
            "file_path": "test.py",
            "content": """
def bad_memory_usage():
    # Reading entire file into memory
    with open('large_file.txt', 'r') as f:
        content = f.read()
    
    # Nested list comprehension
    matrix = [[i*j for i in range(1000)] for j in range(1000)]
    
    # Loading large JSON file
    with open('large_file.json', 'r') as f:
        data = json.loads(f.read())
""",
        }
        
        result = self.step.execute(context)
        
        self.assertEqual(result["status"], "success")
        self.assertTrue(result["message"].startswith("Found"))
        self.assertTrue(len(result["issues"]) > 0)
        
        # Check that issues contain the expected information
        for issue in result["issues"]:
            self.assertIn("line", issue)
            self.assertIn("column", issue)
            self.assertIn("message", issue)
            self.assertIn("severity", issue)
            self.assertIn("line_content", issue)
            self.assertIn("recommendation", issue)


if __name__ == "__main__":
    unittest.main()
