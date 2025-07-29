"""
Unit tests for security review steps.

This module contains tests for the security-related review steps.
"""

import unittest
from typing import Dict, Any

from vaahai.review.steps.built_in.security import HardcodedSecrets, SQLInjection


class TestHardcodedSecrets(unittest.TestCase):
    """Test cases for the HardcodedSecrets review step."""
    
    def setUp(self):
        """Set up the test case."""
        self.step = HardcodedSecrets()
    
    def test_initialization(self):
        """Test initialization of the review step."""
        self.assertEqual(self.step.id, "hardcoded_secrets")
        self.assertEqual(self.step.name, "Hardcoded Secrets")
        self.assertIn("security", self.step.tags)
        self.assertIn("secrets", self.step.tags)
    
    def test_execute_with_no_content(self):
        """Test executing the step with no content."""
        context = {"file_path": "test.py"}
        result = self.step.execute(context)
        
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["message"], "No content provided for review")
        self.assertEqual(len(result["issues"]), 0)
    
    def test_execute_with_no_secrets(self):
        """Test executing the step with code that has no secrets."""
        context = {
            "file_path": "test.py",
            "content": "def test():\n    x = 1\n    return x\n",
        }
        
        result = self.step.execute(context)
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["message"], "Found 0 potential hardcoded secrets")
        self.assertEqual(len(result["issues"]), 0)
    
    def test_execute_with_hardcoded_secrets(self):
        """Test executing the step with code that has hardcoded secrets."""
        context = {
            "file_path": "test.py",
            "content": """
def connect_to_db():
    password = "super_secret_password"
    api_key = "sk_live_1234567890abcdefghijklmnopqrstuvwxyz"
    return connect(password=password, api_key=api_key)
""",
        }
        
        result = self.step.execute(context)
        
        self.assertEqual(result["status"], "success")
        self.assertIn("Found", result["message"])
        self.assertGreater(len(result["issues"]), 0)
        
        # Check that the issues contain the expected information
        for issue in result["issues"]:
            self.assertIn("line", issue)
            self.assertIn("column", issue)
            self.assertIn("message", issue)
            self.assertIn("severity", issue)
            self.assertIn("line_content", issue)
            self.assertIn("recommendation", issue)
            self.assertIn("Potential hardcoded secret found", issue["message"])
    
    def test_execute_with_custom_patterns(self):
        """Test executing the step with custom patterns."""
        # Create a step with a custom pattern to detect credit card numbers
        custom_step = HardcodedSecrets(
            patterns=[r"(?:\d{4}[- ]?){3}\d{4}"]  # Simple credit card pattern
        )
        
        context = {
            "file_path": "test.py",
            "content": """
def process_payment():
    # This is a test credit card number
    card_number = "4111-1111-1111-1111"
    return process(card_number)
""",
        }
        
        result = custom_step.execute(context)
        
        self.assertEqual(result["status"], "success")
        self.assertGreater(len(result["issues"]), 0)
        self.assertIn("4111-1111-1111-1111", result["issues"][0]["line_content"])


class TestSQLInjection(unittest.TestCase):
    """Test cases for the SQLInjection review step."""
    
    def setUp(self):
        """Set up the test case."""
        self.step = SQLInjection()
    
    def test_initialization(self):
        """Test initialization of the review step."""
        self.assertEqual(self.step.id, "sql_injection")
        self.assertEqual(self.step.name, "SQL Injection")
        self.assertIn("security", self.step.tags)
        self.assertIn("sql", self.step.tags)
    
    def test_execute_with_no_content(self):
        """Test executing the step with no content."""
        context = {"file_path": "test.py"}
        result = self.step.execute(context)
        
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["message"], "No content provided for review")
        self.assertEqual(len(result["issues"]), 0)
    
    def test_execute_with_no_sql_injection(self):
        """Test executing the step with code that has no SQL injection vulnerabilities."""
        context = {
            "file_path": "test.py",
            "content": """
def get_user(user_id):
    # Using parameterized query - safe from SQL injection
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    return cursor.fetchone()

def safe_query():
    # No string concatenation or formatting in SQL
    query = "SELECT * FROM users WHERE active = TRUE"
    return cursor.execute(query)
""",
        }
        
        result = self.step.execute(context)
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["message"], "Found 0 potential SQL injection vulnerabilities")
        self.assertEqual(len(result["issues"]), 0)
    
    def test_execute_with_sql_injection(self):
        """Test executing the step with code that has SQL injection vulnerabilities."""
        context = {
            "file_path": "test.py",
            "content": """
def get_user(user_id):
    query = "SELECT * FROM users WHERE id = " + user_id
    cursor.execute(query)
    return cursor.fetchone()

def delete_user(user_id):
    query = f"DELETE FROM users WHERE id = {user_id}"
    cursor.execute(query)
    
def update_user(user_id, name):
    cursor.execute("UPDATE users SET name = '%s' WHERE id = %s" % (name, user_id))
""",
        }
        
        result = self.step.execute(context)
        
        self.assertEqual(result["status"], "success")
        self.assertIn("Found", result["message"])
        self.assertGreater(len(result["issues"]), 0)
        
        # Check that the issues contain the expected information
        for issue in result["issues"]:
            self.assertIn("line", issue)
            self.assertIn("column", issue)
            self.assertIn("message", issue)
            self.assertIn("severity", issue)
            self.assertIn("line_content", issue)
            self.assertIn("recommendation", issue)
            self.assertIn("SQL injection", issue["message"])


if __name__ == "__main__":
    unittest.main()
