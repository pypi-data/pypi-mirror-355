# VaahAI Agents Module

This directory contains the AI agent implementations for the VaahAI project using Microsoft Autogen Framework.

## Agent Types

- `LanguageDetector` - Responsible for detecting the programming language
- `FrameworkOrCMSDetector` - Responsible for detecting the framework or CMS
- `Auditor` - Performs thorough code audits for security, compliance, and quality
- `Reviewer` - Focuses on code quality, bugs, and standards for specific changes
- `Reporter` - Presents audit or review results in various formats (markdown, HTML)
- `Applier` - Applies code changes to files when approved by the user
- `Committer` - Handles git commit operations for applied changes

## Directory Structure

The agents module follows this directory structure:

```
agents/
├── applications/       # Application-specific agent implementations
│   ├── framework_detection/
│   ├── language_detection/
│   └── hello_world/
├── base/               # Base classes and interfaces for all agents
├── utils/              # Utility functions and classes for agents
└── prompts/            # Shared prompt templates
```

## Implementation

Each agent is implemented as a separate module with a clear interface. The agents use the Autogen Framework for orchestration and communication.

The implementation follows an adapter pattern to integrate with Autogen while maintaining flexibility and extensibility. This allows for easy addition of new agent types and capabilities.

## Configuration

Agents are configured through a JSON schema-based configuration system that validates all agent parameters before instantiation. This ensures robust initialization and clear error messages.
