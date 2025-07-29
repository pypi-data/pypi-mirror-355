"""
VaahAI Agents module.

This module contains the AI agent implementations using Microsoft Autogen Framework.
"""

# Import base components
from vaahai.agents.base.agent_base import AgentBase
from vaahai.agents.base.autogen_agent_base import AutoGenAgentBase
from vaahai.agents.base.agent_registry import AgentRegistry
from vaahai.agents.base.agent_factory import AgentFactory

# Import application agents
from vaahai.agents.applications.hello_world import HelloWorldAgent
from vaahai.agents.applications.framework_detection import FrameworkDetectionAgent
from vaahai.agents.applications.language_detection import LanguageDetectionAgent

# Export public API
__all__ = [
    "AgentBase",
    "AutoGenAgentBase",
    "AgentRegistry",
    "AgentFactory",
    "HelloWorldAgent",
    "FrameworkDetectionAgent",
    "LanguageDetectionAgent",
]
