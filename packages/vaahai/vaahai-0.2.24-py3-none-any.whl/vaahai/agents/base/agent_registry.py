"""
Agent registry for VaahAI.

This module provides a registry for agent types, allowing dynamic registration
and lookup of agent classes.
"""

from typing import Dict, Type, Optional, List
from vaahai.agents.base.agent_base import AgentBase


class AgentRegistry:
    """
    Registry for agent types.
    
    This class provides a central registry for all agent types in the VaahAI system,
    allowing dynamic registration and lookup of agent classes.
    """
    
    _registry: Dict[str, Type[AgentBase]] = {}
    
    @classmethod
    def register(cls, agent_type: str) -> callable:
        """
        Register an agent class with the registry.
        
        This method can be used as a decorator to register agent classes.
        
        Args:
            agent_type: The type identifier for the agent.
            
        Returns:
            callable: A decorator function that registers the agent class.
        
        Example:
            @AgentRegistry.register("hello_world")
            class HelloWorldAgent(AutoGenAgentBase):
                pass
        """
        def decorator(agent_class: Type[AgentBase]) -> Type[AgentBase]:
            cls._registry[agent_type] = agent_class
            return agent_class
        return decorator
    
    @classmethod
    def get_agent_class(cls, agent_type: str) -> Optional[Type[AgentBase]]:
        """
        Get an agent class by type.
        
        Args:
            agent_type: The type identifier for the agent.
            
        Returns:
            Optional[Type[AgentBase]]: The agent class, or None if not found.
        """
        return cls._registry.get(agent_type)
    
    @classmethod
    def list_agent_types(cls) -> List[str]:
        """
        List all registered agent types.
        
        Returns:
            List[str]: A list of all registered agent type identifiers.
        """
        return list(cls._registry.keys())
    
    @classmethod
    def is_registered(cls, agent_type: str) -> bool:
        """
        Check if an agent type is registered.
        
        Args:
            agent_type: The type identifier for the agent.
            
        Returns:
            bool: True if the agent type is registered, False otherwise.
        """
        return agent_type in cls._registry
