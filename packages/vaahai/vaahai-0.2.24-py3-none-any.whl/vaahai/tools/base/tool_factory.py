"""
Tool factory for VaahAI.

This module provides a factory for creating and configuring tools.
"""

import logging
from typing import Any, Dict, List, Optional, Type, Union

from vaahai.tools.base.tool_base import ToolBase
from vaahai.tools.base.tool_registry import ToolRegistry
from vaahai.tools.config_loader import ToolConfigLoader

# Set up logging
logger = logging.getLogger(__name__)


class ToolFactory:
    """
    Factory for creating and configuring tools.
    
    This class provides methods for creating tools based on their type and
    configuration.
    """
    
    @staticmethod
    def create_tool(tool_type: str, config: Optional[Dict[str, Any]] = None) -> ToolBase:
        """
        Create a tool of the specified type.
        
        Args:
            tool_type: The type identifier for the tool.
            config: Configuration dictionary for the tool.
            
        Returns:
            ToolBase: An instance of the specified tool type.
            
        Raises:
            ValueError: If the tool type is not registered or the configuration is invalid.
        """
        tool_class = ToolRegistry.get_tool_class(tool_type)
        if not tool_class:
            raise ValueError(f"Unknown tool type: {tool_type}")
        
        try:
            # Validate and prepare the configuration
            validated_config = ToolConfigLoader.validate_and_prepare_config(tool_type, config)
            
            # Create the tool instance
            tool = tool_class(validated_config)
            logger.debug(f"Created tool of type {tool_type}")
            return tool
            
        except ValueError as e:
            # Re-raise with more context
            raise ValueError(f"Failed to create tool of type {tool_type}: {str(e)}")
        except Exception as e:
            # Log unexpected errors and re-raise
            logger.error(f"Unexpected error creating tool of type {tool_type}: {str(e)}")
            raise
    
    @staticmethod
    def create_tools(tool_configs: Dict[str, Dict[str, Any]]) -> Dict[str, ToolBase]:
        """
        Create multiple tools from a configuration dictionary.
        
        Args:
            tool_configs: A dictionary mapping tool names to their configurations.
            
        Returns:
            Dict[str, ToolBase]: A dictionary mapping tool names to tool instances.
            
        Raises:
            ValueError: If a tool type is missing or not registered.
        """
        tools = {}
        errors = []
        
        for tool_name, tool_config in tool_configs.items():
            tool_type = tool_config.get("type")
            if not tool_type:
                errors.append(f"Missing tool type for {tool_name}")
                continue
            
            try:
                tools[tool_name] = ToolFactory.create_tool(tool_type, tool_config)
            except ValueError as e:
                errors.append(f"Error creating tool {tool_name}: {str(e)}")
            except Exception as e:
                errors.append(f"Unexpected error creating tool {tool_name}: {str(e)}")
        
        if errors:
            error_msg = "\n".join(errors)
            raise ValueError(f"Failed to create one or more tools:\n{error_msg}")
        
        return tools
    
    @staticmethod
    def create_tools_from_file(file_path: str) -> Dict[str, ToolBase]:
        """
        Create multiple tools from a configuration file.
        
        Args:
            file_path: Path to the configuration file (YAML or JSON).
            
        Returns:
            Dict[str, ToolBase]: A dictionary mapping tool names to tool instances.
            
        Raises:
            FileNotFoundError: If the file doesn't exist.
            ValueError: If the file format is not supported or the configuration is invalid.
        """
        try:
            config = ToolConfigLoader.load_from_file(file_path)
            return ToolFactory.create_tools(config)
        except Exception as e:
            raise ValueError(f"Failed to create tools from file {file_path}: {str(e)}")
    
    @staticmethod
    def list_available_tools() -> List[str]:
        """
        List all available tool types.
        
        Returns:
            List[str]: A list of all registered tool type identifiers.
        """
        return ToolRegistry.list_tool_types()
    
    @staticmethod
    def is_tool_available(tool_type: str) -> bool:
        """
        Check if a tool type is available.
        
        Args:
            tool_type: The type identifier for the tool.
            
        Returns:
            bool: True if the tool type is registered, False otherwise.
        """
        return ToolRegistry.is_registered(tool_type)
    
    @staticmethod
    def get_tool_metadata(tool_type: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a tool type.
        
        Args:
            tool_type: The type identifier for the tool.
            
        Returns:
            Optional[Dict[str, Any]]: The tool metadata, or None if not found.
        """
        return ToolRegistry.get_tool_metadata(tool_type)
    
    @staticmethod
    def get_tools_by_tag(tag: str) -> List[str]:
        """
        Get all tool types with the specified tag.
        
        Args:
            tag: The tag to filter by.
            
        Returns:
            List[str]: A list of tool type identifiers with the specified tag.
        """
        return ToolRegistry.get_tools_by_tag(tag)
    
    @staticmethod
    def get_tools_by_input_type(input_type: str) -> List[str]:
        """
        Get all tool types that accept the specified input type.
        
        Args:
            input_type: The input type to filter by.
            
        Returns:
            List[str]: A list of tool type identifiers that accept the specified input type.
        """
        return ToolRegistry.get_tools_by_input_type(input_type)
    
    @staticmethod
    def get_tools_by_output_type(output_type: str) -> List[str]:
        """
        Get all tool types that produce the specified output type.
        
        Args:
            output_type: The output type to filter by.
            
        Returns:
            List[str]: A list of tool type identifiers that produce the specified output type.
        """
        return ToolRegistry.get_tools_by_output_type(output_type)
    
    @staticmethod
    def create_tool_pipeline(pipeline_config: List[Dict[str, Any]]) -> List[ToolBase]:
        """
        Create a pipeline of tools from a configuration list.
        
        Args:
            pipeline_config: A list of tool configurations in pipeline order.
            
        Returns:
            List[ToolBase]: A list of tool instances in pipeline order.
            
        Raises:
            ValueError: If a tool type is missing or not registered.
        """
        pipeline = []
        errors = []
        
        for idx, tool_config in enumerate(pipeline_config):
            tool_type = tool_config.get("type")
            if not tool_type:
                errors.append(f"Missing tool type for pipeline step {idx}")
                continue
            
            try:
                pipeline.append(ToolFactory.create_tool(tool_type, tool_config))
            except ValueError as e:
                errors.append(f"Error creating tool for pipeline step {idx}: {str(e)}")
            except Exception as e:
                errors.append(f"Unexpected error creating tool for pipeline step {idx}: {str(e)}")
        
        if errors:
            error_msg = "\n".join(errors)
            raise ValueError(f"Failed to create tool pipeline:\n{error_msg}")
        
        return pipeline
