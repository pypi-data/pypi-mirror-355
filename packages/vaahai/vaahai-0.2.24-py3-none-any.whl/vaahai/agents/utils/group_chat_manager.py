"""
Group Chat Manager for VaahAI.

This module provides a wrapper around Microsoft Autogen's GroupChat functionality,
enabling multi-agent collaboration with proper message routing, termination conditions,
and integration with existing VaahAI agents.
"""

from typing import Any, Dict, List, Optional, Callable, Union, Tuple
import logging
from enum import Enum

# Define dummy classes for type hints in case imports fail
class GroupChat:
    """Mock implementation of GroupChat for test mode."""
    pass

class GroupChatManager:
    """Mock implementation of GroupChatManager for test mode."""
    pass

class RoundRobinGroupChat:
    """Mock implementation of RoundRobinGroupChat for test mode."""
    pass

class SelectorGroupChat:
    """Mock implementation of SelectorGroupChat for test mode."""
    pass

class BroadcastGroupChat:
    """Mock implementation of BroadcastGroupChat for test mode."""
    pass

# Set flag to assume packages are not available initially
AUTOGEN_PACKAGES_AVAILABLE = False

# Check if packages are available without trying specific imports first
try:
    import autogen_agentchat
    import autogen_ext
    
    # Now try to import the specific classes we need
    try:
        from autogen_agentchat.agentchat.groupchat import GroupChat, GroupChatManager
        from autogen_agentchat.agentchat.groupchat import RoundRobinGroupChat, SelectorGroupChat, BroadcastGroupChat
        
        # If we got here, all required classes are available
        AUTOGEN_PACKAGES_AVAILABLE = True
    except (ImportError, AttributeError) as class_err:
        # Specific classes not found, log the issue
        logging.warning(
            f"Some autogen group chat classes not available: {str(class_err)}. "
            "Running in test mode only."
        )
except ImportError as e:
    # Base packages not found
    logging.warning(
        f"autogen-agentchat/autogen-ext packages not found: {str(e)}. "
        "Running in test mode only."
    )

# Import internal modules
from vaahai.agents.base.agent_base import AgentBase
from vaahai.agents.base.autogen_agent_base import AutoGenAgentBase
from vaahai.cli.utils.config import load_config, get_config_value

# Set up logging
logger = logging.getLogger(__name__)


class GroupChatType(Enum):
    """Enum for different types of group chats supported."""
    ROUND_ROBIN = "round_robin"
    SELECTOR = "selector"
    BROADCAST = "broadcast"
    CUSTOM = "custom"


class HumanInputMode(Enum):
    """Enum for different modes of human participation in group chats."""
    ALWAYS = "always"  # Always ask for human input
    NEVER = "never"  # Never ask for human input
    TERMINATE = "terminate"  # Ask for human input only for termination decisions
    FEEDBACK = "feedback"  # Ask for human input for feedback on agent responses


