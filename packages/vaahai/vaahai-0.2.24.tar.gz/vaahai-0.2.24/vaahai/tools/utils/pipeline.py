"""
Tool pipeline utilities for VaahAI.

This module provides utilities for creating and executing tool pipelines.
"""

import logging
from typing import Any, Dict, List, Optional, Union

from vaahai.tools.base import ToolBase, ToolFactory

# Set up logging
logger = logging.getLogger(__name__)


class ToolPipeline:
    """
    A pipeline of tools that can be executed in sequence.
    
    This class allows multiple tools to be chained together, with the output of
    one tool being passed as input to the next tool in the pipeline.
    """
    
    def __init__(self, tools: List[ToolBase]):
        """
        Initialize the tool pipeline.
        
        Args:
            tools: A list of tool instances to include in the pipeline.
        """
        self.tools = tools
        self._validate_pipeline()
    
    @classmethod
    def from_config(cls, config: List[Dict[str, Any]]) -> "ToolPipeline":
        """
        Create a tool pipeline from a configuration list.
        
        Args:
            config: A list of tool configurations in pipeline order.
            
        Returns:
            ToolPipeline: A configured tool pipeline.
            
        Raises:
            ValueError: If a tool type is missing or not registered.
        """
        tools = ToolFactory.create_tool_pipeline(config)
        return cls(tools)
    
    def _validate_pipeline(self) -> None:
        """
        Validate the tool pipeline.
        
        Raises:
            ValueError: If the pipeline is invalid.
        """
        if not self.tools:
            raise ValueError("Pipeline must contain at least one tool")
    
    def execute(self, input_data: Any) -> Any:
        """
        Execute the pipeline on the given input data.
        
        Args:
            input_data: The input data for the first tool in the pipeline.
            
        Returns:
            Any: The output of the last tool in the pipeline.
            
        Raises:
            ValueError: If the input data is invalid.
            RuntimeError: If a tool execution fails.
        """
        current_data = input_data
        results = []
        
        for i, tool in enumerate(self.tools):
            try:
                logger.debug(f"Executing tool {i+1}/{len(self.tools)}: {tool.__class__.__name__}")
                current_data = tool.execute(current_data)
                results.append({
                    "tool": tool.__class__.__name__,
                    "output": current_data
                })
            except Exception as e:
                logger.error(f"Error executing tool {tool.__class__.__name__}: {str(e)}")
                raise RuntimeError(f"Pipeline execution failed at step {i+1} ({tool.__class__.__name__}): {str(e)}")
        
        return {
            "final_output": current_data,
            "pipeline_results": results
        }
    
    def add_tool(self, tool: ToolBase) -> None:
        """
        Add a tool to the end of the pipeline.
        
        Args:
            tool: The tool to add.
        """
        self.tools.append(tool)
    
    def insert_tool(self, index: int, tool: ToolBase) -> None:
        """
        Insert a tool at the specified position in the pipeline.
        
        Args:
            index: The position to insert the tool.
            tool: The tool to insert.
            
        Raises:
            IndexError: If the index is out of range.
        """
        self.tools.insert(index, tool)
    
    def remove_tool(self, index: int) -> ToolBase:
        """
        Remove a tool from the pipeline.
        
        Args:
            index: The index of the tool to remove.
            
        Returns:
            ToolBase: The removed tool.
            
        Raises:
            IndexError: If the index is out of range.
        """
        return self.tools.pop(index)
    
    def get_tool(self, index: int) -> ToolBase:
        """
        Get a tool from the pipeline.
        
        Args:
            index: The index of the tool to get.
            
        Returns:
            ToolBase: The tool at the specified index.
            
        Raises:
            IndexError: If the index is out of range.
        """
        return self.tools[index]
    
    def __len__(self) -> int:
        """
        Get the number of tools in the pipeline.
        
        Returns:
            int: The number of tools.
        """
        return len(self.tools)
