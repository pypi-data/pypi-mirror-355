"""
Unit tests for the review steps registry.

This module contains tests for the ReviewStepRegistry class and related functionality.
"""

import unittest
from unittest.mock import MagicMock, patch

from vaahai.review.steps import ReviewStepRegistry, ReviewStepCategory, ReviewStepSeverity
from vaahai.review.steps.base import ReviewStep


class TestReviewStepRegistry(unittest.TestCase):
    """Test cases for the ReviewStepRegistry class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Clear the registry before each test
        ReviewStepRegistry._steps = {}
    
    def test_singleton_pattern(self):
        """Test that ReviewStepRegistry follows the singleton pattern."""
        registry1 = ReviewStepRegistry()
        registry2 = ReviewStepRegistry()
        self.assertIs(registry1, registry2)
    
    def test_register_decorator(self):
        """Test registering a review step using the decorator."""
        
        @ReviewStepRegistry.register("test_step")
        class TestStep(ReviewStep):
            def __init__(self, **kwargs):
                super().__init__(
                    id="test_step",
                    name="Test Step",
                    description="A test step",
                    category=ReviewStepCategory.GENERAL,
                    severity=ReviewStepSeverity.MEDIUM,
                    **kwargs
                )
            
            def execute(self, context):
                return {"status": "success", "issues": []}
        
        # Check that the step was registered
        self.assertIn("test_step", ReviewStepRegistry.get_all_steps())
        self.assertEqual(ReviewStepRegistry.get_step("test_step"), TestStep)
    
    def test_register_with_default_id(self):
        """Test registering a review step with a default ID."""
        
        @ReviewStepRegistry.register()
        class AnotherTestStep(ReviewStep):
            def __init__(self, **kwargs):
                super().__init__(
                    id="another_test_step",
                    name="Another Test Step",
                    description="Another test step",
                    category=ReviewStepCategory.GENERAL,
                    severity=ReviewStepSeverity.MEDIUM,
                    **kwargs
                )
            
            def execute(self, context):
                return {"status": "success", "issues": []}
        
        # Check that the step was registered with the class name as ID
        self.assertIn("AnotherTestStep", ReviewStepRegistry.get_all_steps())
        self.assertEqual(ReviewStepRegistry.get_step("AnotherTestStep"), AnotherTestStep)
    
    def test_get_step(self):
        """Test getting a review step by ID."""
        
        @ReviewStepRegistry.register("get_test_step")
        class GetTestStep(ReviewStep):
            def __init__(self, **kwargs):
                super().__init__(
                    id="get_test_step",
                    name="Get Test Step",
                    description="A test step for get_step",
                    category=ReviewStepCategory.GENERAL,
                    severity=ReviewStepSeverity.MEDIUM,
                    **kwargs
                )
            
            def execute(self, context):
                return {"status": "success", "issues": []}
        
        # Check that get_step returns the correct class
        self.assertEqual(ReviewStepRegistry.get_step("get_test_step"), GetTestStep)
        
        # Check that get_step returns None for non-existent steps
        self.assertIsNone(ReviewStepRegistry.get_step("non_existent_step"))
    
    def test_get_all_steps(self):
        """Test getting all registered review steps."""
        
        @ReviewStepRegistry.register("step1")
        class Step1(ReviewStep):
            def __init__(self, **kwargs):
                super().__init__(
                    id="step1",
                    name="Step 1",
                    description="Step 1",
                    category=ReviewStepCategory.GENERAL,
                    severity=ReviewStepSeverity.MEDIUM,
                    **kwargs
                )
            
            def execute(self, context):
                return {"status": "success", "issues": []}
        
        @ReviewStepRegistry.register("step2")
        class Step2(ReviewStep):
            def __init__(self, **kwargs):
                super().__init__(
                    id="step2",
                    name="Step 2",
                    description="Step 2",
                    category=ReviewStepCategory.SECURITY,
                    severity=ReviewStepSeverity.HIGH,
                    **kwargs
                )
            
            def execute(self, context):
                return {"status": "success", "issues": []}
        
        # Check that get_all_steps returns all registered steps
        all_steps = ReviewStepRegistry.get_all_steps()
        self.assertEqual(len(all_steps), 2)
        self.assertIn("step1", all_steps)
        self.assertIn("step2", all_steps)
        self.assertEqual(all_steps["step1"], Step1)
        self.assertEqual(all_steps["step2"], Step2)
    
    def test_filter_steps_by_category(self):
        """Test filtering review steps by category."""
        
        @ReviewStepRegistry.register("general_step")
        class GeneralStep(ReviewStep):
            category = ReviewStepCategory.GENERAL
            severity = ReviewStepSeverity.MEDIUM
            enabled = True
            
            def __init__(self, **kwargs):
                super().__init__(
                    id="general_step",
                    name="General Step",
                    description="A general step",
                    category=ReviewStepCategory.GENERAL,
                    severity=ReviewStepSeverity.MEDIUM,
                    **kwargs
                )
            
            def execute(self, context):
                return {"status": "success", "issues": []}
        
        @ReviewStepRegistry.register("security_step")
        class SecurityStep(ReviewStep):
            category = ReviewStepCategory.SECURITY
            severity = ReviewStepSeverity.HIGH
            enabled = True
            
            def __init__(self, **kwargs):
                super().__init__(
                    id="security_step",
                    name="Security Step",
                    description="A security step",
                    category=ReviewStepCategory.SECURITY,
                    severity=ReviewStepSeverity.HIGH,
                    **kwargs
                )
            
            def execute(self, context):
                return {"status": "success", "issues": []}
        
        # Filter by GENERAL category
        general_steps = ReviewStepRegistry.filter_steps(category=ReviewStepCategory.GENERAL)
        self.assertEqual(len(general_steps), 1)
        self.assertIn("general_step", general_steps)
        
        # Filter by SECURITY category
        security_steps = ReviewStepRegistry.filter_steps(category=ReviewStepCategory.SECURITY)
        self.assertEqual(len(security_steps), 1)
        self.assertIn("security_step", security_steps)
        
        # Filter by multiple categories
        multi_steps = ReviewStepRegistry.filter_steps(
            category=[ReviewStepCategory.GENERAL, ReviewStepCategory.SECURITY]
        )
        self.assertEqual(len(multi_steps), 2)
        self.assertIn("general_step", multi_steps)
        self.assertIn("security_step", multi_steps)
    
    def test_filter_steps_by_severity(self):
        """Test filtering review steps by severity."""
        
        @ReviewStepRegistry.register("medium_step")
        class MediumStep(ReviewStep):
            category = ReviewStepCategory.GENERAL
            severity = ReviewStepSeverity.MEDIUM
            enabled = True
            
            def __init__(self, **kwargs):
                super().__init__(
                    id="medium_step",
                    name="Medium Step",
                    description="A medium severity step",
                    category=ReviewStepCategory.GENERAL,
                    severity=ReviewStepSeverity.MEDIUM,
                    **kwargs
                )
            
            def execute(self, context):
                return {"status": "success", "issues": []}
        
        @ReviewStepRegistry.register("high_step")
        class HighStep(ReviewStep):
            category = ReviewStepCategory.SECURITY
            severity = ReviewStepSeverity.HIGH
            enabled = True
            
            def __init__(self, **kwargs):
                super().__init__(
                    id="high_step",
                    name="High Step",
                    description="A high severity step",
                    category=ReviewStepCategory.SECURITY,
                    severity=ReviewStepSeverity.HIGH,
                    **kwargs
                )
            
            def execute(self, context):
                return {"status": "success", "issues": []}
        
        # Filter by MEDIUM severity
        medium_steps = ReviewStepRegistry.filter_steps(severity=ReviewStepSeverity.MEDIUM)
        self.assertEqual(len(medium_steps), 1)
        self.assertIn("medium_step", medium_steps)
        
        # Filter by HIGH severity
        high_steps = ReviewStepRegistry.filter_steps(severity=ReviewStepSeverity.HIGH)
        self.assertEqual(len(high_steps), 1)
        self.assertIn("high_step", high_steps)
    
    def test_filter_steps_by_tags(self):
        """Test filtering review steps by tags."""
        
        @ReviewStepRegistry.register("tag1_step")
        class Tag1Step(ReviewStep):
            category = ReviewStepCategory.GENERAL
            severity = ReviewStepSeverity.MEDIUM
            tags = {"tag1", "common"}
            enabled = True
            
            def __init__(self, **kwargs):
                super().__init__(
                    id="tag1_step",
                    name="Tag1 Step",
                    description="A step with tag1",
                    category=ReviewStepCategory.GENERAL,
                    severity=ReviewStepSeverity.MEDIUM,
                    tags={"tag1", "common"},
                    **kwargs
                )
            
            def execute(self, context):
                return {"status": "success", "issues": []}
        
        @ReviewStepRegistry.register("tag2_step")
        class Tag2Step(ReviewStep):
            category = ReviewStepCategory.SECURITY
            severity = ReviewStepSeverity.HIGH
            tags = {"tag2", "common"}
            enabled = True
            
            def __init__(self, **kwargs):
                super().__init__(
                    id="tag2_step",
                    name="Tag2 Step",
                    description="A step with tag2",
                    category=ReviewStepCategory.SECURITY,
                    severity=ReviewStepSeverity.HIGH,
                    tags={"tag2", "common"},
                    **kwargs
                )
            
            def execute(self, context):
                return {"status": "success", "issues": []}
        
        # Filter by tag1
        tag1_steps = ReviewStepRegistry.filter_steps(tags="tag1")
        self.assertEqual(len(tag1_steps), 1)
        self.assertIn("tag1_step", tag1_steps)
        
        # Filter by tag2
        tag2_steps = ReviewStepRegistry.filter_steps(tags="tag2")
        self.assertEqual(len(tag2_steps), 1)
        self.assertIn("tag2_step", tag2_steps)
        
        # Filter by common tag
        common_steps = ReviewStepRegistry.filter_steps(tags="common")
        self.assertEqual(len(common_steps), 2)
        self.assertIn("tag1_step", common_steps)
        self.assertIn("tag2_step", common_steps)
    
    def test_filter_steps_by_enabled(self):
        """Test filtering review steps by enabled status."""
        
        @ReviewStepRegistry.register("enabled_step")
        class EnabledStep(ReviewStep):
            category = ReviewStepCategory.GENERAL
            severity = ReviewStepSeverity.MEDIUM
            enabled = True
            
            def __init__(self, **kwargs):
                super().__init__(
                    id="enabled_step",
                    name="Enabled Step",
                    description="An enabled step",
                    category=ReviewStepCategory.GENERAL,
                    severity=ReviewStepSeverity.MEDIUM,
                    enabled=True,
                    **kwargs
                )
            
            def execute(self, context):
                return {"status": "success", "issues": []}
        
        @ReviewStepRegistry.register("disabled_step")
        class DisabledStep(ReviewStep):
            category = ReviewStepCategory.SECURITY
            severity = ReviewStepSeverity.HIGH
            enabled = False
            
            def __init__(self, **kwargs):
                super().__init__(
                    id="disabled_step",
                    name="Disabled Step",
                    description="A disabled step",
                    category=ReviewStepCategory.SECURITY,
                    severity=ReviewStepSeverity.HIGH,
                    enabled=False,
                    **kwargs
                )
            
            def execute(self, context):
                return {"status": "success", "issues": []}
        
        # Filter enabled steps only (default)
        enabled_steps = ReviewStepRegistry.filter_steps()
        self.assertEqual(len(enabled_steps), 1)
        self.assertIn("enabled_step", enabled_steps)
        
        # Include disabled steps
        all_steps = ReviewStepRegistry.filter_steps(enabled_only=False)
        self.assertEqual(len(all_steps), 2)
        self.assertIn("enabled_step", all_steps)
        self.assertIn("disabled_step", all_steps)
    
    def test_create_step_instance(self):
        """Test creating a review step instance."""
        
        @ReviewStepRegistry.register("instance_step")
        class InstanceStep(ReviewStep):
            def __init__(
                self,
                id="instance_step",
                name="Instance Step",
                description="A step for testing instance creation",
                category=ReviewStepCategory.GENERAL,
                severity=ReviewStepSeverity.MEDIUM,
                custom_param=None,
                **kwargs
            ):
                super().__init__(
                    id=id,
                    name=name,
                    description=description,
                    category=category,
                    severity=severity,
                    **kwargs
                )
                self.custom_param = custom_param
            
            def execute(self, context):
                return {"status": "success", "custom_param": self.custom_param, "issues": []}
        
        # Create an instance with default parameters
        instance1 = ReviewStepRegistry.create_step_instance("instance_step")
        self.assertIsInstance(instance1, InstanceStep)
        self.assertIsNone(instance1.custom_param)
        
        # Create an instance with custom parameters
        instance2 = ReviewStepRegistry.create_step_instance(
            "instance_step", custom_param="test_value"
        )
        self.assertIsInstance(instance2, InstanceStep)
        self.assertEqual(instance2.custom_param, "test_value")
        
        # Try to create an instance of a non-existent step
        instance3 = ReviewStepRegistry.create_step_instance("non_existent_step")
        self.assertIsNone(instance3)


if __name__ == "__main__":
    unittest.main()