class VaahAIGroupChatManager:
    """
    Manages multi-agent conversations using AutoGen's GroupChat functionality.
    
    This class provides a wrapper around Autogen's GroupChat classes with additional
    functionality specific to VaahAI, such as message filtering, termination conditions,
    and human-in-the-loop integration.
    
    Attributes:
        agents (List[AutoGenAgentBase]): List of VaahAI agents to participate in the chat.
        config (Dict[str, Any]): Configuration dictionary for the group chat.
        autogen_agents (List): List of underlying Autogen agents.
        group_chat (Any): The Autogen GroupChat instance.
        chat_type (GroupChatType): The type of group chat to use.
        human_input_mode (HumanInputMode): Mode for human participation.
        max_rounds (int): Maximum number of conversation rounds.
        messages (List[Dict[str, Any]]): List of messages in the conversation.
    """
    
    def __init__(
        self, 
        agents: List[AutoGenAgentBase], 
        config: Optional[Dict[str, Any]] = None,
        chat_type: Union[GroupChatType, str] = GroupChatType.ROUND_ROBIN,
        human_input_mode: Union[HumanInputMode, str] = HumanInputMode.TERMINATE
    ):
        """
        Initialize the group chat manager with the given agents and configuration.
        
        Args:
            agents: List of VaahAI agents to participate in the chat.
            config: Configuration dictionary for the group chat.
            chat_type: Type of group chat to use (round_robin, selector, broadcast, custom).
            human_input_mode: Mode for human participation in the chat.
        """
        self.agents = agents
        self.config = config or {}
        
        # Convert string enum values to enum objects if needed
        if isinstance(chat_type, str):
            try:
                self.chat_type = GroupChatType(chat_type.lower())
            except ValueError:
                logger.warning(f"Unknown chat type: {chat_type}. Using ROUND_ROBIN.")
                self.chat_type = GroupChatType.ROUND_ROBIN
        else:
            self.chat_type = chat_type
            
        if isinstance(human_input_mode, str):
            try:
                self.human_input_mode = HumanInputMode(human_input_mode.lower())
            except ValueError:
                logger.warning(f"Unknown human input mode: {human_input_mode}. Using TERMINATE.")
                self.human_input_mode = HumanInputMode.TERMINATE
        else:
            self.human_input_mode = human_input_mode
        
        # Extract autogen agents from VaahAI agents
        self.autogen_agents = [agent.agent for agent in agents if hasattr(agent, 'agent')]
        
        # Check if we're in test mode
        self.test_mode = self.config.get("_test_mode", False)
        
        # If packages are not available and not in test mode, set test mode
        if not AUTOGEN_PACKAGES_AVAILABLE and not self.test_mode:
            self.config["_test_mode"] = True
            self.test_mode = True
            logger.warning("AutoGen packages not available. Running in test mode.")
        
        # Set max rounds from config or default
        self.max_rounds = self.config.get("max_rounds", 10)
        
        # Initialize messages list
        self.messages = []
        
        # Create the group chat instance
        self.group_chat = self._create_group_chat()
        
    def _create_group_chat(self) -> Any:
        """
        Create an AutoGen GroupChat instance based on the configured chat type.
        
        Returns:
            The created GroupChat instance.
        """
        if self.test_mode:
            logger.info("Creating mock group chat in test mode")
            return type('MockGroupChat', (), {
                'agents': self.autogen_agents,
                'messages': [],
                'max_round': self.max_rounds,
                'add_agent': lambda agent: None,
                'remove_agent': lambda agent: None
            })
        
        # Common parameters for all group chat types
        common_params = {
            'agents': self.autogen_agents,
            'messages': [],
            'max_round': self.max_rounds,
            'allow_repeat_speaker': self.config.get('allow_repeat_speaker', False),
            'speaker_selection_method': self.config.get('speaker_selection_method', 'auto'),
            'send_introductions': self.config.get('send_introductions', True),
        }
        
        # Create the appropriate group chat type
        if self.chat_type == GroupChatType.ROUND_ROBIN:
            return RoundRobinGroupChat(**common_params)
        
        elif self.chat_type == GroupChatType.SELECTOR:
            # For selector chat, we need a selection function
            selection_function = self.config.get('selection_function')
            if not selection_function:
                logger.warning("No selection function provided for SELECTOR chat type. Using default.")
            
            return SelectorGroupChat(
                **common_params,
                selector_agent=self.config.get('selector_agent'),
                selection_function=selection_function
            )
        
        elif self.chat_type == GroupChatType.BROADCAST:
            return BroadcastGroupChat(**common_params)
        
        elif self.chat_type == GroupChatType.CUSTOM:
            # For custom chat, we need a custom group chat class
            custom_class = self.config.get('custom_class')
            if not custom_class:
                logger.warning("No custom class provided for CUSTOM chat type. Using RoundRobinGroupChat.")
                return RoundRobinGroupChat(**common_params)
            
            return custom_class(**common_params)
        
        # Default to RoundRobinGroupChat if chat_type is not recognized
        logger.warning(f"Unknown chat type: {self.chat_type}. Using RoundRobinGroupChat.")
        return RoundRobinGroupChat(**common_params)
    
    def _create_termination_function(self) -> Optional[Callable]:
        """
        Create a termination function based on the configuration.
        
        Returns:
            A function that determines when to terminate the conversation, or None.
        """
        if self.test_mode:
            return None
            
        termination_config = self.config.get("termination", {})
        
        # If no termination config is provided, return None
        if not termination_config:
            return None
            
        # Get termination parameters
        max_messages = termination_config.get("max_messages")
        completion_indicators = termination_config.get("completion_indicators", [])
        custom_termination_function = termination_config.get("custom_function")
        
        # If a custom termination function is provided, use it
        if custom_termination_function and callable(custom_termination_function):
            return custom_termination_function
            
        # Otherwise, create a termination function based on the parameters
        def termination_function(messages: List[Dict[str, Any]]) -> bool:
            # Check if max messages has been reached
            if max_messages and len(messages) >= max_messages:
                return True
                
            # Check for completion indicators in the last message
            if completion_indicators and messages:
                last_message = messages[-1].get("content", "")
                for indicator in completion_indicators:
                    if indicator in last_message:
                        return True
                        
            # Default to not terminating
            return False
            
        return termination_function
    
    def _create_message_filter(self) -> Optional[Callable]:
        """
        Create a message filter function based on the configuration.
        
        Returns:
            A function that filters messages, or None.
        """
        if self.test_mode:
            return None
            
        filter_config = self.config.get("message_filter", {})
        
        # If no filter config is provided, return None
        if not filter_config:
            return None
            
        # Get filter parameters
        excluded_agents = filter_config.get("excluded_agents", [])
        excluded_content = filter_config.get("excluded_content", [])
        custom_filter_function = filter_config.get("custom_function")
        
        # If a custom filter function is provided, use it
        if custom_filter_function and callable(custom_filter_function):
            return custom_filter_function
            
        # Otherwise, create a filter function based on the parameters
        def filter_function(message: Dict[str, Any]) -> bool:
            # Check if the message is from an excluded agent
            sender = message.get("sender", "")
            if sender in excluded_agents:
                return False
                
            # Check if the message contains excluded content
            content = message.get("content", "")
            for excluded in excluded_content:
                if excluded in content:
                    return False
                    
            # Default to including the message
            return True
            
        return filter_function
    
    def _setup_human_input_mode(self) -> Dict[str, Any]:
        """
        Set up the human input configuration based on the human input mode.
        
        Returns:
            Dictionary with human input configuration.
        """
        if self.test_mode:
            return {}
            
        human_input_config = {}
        
        if self.human_input_mode == HumanInputMode.ALWAYS:
            human_input_config["human_input_mode"] = "ALWAYS"
        elif self.human_input_mode == HumanInputMode.NEVER:
            human_input_config["human_input_mode"] = "NEVER"
        elif self.human_input_mode == HumanInputMode.TERMINATE:
            human_input_config["human_input_mode"] = "TERMINATE"
        elif self.human_input_mode == HumanInputMode.FEEDBACK:
            human_input_config["human_input_mode"] = "FEEDBACK"
        
        return human_input_config
    
    async def start_chat(self, message: str) -> Dict[str, Any]:
        """
        Start a group chat with the given message.
        
        Args:
            message: The initial message to start the conversation with.
            
        Returns:
            Dictionary containing the result and messages from the conversation.
        """
        if self.test_mode:
            logger.info(f"Starting mock group chat with message: {message}")
            self.messages.append({
                "sender": "user",
                "content": message
            })
            return {"result": "Test mode active. No actual chat performed.", "messages": self.messages}
        
        # Create a GroupChatManager with the group chat
        manager_config = {}
        
        # Add termination function if configured
        termination_function = self._create_termination_function()
        if termination_function:
            manager_config["termination_function"] = termination_function
            
        # Add message filter if configured
        message_filter = self._create_message_filter()
        if message_filter:
            manager_config["message_filter"] = message_filter
            
        # Set up human input mode
        human_input_config = self._setup_human_input_mode()
        manager_config.update(human_input_config)
        
        # Add any additional configuration from the config dictionary
        if "manager_config" in self.config:
            manager_config.update(self.config["manager_config"])
        
        # Create the manager
        manager = GroupChatManager(
            groupchat=self.group_chat,
            **manager_config
        )
        
        # Start the chat with the given message
        result = await manager.run(message)
        
        # Store the messages for later retrieval
        self.messages = self.group_chat.messages
        
        return {"result": result, "messages": self.messages}
    
    def add_agent(self, agent: AutoGenAgentBase) -> None:
        """
        Add an agent to the group chat.
        
        Args:
            agent: The VaahAI agent to add to the group chat.
        """
        if not hasattr(agent, 'agent'):
            logger.warning(f"Agent {agent.name} does not have an underlying Autogen agent.")
            return
            
        if self.test_mode:
            logger.info(f"Adding agent {agent.name} to mock group chat")
            self.agents.append(agent)
            self.autogen_agents.append(agent.agent)
            return
            
        # Add the agent to our lists
        self.agents.append(agent)
        self.autogen_agents.append(agent.agent)
        
        # Add the agent to the group chat
        self.group_chat.add_agent(agent.agent)
    
    def remove_agent(self, agent: AutoGenAgentBase) -> None:
        """
        Remove an agent from the group chat.
        
        Args:
            agent: The VaahAI agent to remove from the group chat.
        """
        if not hasattr(agent, 'agent'):
            logger.warning(f"Agent {agent.name} does not have an underlying Autogen agent.")
            return
            
        if self.test_mode:
            logger.info(f"Removing agent {agent.name} from mock group chat")
            if agent in self.agents:
                self.agents.remove(agent)
            if agent.agent in self.autogen_agents:
                self.autogen_agents.remove(agent.agent)
            return
            
        # Remove the agent from our lists
        if agent in self.agents:
            self.agents.remove(agent)
        if agent.agent in self.autogen_agents:
            self.autogen_agents.remove(agent.agent)
            
        # Remove the agent from the group chat
        self.group_chat.remove_agent(agent.agent)
    
    def get_chat_history(self) -> List[Dict[str, Any]]:
        """
        Get the chat history.
        
        Returns:
            List of messages in the conversation.
        """
        if self.test_mode:
            return self.messages
            
        return self.group_chat.messages
