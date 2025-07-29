"""
Group Chat Factory for VaahAI.

This module provides a factory for creating group chat managers with
different configurations and agent combinations.
"""

from typing import Dict, List, Any, Optional, Union

from vaahai.agents.base.agent_base import AgentBase
from vaahai.agents.base.agent_factory import AgentFactory
from vaahai.agents.utils.group_chat_manager import (
    VaahAIGroupChatManager,
    GroupChatType,
    HumanInputMode
)
from vaahai.config.schemas.group_chat import validate_group_chat_config


class GroupChatFactory:
    """
    Factory for creating group chat managers with different configurations.
    
    This class provides methods for creating group chat managers with
    different agent combinations and configurations, making it easier
    to set up multi-agent conversations.
    """
    
    @classmethod
    def create_group_chat(
        cls,
        agent_configs: List[Dict[str, Any]],
        chat_config: Optional[Dict[str, Any]] = None,
        chat_type: Optional[Union[GroupChatType, str]] = None,
        human_input_mode: Optional[Union[HumanInputMode, str]] = None
    ) -> VaahAIGroupChatManager:
        """
        Create a group chat manager with the specified agents and configuration.
        
        Args:
            agent_configs: List of agent configurations to create
            chat_config: Configuration for the group chat
            chat_type: Type of group chat to create (overrides chat_config)
            human_input_mode: Human input mode to use (overrides chat_config)
            
        Returns:
            A configured VaahAIGroupChatManager instance
            
        Raises:
            ValueError: If the configuration is invalid
        """
        # Create agents
        agents = []
        for config in agent_configs:
            agent_type = config.pop("type", None)
            if not agent_type:
                raise ValueError("Agent configuration must include a 'type' field")
            
            agent = AgentFactory.create_agent(agent_type, config)
            agents.append(agent)
        
        # Validate and process chat configuration
        if chat_config is None:
            chat_config = {}
        
        # Override chat type if specified
        if chat_type is not None:
            if isinstance(chat_type, str):
                chat_config["type"] = chat_type.lower()
            else:
                chat_config["type"] = chat_type.value.lower()
        
        # Override human input mode if specified
        if human_input_mode is not None:
            if isinstance(human_input_mode, str):
                chat_config["human_input_mode"] = human_input_mode.lower()
            else:
                chat_config["human_input_mode"] = human_input_mode.value.lower()
        
        # Validate the configuration
        validated_config = validate_group_chat_config(chat_config)
        
        # Create the group chat manager
        return VaahAIGroupChatManager(
            agents=agents,
            config=validated_config
        )
    
    @classmethod
    def create_round_robin_chat(
        cls,
        agent_configs: List[Dict[str, Any]],
        chat_config: Optional[Dict[str, Any]] = None,
        human_input_mode: Optional[Union[HumanInputMode, str]] = None
    ) -> VaahAIGroupChatManager:
        """
        Create a round-robin group chat manager.
        
        Args:
            agent_configs: List of agent configurations to create
            chat_config: Additional configuration for the group chat
            human_input_mode: Human input mode to use
            
        Returns:
            A configured VaahAIGroupChatManager instance with round-robin chat type
        """
        return cls.create_group_chat(
            agent_configs=agent_configs,
            chat_config=chat_config,
            chat_type=GroupChatType.ROUND_ROBIN,
            human_input_mode=human_input_mode
        )
    
    @classmethod
    def create_selector_chat(
        cls,
        agent_configs: List[Dict[str, Any]],
        selector_agent_name: str,
        chat_config: Optional[Dict[str, Any]] = None,
        human_input_mode: Optional[Union[HumanInputMode, str]] = None
    ) -> VaahAIGroupChatManager:
        """
        Create a selector group chat manager.
        
        Args:
            agent_configs: List of agent configurations to create
            selector_agent_name: Name of the agent that will select the next speaker
            chat_config: Additional configuration for the group chat
            human_input_mode: Human input mode to use
            
        Returns:
            A configured VaahAIGroupChatManager instance with selector chat type
        """
        if chat_config is None:
            chat_config = {}
        
        chat_config["selector_agent"] = selector_agent_name
        
        return cls.create_group_chat(
            agent_configs=agent_configs,
            chat_config=chat_config,
            chat_type=GroupChatType.SELECTOR,
            human_input_mode=human_input_mode
        )
    
    @classmethod
    def create_broadcast_chat(
        cls,
        agent_configs: List[Dict[str, Any]],
        chat_config: Optional[Dict[str, Any]] = None,
        human_input_mode: Optional[Union[HumanInputMode, str]] = None
    ) -> VaahAIGroupChatManager:
        """
        Create a broadcast group chat manager.
        
        Args:
            agent_configs: List of agent configurations to create
            chat_config: Additional configuration for the group chat
            human_input_mode: Human input mode to use
            
        Returns:
            A configured VaahAIGroupChatManager instance with broadcast chat type
        """
        return cls.create_group_chat(
            agent_configs=agent_configs,
            chat_config=chat_config,
            chat_type=GroupChatType.BROADCAST,
            human_input_mode=human_input_mode
        )
    
    @classmethod
    def create_custom_chat(
        cls,
        agent_configs: List[Dict[str, Any]],
        custom_class: str,
        chat_config: Optional[Dict[str, Any]] = None,
        human_input_mode: Optional[Union[HumanInputMode, str]] = None
    ) -> VaahAIGroupChatManager:
        """
        Create a custom group chat manager.
        
        Args:
            agent_configs: List of agent configurations to create
            custom_class: Fully qualified name of the custom group chat class
            chat_config: Additional configuration for the group chat
            human_input_mode: Human input mode to use
            
        Returns:
            A configured VaahAIGroupChatManager instance with custom chat type
        """
        if chat_config is None:
            chat_config = {}
        
        chat_config["custom_class"] = custom_class
        
        return cls.create_group_chat(
            agent_configs=agent_configs,
            chat_config=chat_config,
            chat_type=GroupChatType.CUSTOM,
            human_input_mode=human_input_mode
        )
