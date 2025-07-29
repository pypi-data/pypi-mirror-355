"""
Tool registry for VaahAI.

This module provides a registry for tool types, allowing dynamic registration
and lookup of tool classes.
"""

from typing import Dict, Type, Optional, List, Any
from vaahai.tools.base.tool_base import ToolBase


class ToolRegistry:
    """
    Registry for tool types.
    
    This class provides a central registry for all tool types in the VaahAI system,
    allowing dynamic registration and lookup of tool classes.
    """
    
    _registry: Dict[str, Type[ToolBase]] = {}
    _metadata_cache: Dict[str, Dict[str, Any]] = {}
    
    @classmethod
    def register(cls, tool_type: str) -> callable:
        """
        Register a tool class with the registry.
        
        This method can be used as a decorator to register tool classes.
        
        Args:
            tool_type: The type identifier for the tool.
            
        Returns:
            callable: A decorator function that registers the tool class.
        
        Example:
            @ToolRegistry.register("code_linter")
            class CodeLinterTool(ToolBase):
                pass
        """
        def decorator(tool_class: Type[ToolBase]) -> Type[ToolBase]:
            cls._registry[tool_type] = tool_class
            # Cache the tool metadata
            cls._metadata_cache[tool_type] = tool_class.get_tool_metadata()
            return tool_class
        return decorator
    
    @classmethod
    def get_tool_class(cls, tool_type: str) -> Optional[Type[ToolBase]]:
        """
        Get a tool class by type.
        
        Args:
            tool_type: The type identifier for the tool.
            
        Returns:
            Optional[Type[ToolBase]]: The tool class, or None if not found.
        """
        return cls._registry.get(tool_type)
    
    @classmethod
    def list_tool_types(cls) -> List[str]:
        """
        List all registered tool types.
        
        Returns:
            List[str]: A list of all registered tool type identifiers.
        """
        return list(cls._registry.keys())
    
    @classmethod
    def is_registered(cls, tool_type: str) -> bool:
        """
        Check if a tool type is registered.
        
        Args:
            tool_type: The type identifier for the tool.
            
        Returns:
            bool: True if the tool type is registered, False otherwise.
        """
        return tool_type in cls._registry
    
    @classmethod
    def get_tool_metadata(cls, tool_type: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a tool type.
        
        Args:
            tool_type: The type identifier for the tool.
            
        Returns:
            Optional[Dict[str, Any]]: The tool metadata, or None if not found.
        """
        if tool_type in cls._metadata_cache:
            return cls._metadata_cache[tool_type]
        
        tool_class = cls.get_tool_class(tool_type)
        if not tool_class:
            return None
        
        metadata = tool_class.get_tool_metadata()
        cls._metadata_cache[tool_type] = metadata
        return metadata
    
    @classmethod
    def get_tools_by_tag(cls, tag: str) -> List[str]:
        """
        Get all registered tool types that have the specified tag.
        
        Args:
            tag: The tag to filter by.
            
        Returns:
            List[str]: A list of tool types that have the specified tag.
        """
        result = []
        for tool_type in cls._registry:
            metadata = cls.get_tool_metadata(tool_type)
            if metadata and tag in metadata.get("tags", []):
                result.append(tool_type)
        return result
    
    @classmethod
    def get_tools_by_input_type(cls, input_type: str) -> List[str]:
        """
        Get all registered tool types that accept the specified input type.
        
        Args:
            input_type: The input type to filter by.
            
        Returns:
            List[str]: A list of tool types that accept the specified input type.
        """
        result = []
        for tool_type in cls._registry:
            metadata = cls.get_tool_metadata(tool_type)
            if metadata and metadata.get("input_type") == input_type:
                result.append(tool_type)
        return result
    
    @classmethod
    def get_tools_by_output_type(cls, output_type: str) -> List[str]:
        """
        Get all registered tool types that produce the specified output type.
        
        Args:
            output_type: The output type to filter by.
            
        Returns:
            List[str]: A list of tool types that produce the specified output type.
        """
        result = []
        for tool_type in cls._registry:
            metadata = cls.get_tool_metadata(tool_type)
            if metadata and metadata.get("output_type") == output_type:
                result.append(tool_type)
        return result
