# VaahAI CLI Module

This directory contains the CLI implementation for the VaahAI project using Typer and InquirerPy.

## Structure

- Command groups for different functionalities
- Interactive prompts using InquirerPy
- Rich terminal output formatting

## Core Commands

- `vaahai config init` - Initial setup for LLM choices, API keys, models, and Docker usage
- `vaahai helloworld` - Test command to verify proper functioning
- `vaahai audit [PATH]` - Thorough code examination for security, compliance, and quality
- `vaahai review [PATH]` - Focus on improving code quality and catching bugs

## Implementation

The CLI is built using Typer for command structure and InquirerPy for interactive prompts. Rich is used for enhanced terminal output formatting.

Each command is implemented as a separate module within this directory, with a common entry point that registers all commands with the Typer app.
