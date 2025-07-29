"""
Unit tests for the VaahAI Tool Registry.

This module contains tests for the tool registry, factory, and base classes.
"""

import os
import unittest
from unittest.mock import MagicMock, patch

from vaahai.tools.base import ToolBase, ToolRegistry, ToolFactory
from vaahai.tools.config_loader import ToolConfigLoader


class TestToolBase(unittest.TestCase):
    """Test cases for the ToolBase class."""

    def test_abstract_base_class(self):
        """Test that ToolBase is an abstract base class that cannot be instantiated directly."""
        with self.assertRaises(TypeError):
            ToolBase({})
    
    def test_concrete_subclass(self):
        """Test that a concrete subclass of ToolBase can be instantiated."""
        class ConcreteTool(ToolBase):
            def _validate_config(self):
                pass
            
            def execute(self, input_data):
                return {"result": "success"}
        
        tool = ConcreteTool({})
        self.assertIsInstance(tool, ToolBase)
        self.assertEqual(tool.execute("test"), {"result": "success"})


class TestToolRegistry(unittest.TestCase):
    """Test cases for the ToolRegistry class."""

    def setUp(self):
        """Set up the test environment."""
        # Clear the registry before each test
        ToolRegistry._registry = {}
        ToolRegistry._metadata_cache = {}
    
    def test_register_decorator(self):
        """Test the register decorator."""
        @ToolRegistry.register("test_tool")
        class TestTool(ToolBase):
            def _validate_config(self):
                pass
            
            def execute(self, input_data):
                return {"result": "success"}
        
        self.assertIn("test_tool", ToolRegistry._registry)
        self.assertEqual(ToolRegistry._registry["test_tool"], TestTool)
    
    def test_get_tool_class(self):
        """Test getting a tool class from the registry."""
        @ToolRegistry.register("test_tool")
        class TestTool(ToolBase):
            def _validate_config(self):
                pass
            
            def execute(self, input_data):
                return {"result": "success"}
        
        tool_class = ToolRegistry.get_tool_class("test_tool")
        self.assertEqual(tool_class, TestTool)
        
        # Test getting a non-existent tool class
        self.assertIsNone(ToolRegistry.get_tool_class("non_existent"))
    
    def test_is_registered(self):
        """Test checking if a tool is registered."""
        @ToolRegistry.register("test_tool")
        class TestTool(ToolBase):
            def _validate_config(self):
                pass
            
            def execute(self, input_data):
                return {"result": "success"}
        
        self.assertTrue(ToolRegistry.is_registered("test_tool"))
        self.assertFalse(ToolRegistry.is_registered("non_existent"))
    
    def test_list_registered_tools(self):
        """Test listing registered tools."""
        @ToolRegistry.register("test_tool1")
        class TestTool1(ToolBase):
            def _validate_config(self):
                pass
            
            def execute(self, input_data):
                return {"result": "success"}
        
        @ToolRegistry.register("test_tool2")
        class TestTool2(ToolBase):
            def _validate_config(self):
                pass
            
            def execute(self, input_data):
                return {"result": "success"}
        
        tools = ToolRegistry.list_registered_tools()
        self.assertEqual(set(tools), {"test_tool1", "test_tool2"})
    
    def test_get_tool_metadata(self):
        """Test getting tool metadata."""
        @ToolRegistry.register("test_tool")
        class TestTool(ToolBase):
            input_type = "test_input"
            output_type = "test_output"
            version = "1.0.0"
            author = "Test Author"
            tags = ["test", "example"]
            requirements = ["test-package>=1.0.0"]
            
            def _validate_config(self):
                pass
            
            def execute(self, input_data):
                return {"result": "success"}
        
        metadata = ToolRegistry.get_tool_metadata("test_tool")
        self.assertEqual(metadata["input_type"], "test_input")
        self.assertEqual(metadata["output_type"], "test_output")
        self.assertEqual(metadata["version"], "1.0.0")
        self.assertEqual(metadata["author"], "Test Author")
        self.assertEqual(metadata["tags"], ["test", "example"])
        self.assertEqual(metadata["requirements"], ["test-package>=1.0.0"])
        
        # Test getting metadata for a non-existent tool
        self.assertIsNone(ToolRegistry.get_tool_metadata("non_existent"))
    
    def test_get_tools_by_tag(self):
        """Test filtering tools by tag."""
        @ToolRegistry.register("test_tool1")
        class TestTool1(ToolBase):
            tags = ["test", "example"]
            
            def _validate_config(self):
                pass
            
            def execute(self, input_data):
                return {"result": "success"}
        
        @ToolRegistry.register("test_tool2")
        class TestTool2(ToolBase):
            tags = ["test", "other"]
            
            def _validate_config(self):
                pass
            
            def execute(self, input_data):
                return {"result": "success"}
        
        @ToolRegistry.register("test_tool3")
        class TestTool3(ToolBase):
            tags = ["example"]
            
            def _validate_config(self):
                pass
            
            def execute(self, input_data):
                return {"result": "success"}
        
        tools = ToolRegistry.get_tools_by_tag("test")
        self.assertEqual(set(tools), {"test_tool1", "test_tool2"})
        
        tools = ToolRegistry.get_tools_by_tag("example")
        self.assertEqual(set(tools), {"test_tool1", "test_tool3"})
        
        tools = ToolRegistry.get_tools_by_tag("other")
        self.assertEqual(set(tools), {"test_tool2"})
        
        tools = ToolRegistry.get_tools_by_tag("non_existent")
        self.assertEqual(tools, [])
    
    def test_get_tools_by_input_type(self):
        """Test filtering tools by input type."""
        @ToolRegistry.register("test_tool1")
        class TestTool1(ToolBase):
            input_type = "text"
            
            def _validate_config(self):
                pass
            
            def execute(self, input_data):
                return {"result": "success"}
        
        @ToolRegistry.register("test_tool2")
        class TestTool2(ToolBase):
            input_type = "code"
            
            def _validate_config(self):
                pass
            
            def execute(self, input_data):
                return {"result": "success"}
        
        tools = ToolRegistry.get_tools_by_input_type("text")
        self.assertEqual(set(tools), {"test_tool1"})
        
        tools = ToolRegistry.get_tools_by_input_type("code")
        self.assertEqual(set(tools), {"test_tool2"})
        
        tools = ToolRegistry.get_tools_by_input_type("non_existent")
        self.assertEqual(tools, [])
    
    def test_get_tools_by_output_type(self):
        """Test filtering tools by output type."""
        @ToolRegistry.register("test_tool1")
        class TestTool1(ToolBase):
            output_type = "text"
            
            def _validate_config(self):
                pass
            
            def execute(self, input_data):
                return {"result": "success"}
        
        @ToolRegistry.register("test_tool2")
        class TestTool2(ToolBase):
            output_type = "analysis"
            
            def _validate_config(self):
                pass
            
            def execute(self, input_data):
                return {"result": "success"}
        
        tools = ToolRegistry.get_tools_by_output_type("text")
        self.assertEqual(set(tools), {"test_tool1"})
        
        tools = ToolRegistry.get_tools_by_output_type("analysis")
        self.assertEqual(set(tools), {"test_tool2"})
        
        tools = ToolRegistry.get_tools_by_output_type("non_existent")
        self.assertEqual(tools, [])


