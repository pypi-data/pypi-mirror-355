# VaahAI Application Agents

This directory contains the application-specific agent implementations for the VaahAI project.

## Agent Types

- `framework_detection` - Detects web frameworks and content management systems (CMS) in code repositories
- `language_detection` - Detects programming languages from code samples
- `hello_world` - Simple demonstration agent for testing the agent system

## Directory Structure

Each agent follows a consistent structure:

```
agent_name/
├── __init__.py        # Exports the main agent class
├── agent.py           # Contains the agent implementation
└── prompts/           # Contains prompt templates for the agent
    └── agent_name.md  # Main prompt template
```

## Usage

Agents should be imported from their respective packages:

```python
from vaahai.agents.applications.framework_detection import FrameworkDetectionAgent
from vaahai.agents.applications.language_detection import LanguageDetectionAgent
```

## Implementation Notes

- All agents extend the `AgentBase` class from `vaahai.agents.base.agent_base`
- Agents are registered with the `AgentRegistry` using the `@AgentRegistry.register` decorator
- Agents use the `PromptManager` for loading and rendering prompt templates
- Each agent implements a `run` method with agent-specific parameters and return values
