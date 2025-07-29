"""
Base class for Autogen agents.

This module provides the base classes for implementing agents using the
Autogen framework, handling common tasks like configuration, LLM setup,
and agent initialization.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
import os
import logging

# Define dummy classes for type hints in case imports fail
class BaseChatAgent:
    """Mock implementation of BaseChatAgent for test mode."""
    pass

class OpenAIChatCompletionClient:
    """Mock implementation of OpenAIChatCompletionClient for test mode."""
    def __init__(self, model: str = None, api_key: str = None):
        self.model = model
        self.api_key = api_key
        self.api_base = None

# Set flag to assume packages are not available initially
AUTOGEN_PACKAGES_AVAILABLE = False

# Check if packages are available without trying specific imports first
try:
    import autogen_agentchat
    import autogen_ext
    
    # Now try to import the specific classes we need - don't error if they don't exist
    try:
        # Check if these modules and classes exist
        from autogen_agentchat.agents import BaseChatAgent
        from autogen_ext.models.openai import OpenAIChatCompletionClient
        
        # If we got here, all required classes are available
        AUTOGEN_PACKAGES_AVAILABLE = True
    except (ImportError, AttributeError) as class_err:
        # Specific classes not found, log the issue
        logging.warning(
            f"Some autogen classes not available: {str(class_err)}. "
            "Running in test mode only."
        )
except ImportError as e:
    # Base packages not found
    logging.warning(
        f"autogen-agentchat/autogen-ext packages not found: {str(e)}. "
        "Running in test mode only."
    )

# Import internal modules
from vaahai.cli.utils.config import load_config, get_config_value

# Set up logging
logger = logging.getLogger(__name__)


class AgentBase(ABC):
    """Abstract base class for all agents in the system."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the agent with a configuration.
        
        Args:
            config: Dictionary containing agent configuration
        """
        self.config = config
    
    @abstractmethod
    def run(self, *args, **kwargs) -> Any:
        """
        Run the agent with the provided inputs.
        
        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
            
        Returns:
            The result of running the agent
        """
        pass


class AutoGenAgentBase(AgentBase):
    """Base class for agents using the Autogen framework."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the agent with a configuration and set up the LLM.
        
        Args:
            config: Dictionary containing agent configuration
        """
        # Call parent's init first to set up self.config
        super().__init__(config)
        
        # Check if we're in test mode
        test_mode = self.config.get("_test_mode", False)
        
        # If packages are not available and not in test mode, set test mode
        if not AUTOGEN_PACKAGES_AVAILABLE and not test_mode:
            self.config["_test_mode"] = True
            test_mode = True
            logger.warning("AutoGen packages not available. Running in test mode.")
        
        # Don't prepare LLM config in test mode
        if not test_mode:
            self.llm_config = self._prepare_llm_config()
        else:
            self.llm_config = {"model": "gpt-3.5-turbo"}
        
        # Initialize agent to None - subclasses will create it when ready
        self.agent = None
    
    def _prepare_llm_config(self) -> Dict[str, Any]:
        """
        Prepare the LLM configuration for the agent.
        
        Returns:
            Dictionary containing LLM configuration
        """
        # Skip LLM config in test mode
        if self.config.get("_test_mode", False):
            return {"model": "gpt-3.5-turbo"}
            
        try:
            vaahai_config = load_config()
            
            # Always default to OpenAI if provider is not specified
            provider = self.config.get("provider") or get_config_value("llm.provider", vaahai_config) or "openai"
            
            # Get model from config or use default for the provider
            model = self.config.get("model")
            if not model:
                # Try config path with providers prefix
                provider_model_key = f"llm.providers.{provider}.model"
                model = get_config_value(provider_model_key, vaahai_config)
                
                # Try older config path without providers prefix as fallback
                if not model:
                    provider_model_key = f"llm.{provider}.model"
                    model = get_config_value(provider_model_key, vaahai_config)
                
                # If provider-specific model is not found, use default model for OpenAI
                if not model:
                    if provider == "openai":
                        model = "gpt-3.5-turbo"
                    else:
                        # Try to get the default model for the provider
                        model = get_config_value(f"llm.providers.{provider}.model", vaahai_config) or "gpt-3.5-turbo"
                
            # Get API key from config or environment variables
            api_key = self.config.get("api_key")
            if not api_key:
                # Try config path with providers prefix
                provider_api_key = f"llm.providers.{provider}.api_key"
                api_key = get_config_value(provider_api_key, vaahai_config)
                
                # Try older config path without providers prefix as fallback
                if not api_key:
                    provider_api_key = f"llm.{provider}.api_key"
                    api_key = get_config_value(provider_api_key, vaahai_config)
                
                if not api_key:
                    # Check environment variables in order of precedence
                    env_var_name = f"VAAHAI_PROVIDERS_{provider.upper()}_API_KEY"
                    api_key = os.environ.get(env_var_name)
                    
                    # For OpenAI, also check standard environment variable
                    if not api_key and provider.lower() == "openai":
                        api_key = os.environ.get("OPENAI_API_KEY")
                        
                    if not api_key:
                        # If no API key is found for the specified provider, try OpenAI as fallback
                        if provider.lower() != "openai":
                            logger.warning(
                                f"No API key found for provider '{provider}'. Trying OpenAI as fallback."
                            )
                            provider = "openai"
                            model = "gpt-3.5-turbo"
                            api_key = os.environ.get("OPENAI_API_KEY")
                            
                        # If still no API key, raise error
                        if not api_key:
                            raise ValueError(f"No API key found for provider '{provider}'")
            
            # Prepare base LLM config
            llm_config = {
                "model": model,
                "temperature": self.config.get("temperature", 0.7),
                "api_key": api_key
            }
            
            # Handle API base URL
            api_base = self.config.get("api_base")
            if not api_base:
                # Try config path with providers prefix
                provider_api_base = f"llm.providers.{provider}.api_base"
                api_base = get_config_value(provider_api_base, vaahai_config)
                
                # Try older config path without providers prefix as fallback
                if not api_base:
                    provider_api_base = f"llm.{provider}.api_base"
                    api_base = get_config_value(provider_api_base, vaahai_config)
                
                if not api_base:
                    env_var_name = f"VAAHAI_PROVIDERS_{provider.upper()}_API_BASE"
                    api_base = os.environ.get(env_var_name)
                    
                    # For OpenAI, also check standard environment variable
                    if not api_base and provider.lower() == "openai":
                        api_base = os.environ.get("OPENAI_API_BASE")
                
            if api_base:
                llm_config["api_base"] = api_base
                
            # For project-specific keys (sk-proj-), set API type to azure
            if api_key and api_key.startswith("sk-proj-"):
                llm_config["api_type"] = "azure"
                
            # Update with any additional LLM config from agent config
            if "llm_config" in self.config:
                llm_config.update(self.config["llm_config"])
                
            return llm_config
            
        except Exception as e:
            raise ValueError(f"Error preparing LLM configuration: {str(e)}")

    def _create_model_client(self) -> Optional[OpenAIChatCompletionClient]:
        """
        Create a model client based on the LLM configuration.
        
        Returns:
            A model client for the agent to use
        """
        # Skip in test mode
        if self.config.get("_test_mode", False):
            return None
            
        # Skip if packages are not available
        if not AUTOGEN_PACKAGES_AVAILABLE:
            return None
            
        # Create OpenAI client
        if self.config.get("provider", "openai").lower() == "openai":
            client = OpenAIChatCompletionClient(
                model=self.llm_config.get("model", "gpt-3.5-turbo"),
                api_key=self.llm_config.get("api_key"),
            )
            
            # Set API base if provided
            if "api_base" in self.llm_config:
                client.api_base = self.llm_config["api_base"]
                
            return client
            
        # TODO: Add support for other providers
        
        # Default to None if provider not supported
        return None
    
    @abstractmethod
    def _create_autogen_agent(self) -> Any:
        """
        Create an Autogen agent based on the configuration.
        
        This method should be implemented by subclasses to create the specific
        type of Autogen agent needed for their use case.
        
        Returns:
            An Autogen agent instance
        """
        pass

    @abstractmethod
    def run(self, *args, **kwargs) -> Any:
        """
        Run the agent with the provided inputs.
        
        Args:
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
            
        Returns:
            The result of running the agent
            
        This method must be implemented by subclasses.
        """
        pass

    def update_system_message(self, system_message: str) -> None:
        """
        Update the system message for the agent.
        
        Args:
            system_message: New system message
        """
        if hasattr(self.agent, "update_system_message"):
            self.agent.update_system_message(system_message)
        else:
            raise NotImplementedError("The underlying agent does not support updating system messages")
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """
        Get the conversation history for the agent.
        
        Returns:
            List of messages in the conversation history.
        """
        if self.config.get("_test_mode", False):
            return []
            
        if hasattr(self.agent, "get_conversation_history"):
            return self.agent.get_conversation_history()
        else:
            return []
