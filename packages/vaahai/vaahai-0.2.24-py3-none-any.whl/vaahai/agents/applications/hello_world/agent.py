"""
Hello World agent implementation.

This module provides a simple Hello World agent that demonstrates
the basic functionality of the VaahAI agent system using the new
autogen-agentchat and autogen-ext packages.
"""

import os
import logging
import asyncio
import random
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

# Define dummy classes for type hints in case imports fail
class MockAssistantAgent:
    """
    Mock implementation of AssistantAgent for testing without LLM.
    """
    def __init__(self, name, system_message):
        self.name = name
        self.system_message = system_message
        
    async def on_messages(self, messages, cancellation_token=None):
        """
        Mock implementation of on_messages that returns a predefined greeting.
        
        Args:
            messages: List of messages (ignored in mock)
            cancellation_token: Optional cancellation token (ignored in mock)
            
        Returns:
            Mock response with greeting content
        """
        # Create a simple response object with a content attribute
        class MockResponse:
            def __init__(self, content):
                self.content = content
                
        # Generate a friendly greeting response
        greeting = f"Hello! I'm {self.name}, your friendly AI assistant. "
        greeting += "I'm running in test mode right now, but I'd normally tell you "
        greeting += "a funny joke. Why did the AI go to therapy? It had too many "
        greeting += "deep learning issues! 😄"
        
        return MockResponse(greeting)

class MockUserMessage:
    """Mock implementation of UserMessage for test mode."""
    def __init__(self, content: str, source: str):
        self.content = content
        self.source = source

class MockTextMessage:
    """Mock implementation of TextMessage for test mode."""
    def __init__(self, content: str, source: str):
        self.content = content
        self.source = source

# Set flag to assume packages are not available initially
AUTOGEN_PACKAGES_AVAILABLE = False

# Simplified imports for AutoGen components - don't over-complicate
try:
    # First check if base packages exist
    import autogen_agentchat
    import autogen_core
    
    # Import specific components we need
    try:
        from autogen_agentchat.agents import AssistantAgent
        from autogen_agentchat.messages import TextMessage, MultiModalMessage
        from autogen_core import _cancellation_token
        from autogen_ext.models.openai import OpenAIChatCompletionClient
        
        # If we got here without exceptions, packages are available
        AUTOGEN_PACKAGES_AVAILABLE = True
        logging.info("AutoGen packages available, running with real LLM capabilities.")
    except (ImportError, AttributeError) as e:
        logging.warning(f"Failed to import AutoGen components: {e}. Running in test mode.")
except ImportError as e:
    logging.warning(f"AutoGen packages not available: {e}. Running in test mode.")

# Set up logging
logger = logging.getLogger(__name__)

from vaahai.agents.base.autogen_agent_base import AutoGenAgentBase
from vaahai.agents.base.agent_registry import AgentRegistry
from vaahai.agents.utils.prompt_manager import PromptManager