class TestToolFactory(unittest.TestCase):
    """Test cases for the ToolFactory class."""

    def setUp(self):
        """Set up the test environment."""
        # Clear the registry before each test
        ToolRegistry._registry = {}
        ToolRegistry._metadata_cache = {}
        
        # Register a test tool
        @ToolRegistry.register("test_tool")
        class TestTool(ToolBase):
            def _validate_config(self):
                pass
            
            def execute(self, input_data):
                return {"result": "success"}
    
    @patch("vaahai.tools.config_loader.ToolConfigLoader.validate_and_prepare_config")
    def test_create_tool(self, mock_validate):
        """Test creating a tool."""
        mock_validate.return_value = {"type": "test_tool"}
        
        tool = ToolFactory.create_tool("test_tool")
        self.assertIsInstance(tool, ToolBase)
        
        # Test creating a tool with a config
        config = {"type": "test_tool", "option": "value"}
        mock_validate.return_value = config
        
        tool = ToolFactory.create_tool("test_tool", config)
        self.assertIsInstance(tool, ToolBase)
        
        # Test creating a non-existent tool
        with self.assertRaises(ValueError):
            ToolFactory.create_tool("non_existent")
    
    @patch("vaahai.tools.config_loader.ToolConfigLoader.load_config_from_file")
    def test_create_tool_from_file(self, mock_load):
        """Test creating a tool from a configuration file."""
        mock_load.return_value = {"type": "test_tool"}
        
        tool = ToolFactory.create_tool_from_file("test_file.yaml")
        self.assertIsInstance(tool, ToolBase)
        
        # Test with a non-existent tool type
        mock_load.return_value = {"type": "non_existent"}
        
        with self.assertRaises(ValueError):
            ToolFactory.create_tool_from_file("test_file.yaml")
    
    def test_list_available_tools(self):
        """Test listing available tools."""
        tools = ToolFactory.list_available_tools()
        self.assertEqual(set(tools), {"test_tool"})
    
    def test_is_tool_available(self):
        """Test checking if a tool is available."""
        self.assertTrue(ToolFactory.is_tool_available("test_tool"))
        self.assertFalse(ToolFactory.is_tool_available("non_existent"))
    
    def test_get_tool_metadata(self):
        """Test getting tool metadata."""
        metadata = ToolFactory.get_tool_metadata("test_tool")
        self.assertIsNotNone(metadata)
        
        # Test getting metadata for a non-existent tool
        with self.assertRaises(ValueError):
            ToolFactory.get_tool_metadata("non_existent")
    
    @patch("vaahai.tools.config_loader.ToolConfigLoader.validate_and_prepare_config")
    def test_create_tool_pipeline(self, mock_validate):
        """Test creating a tool pipeline."""
        # Register another test tool
        @ToolRegistry.register("test_tool2")
        class TestTool2(ToolBase):
            def _validate_config(self):
                pass
            
            def execute(self, input_data):
                return {"result2": "success"}
        
        # Mock the validate function to return the input config
        mock_validate.side_effect = lambda tool_type, config: {"type": tool_type, **(config or {})}
        
        # Test creating a pipeline with multiple tools
        pipeline_config = [
            {"type": "test_tool"},
            {"type": "test_tool2"}
        ]
        
        tools = ToolFactory.create_tool_pipeline(pipeline_config)
        self.assertEqual(len(tools), 2)
        self.assertEqual(tools[0].__class__.__name__, "TestTool")
        self.assertEqual(tools[1].__class__.__name__, "TestTool2")
        
        # Test with an invalid tool type
        pipeline_config = [
            {"type": "test_tool"},
            {"type": "non_existent"}
        ]
        
        with self.assertRaises(ValueError):
            ToolFactory.create_tool_pipeline(pipeline_config)


