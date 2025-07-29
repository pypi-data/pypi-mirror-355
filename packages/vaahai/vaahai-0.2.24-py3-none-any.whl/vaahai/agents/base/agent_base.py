"""
Base agent classes for VaahAI.

This module defines the abstract base classes that all VaahAI agents must implement.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class AgentBase(ABC):
    """
    Abstract base class for all VaahAI agents.
    
    All agents in the VaahAI system must inherit from this class and implement
    its abstract methods.
    
    Attributes:
        config (Dict[str, Any]): Configuration dictionary for the agent.
        name (str): Name of the agent, defaults to class name if not specified.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the agent with the given configuration.
        
        Args:
            config: Configuration dictionary for the agent.
        """
        self.config = config
        self.name = self.config.get("name", self.__class__.__name__)
        self.initialize()
    
    def initialize(self) -> None:
        """
        Initialize agent resources.
        
        This method is called during initialization and can be overridden by
        subclasses to perform any necessary setup.
        """
        pass
    
    @abstractmethod
    def run(self, *args, **kwargs) -> Any:
        """
        Run the agent with the given inputs.
        
        This is the main entry point for agent execution and must be implemented
        by all subclasses.
        
        Args:
            *args: Positional arguments for the agent.
            **kwargs: Keyword arguments for the agent.
            
        Returns:
            Any: The result of the agent execution.
        """
        pass
    
    def cleanup(self) -> None:
        """
        Clean up any resources used by the agent.
        
        This method is called when the agent is no longer needed and can be
        overridden by subclasses to perform any necessary cleanup.
        """
        pass