@AgentRegistry.register("hello_world")
class HelloWorldAgent(AutoGenAgentBase):
    """
    A simple Hello World agent that demonstrates the basic functionality
    of the VaahAI agent system.
    
    This agent uses the new autogen-agentchat and autogen-ext packages
    and supports project-specific OpenAI API keys.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Hello World agent.
        
        Args:
            config: Configuration dictionary for the agent
        """
        # Call parent's init first to set up self.config
        super().__init__(config)
        
        # Set up the agent name
        self.name = self.config.get("name", "HelloWorldAgent")
        
        # Initialize the prompt manager
        self.prompt_manager = PromptManager(agent_type="hello_world", agent_name=self.name)
        
        # Load the greeting prompt
        self.greeting_prompt = self._load_greeting_prompt()
        
        # Create the agent
        if not hasattr(self, 'agent') or self.agent is None:
            self.agent = self._create_autogen_agent()
    
    def _load_greeting_prompt(self) -> str:
        """
        Load the greeting prompt from the prompt manager.
        
        Returns:
            Greeting prompt string
        """
        # Try to load from prompt manager first
        try:
            # Use render_prompt instead of get_prompt
            context = {
                "agent_name": self.name,
                "temperature": self.config.get("temperature", 0.7)
            }
            prompt = self.prompt_manager.render_prompt("greeting", context)
            if prompt:
                return prompt
        except Exception as e:
            logger.warning(f"Error loading prompt: {str(e)}")
        
        # Default prompt if not found
        return """
        You are a friendly and helpful AI assistant named {agent_name}.
        
        Please respond to the user's greeting with a funny, unique, and creative response.
        Make your response humorous and different each time.
        Include a joke, pun, or playful element in your response.
        Keep your response concise (1-2 sentences).
        """
    
    def _create_autogen_agent(self) -> Any:
        """
        Create an Autogen assistant agent for the Hello World agent.
        
        Returns:
            An Autogen assistant agent instance or None if in test mode
        """
        # Use test mode if specified or if AutoGen packages are not available
        if self.config.get("_test_mode", False) or not AUTOGEN_PACKAGES_AVAILABLE:
            logger.info("Creating mock agent for test mode")
            return MockAssistantAgent(
                name=self.name,
                system_message=self.greeting_prompt.format(agent_name=self.name)
            )
            
        try:
            # Create the model client
            model_client = self._create_model_client()
            if not model_client:
                logger.warning("Failed to create model client, using mock agent")
                return MockAssistantAgent(
                    name=self.name,
                    system_message=self.greeting_prompt.format(agent_name=self.name)
                )
                
            # Create the assistant agent with the funny greeting prompt
            # Use correct parameters based on AssistantAgent signature
            logger.info(f"Creating AssistantAgent with model client")
            return AssistantAgent(
                name=self.name,
                model_client=model_client,
                system_message=self.greeting_prompt.format(agent_name=self.name)
            )
        except Exception as e:
            logger.error(f"Error creating agent: {str(e)}")
            return MockAssistantAgent(
                name=self.name,
                system_message=self.greeting_prompt.format(agent_name=self.name)
            )
    
    def _create_model_client(self) -> Optional[Any]:
        """
        Create a model client for the agent.
        
        This method attempts to create an OpenAIChatCompletionClient
        using the configured API key and model. If the configuration
        is missing or invalid, it returns None.
        
        Returns:
            OpenAIChatCompletionClient instance or None if creation fails
        """
        if not AUTOGEN_PACKAGES_AVAILABLE:
            logger.warning("AutoGen packages not available, cannot create model client")
            return None
            
        try:
            # Access the LLM config property directly from the base class
            if not hasattr(self, 'llm_config') or not self.llm_config:
                logger.warning("No LLM configuration found")
                return None
                
            # Check if we have an OpenAI API key
            api_key = self.llm_config.get("api_key")
            if not api_key:
                logger.warning("No API key found in LLM configuration")
                return None
                
            # Get the model name, defaulting to gpt-4
            model = self.llm_config.get("model", "gpt-4")
            logger.info(f"Creating OpenAI client with model: {model}")
            
            # Create the OpenAI client
            return OpenAIChatCompletionClient(
                model=model,
                api_key=api_key,
                temperature=self.config.get("temperature", 0.7)
            )
        except Exception as e:
            logger.error(f"Error creating model client: {str(e)}")
            return None

    async def _generate_greeting(self, location=None) -> str:
        """
        Generate a greeting message using the agent.
        
        Args:
            location: Optional location/country string to personalize the greeting
        Returns:
            Greeting message string
        """
        if self.agent:
            try:
                # Check if we're in test mode first
                if self.config.get("_test_mode", False):
                    logger.info("Running in test mode with mock agent")
                    # For test mode, we can use simple mock message
                    mock_message = MockUserMessage(
                        content=f"Test mode greeting for {location or 'the world'}!",
                        source="test"
                    )
                    return mock_message.content
                # Render the prompt with location
                prompt_vars = {"location": location or "the world"}
                system_message = self.prompt_manager.render_prompt("greeting", prompt_vars)
                # Use the system message in the agent
                # Use the real TextMessage class for the real agent
                from autogen_agentchat.messages import TextMessage
                response = await self.agent.on_messages([
                    TextMessage(content=system_message, source="system")
                ], cancellation_token=None)
                
                # Extract content from response (handle different response formats)
                if hasattr(response, "chat_message") and response.chat_message:
                    logger.info(f"Extracting content from chat_message: {response.chat_message}")
                    return response.chat_message.content
                elif hasattr(response, "content"):
                    return response.content
                else:
                    logger.warning(f"Unknown response format: {response}")
                    return str(response)
            except Exception as e:
                logger.error(f"Error generating greeting: {str(e)}")
                return f"[Error] {str(e)}"
        # Fallback to a default greeting if there's no agent
        logger.warning("No agent available, using fallback greeting")
        return f"Hello from {self.name}! (Fallback greeting)"

    async def run(self, location=None) -> dict:
        """
        Run the agent to generate a greeting.
        Args:
            location: Optional location/country string to personalize the greeting
        Returns:
            Dict containing the greeting response and status
        """
        try:
            greeting = await self._generate_greeting(location=location)
            # Return a properly structured result dictionary
            return {
                "status": "success",
                "response": greeting
            }
        except Exception as e:
            logger.error(f"Error running HelloWorldAgent: {str(e)}")
            # Return error information in the expected dictionary format
            return {
                "status": "error",
                "error": str(e),
                "response": f"Failed to generate greeting: {str(e)}"
            }
