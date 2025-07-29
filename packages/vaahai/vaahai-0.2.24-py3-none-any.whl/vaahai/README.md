# VaahAI Source Code

This directory contains the main source code for the VaahAI project, a multi AI agent CLI tool built with Microsoft's Autogen Framework.

## Directory Structure

- `cli/` - Contains all CLI commands and utilities using Typer and InquirerPy
- `agents/` - Contains AI agent implementations using Microsoft Autogen Framework
- `tests/` - Contains unit and end-to-end tests

## Overview

VaahAI is designed to provide code review, code audit, code generation, and scaffolding capabilities using multiple specialized AI agents. The tool uses Typer for CLI implementation, InquirerPy for interactive prompts, and Microsoft Autogen for AI agent orchestration.

## Key Features

- Code review and audit capabilities
- Multiple specialized AI agents for different tasks
- Interactive CLI with rich terminal output
- Configuration management for LLM API keys and preferences
- Support for various LLM providers including OpenAI, Claude, Junie, and local LLMs via Ollama
