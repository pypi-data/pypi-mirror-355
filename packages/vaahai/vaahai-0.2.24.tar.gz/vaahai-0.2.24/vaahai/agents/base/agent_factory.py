"""
Agent factory for VaahAI.

This module provides a factory for creating and configuring agents.
"""

import logging
from typing import Any, Dict, List, Optional, Type, Union

from vaahai.agents.base.agent_base import AgentBase
from vaahai.agents.base.agent_registry import AgentRegistry
from vaahai.agents.config_loader import AgentConfigLoader

# Set up logging
logger = logging.getLogger(__name__)


class AgentFactory:
    """
    Factory for creating and configuring agents.
    
    This class provides methods for creating agents based on their type and
    configuration.
    """
    
    @staticmethod
    def create_agent(agent_type: str, config: Optional[Dict[str, Any]] = None) -> AgentBase:
        """
        Create an agent of the specified type.
        
        Args:
            agent_type: The type identifier for the agent.
            config: Configuration dictionary for the agent.
            
        Returns:
            AgentBase: An instance of the specified agent type.
            
        Raises:
            ValueError: If the agent type is not registered or the configuration is invalid.
        """
        agent_class = AgentRegistry.get_agent_class(agent_type)
        if not agent_class:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        try:
            # Validate and prepare the configuration
            validated_config = AgentConfigLoader.validate_and_prepare_config(agent_type, config)
            
            # Create the agent instance
            agent = agent_class(validated_config)
            logger.debug(f"Created agent of type {agent_type}")
            return agent
            
        except ValueError as e:
            # Re-raise with more context
            raise ValueError(f"Failed to create agent of type {agent_type}: {str(e)}")
        except Exception as e:
            # Log unexpected errors and re-raise
            logger.error(f"Unexpected error creating agent of type {agent_type}: {str(e)}")
            raise
    
    @staticmethod
    def create_agents(agent_configs: Dict[str, Dict[str, Any]]) -> Dict[str, AgentBase]:
        """
        Create multiple agents from a configuration dictionary.
        
        Args:
            agent_configs: A dictionary mapping agent names to their configurations.
            
        Returns:
            Dict[str, AgentBase]: A dictionary mapping agent names to agent instances.
            
        Raises:
            ValueError: If an agent type is missing or not registered.
        """
        agents = {}
        errors = []
        
        for agent_name, agent_config in agent_configs.items():
            agent_type = agent_config.get("type")
            if not agent_type:
                errors.append(f"Missing agent type for {agent_name}")
                continue
            
            try:
                agents[agent_name] = AgentFactory.create_agent(agent_type, agent_config)
            except ValueError as e:
                errors.append(f"Error creating agent {agent_name}: {str(e)}")
            except Exception as e:
                errors.append(f"Unexpected error creating agent {agent_name}: {str(e)}")
        
        if errors:
            error_msg = "\n".join(errors)
            raise ValueError(f"Failed to create one or more agents:\n{error_msg}")
        
        return agents
    
    @staticmethod
    def create_agents_from_file(file_path: str) -> Dict[str, AgentBase]:
        """
        Create multiple agents from a configuration file.
        
        Args:
            file_path: Path to the configuration file (YAML or JSON).
            
        Returns:
            Dict[str, AgentBase]: A dictionary mapping agent names to agent instances.
            
        Raises:
            FileNotFoundError: If the file doesn't exist.
            ValueError: If the file format is not supported or the configuration is invalid.
        """
        try:
            config = AgentConfigLoader.load_from_file(file_path)
            return AgentFactory.create_agents(config)
        except Exception as e:
            raise ValueError(f"Failed to create agents from file {file_path}: {str(e)}")
    
    @staticmethod
    def list_available_agents() -> List[str]:
        """
        List all available agent types.
        
        Returns:
            List[str]: A list of all registered agent type identifiers.
        """
        return AgentRegistry.list_agent_types()
    
    @staticmethod
    def is_agent_available(agent_type: str) -> bool:
        """
        Check if an agent type is available.
        
        Args:
            agent_type: The type identifier for the agent.
            
        Returns:
            bool: True if the agent type is registered, False otherwise.
        """
        return AgentRegistry.is_registered(agent_type)
    
    @staticmethod
    def get_agent_metadata(agent_type: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for an agent type.
        
        Args:
            agent_type: The type identifier for the agent.
            
        Returns:
            Optional[Dict[str, Any]]: The agent metadata, or None if not found.
        """
        agent_class = AgentRegistry.get_agent_class(agent_type)
        if not agent_class:
            return None
        
        # Get metadata from class attributes if available
        metadata = getattr(agent_class, "metadata", {})
        if not metadata:
            # Build basic metadata from class information
            metadata = {
                "name": agent_class.__name__,
                "description": agent_class.__doc__ or "No description available",
                "type": agent_type
            }
        
        return metadata