class TestToolConfigLoader(unittest.TestCase):
    """Test cases for the ToolConfigLoader class."""

    @patch("os.path.exists")
    @patch("builtins.open")
    def test_load_config_from_file(self, mock_open, mock_exists):
        """Test loading a configuration from a file."""
        # Mock file existence
        mock_exists.return_value = True
        
        # Mock file content for YAML
        mock_file = MagicMock()
        mock_file.__enter__.return_value.read.return_value = "type: test_tool\noption: value"
        mock_open.return_value = mock_file
        
        config = ToolConfigLoader.load_config_from_file("test_file.yaml")
        self.assertEqual(config, {"type": "test_tool", "option": "value"})
        
        # Mock file content for JSON
        mock_file.__enter__.return_value.read.return_value = '{"type": "test_tool", "option": "value"}'
        config = ToolConfigLoader.load_config_from_file("test_file.json")
        self.assertEqual(config, {"type": "test_tool", "option": "value"})
        
        # Test with a non-existent file
        mock_exists.return_value = False
        with self.assertRaises(FileNotFoundError):
            ToolConfigLoader.load_config_from_file("non_existent.yaml")
        
        # Test with an unsupported file extension
        mock_exists.return_value = True
        with self.assertRaises(ValueError):
            ToolConfigLoader.load_config_from_file("test_file.txt")
    
    @patch("vaahai.tools.schemas.get_default_config")
    @patch("vaahai.tools.schemas.validate_tool_config")
    def test_validate_and_prepare_config(self, mock_validate, mock_default):
        """Test validating and preparing a configuration."""
        # Mock default config
        mock_default.return_value = {"type": "test_tool", "default_option": "default_value"}
        
        # Mock validation (no errors)
        mock_validate.return_value = []
        
        # Test with a minimal config
        config = {"type": "test_tool"}
        prepared_config = ToolConfigLoader.validate_and_prepare_config("test_tool", config)
        self.assertEqual(prepared_config["type"], "test_tool")
        self.assertEqual(prepared_config["default_option"], "default_value")
        
        # Test with a config that overrides defaults
        config = {"type": "test_tool", "default_option": "custom_value"}
        prepared_config = ToolConfigLoader.validate_and_prepare_config("test_tool", config)
        self.assertEqual(prepared_config["default_option"], "custom_value")
        
        # Test with validation errors
        mock_validate.return_value = ["Error 1", "Error 2"]
        with self.assertRaises(ValueError):
            ToolConfigLoader.validate_and_prepare_config("test_tool", config)
    
    def test_process_env_vars(self):
        """Test processing environment variables in a configuration."""
        # Set up environment variables for testing
        os.environ["TEST_VAR"] = "test_value"
        os.environ["TEST_NUM"] = "42"
        
        # Test with string values
        config = {
            "string_var": "${TEST_VAR}",
            "nested": {
                "string_var": "prefix_${TEST_VAR}_suffix"
            }
        }
        processed_config = ToolConfigLoader.process_env_vars(config)
        self.assertEqual(processed_config["string_var"], "test_value")
        self.assertEqual(processed_config["nested"]["string_var"], "prefix_test_value_suffix")
        
        # Test with numeric values
        config = {
            "num_var": "${TEST_NUM}",
            "nested": {
                "num_var": "${TEST_NUM}"
            }
        }
        processed_config = ToolConfigLoader.process_env_vars(config)
        self.assertEqual(processed_config["num_var"], "42")
        self.assertEqual(processed_config["nested"]["num_var"], "42")
        
        # Test with missing environment variables
        config = {"missing_var": "${MISSING_VAR}"}
        with self.assertRaises(ValueError):
            ToolConfigLoader.process_env_vars(config)
        
        # Test with default values for missing variables
        config = {"missing_var": "${MISSING_VAR:-default_value}"}
        processed_config = ToolConfigLoader.process_env_vars(config)
        self.assertEqual(processed_config["missing_var"], "default_value")
        
        # Clean up environment variables
        del os.environ["TEST_VAR"]
        del os.environ["TEST_NUM"]


if __name__ == "__main__":
    unittest.main()
