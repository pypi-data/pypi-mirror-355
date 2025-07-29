"""
Tool base class for VaahAI.

This module provides the base class for all tools in the VaahAI system.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class ToolBase(ABC):
    """
    Abstract base class for all tools in VaahAI.
    
    This class defines the interface that all tools must implement.
    Tools are utilities that can be used by agents to perform specific tasks,
    such as code analysis, linting, or other operations on code.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the tool with the given configuration.
        
        Args:
            config: Configuration dictionary for the tool.
        """
        self.config = config or {}
        self._validate_config()
    
    @abstractmethod
    def _validate_config(self) -> None:
        """
        Validate the tool configuration.
        
        This method should be implemented by subclasses to validate their specific
        configuration requirements.
        
        Raises:
            ValueError: If the configuration is invalid.
        """
        pass
    
    @abstractmethod
    def execute(self, input_data: Any) -> Any:
        """
        Execute the tool on the given input data.
        
        Args:
            input_data: The input data for the tool to process.
            
        Returns:
            Any: The result of the tool execution.
            
        Raises:
            ValueError: If the input data is invalid.
            RuntimeError: If the tool execution fails.
        """
        pass
    
    @classmethod
    def get_tool_metadata(cls) -> Dict[str, Any]:
        """
        Get metadata about the tool.
        
        Returns:
            Dict[str, Any]: A dictionary containing tool metadata.
        """
        return {
            "name": cls.__name__,
            "description": cls.__doc__ or "No description available",
            "input_type": getattr(cls, "input_type", "Any"),
            "output_type": getattr(cls, "output_type", "Any"),
            "version": getattr(cls, "version", "0.1.0"),
            "author": getattr(cls, "author", "VaahAI"),
            "dependencies": getattr(cls, "dependencies", []),
            "tags": getattr(cls, "tags", []),
        }
    
    def get_requirements(self) -> List[str]:
        """
        Get the Python package requirements for this tool.
        
        Returns:
            List[str]: A list of package requirements in pip format.
        """
        return getattr(self, "requirements", [])
    
    def get_dependencies(self) -> List[str]:
        """
        Get the tool dependencies for this tool.
        
        Returns:
            List[str]: A list of tool type identifiers that this tool depends on.
        """
        return getattr(self, "dependencies", [])
