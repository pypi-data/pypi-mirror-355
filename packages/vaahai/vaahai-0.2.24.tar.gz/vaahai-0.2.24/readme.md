# VaahAI

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)
![Status](https://img.shields.io/badge/status-stable-green.svg)

**VaahAI** is a multi-agent AI CLI tool built with Microsoft's Autogen Framework, designed to enhance code quality and development workflows through AI-powered code review, auditing, generation, and scaffolding capabilities.

## 🌟 Features

- **Multi-Agent Architecture**: Specialized AI agents collaborate to perform complex tasks
- **Code Review**: Comprehensive code review focusing on quality, style, security, and performance
- **Interactive Code Improvements**: Apply suggested code changes with interactive UI and safety features
- **Multiple Output Formats**: Rich terminal output, markdown reports, HTML reports, and interactive mode
- **Code Audit**: Security vulnerability detection, compliance checking, and architectural assessment
- **Code Generation**: AI-powered code generation from natural language descriptions
- **Multiple LLM Support**: OpenAI, Claude, Junie, and local models via Ollama
- **Intelligent Model Selection**: Filter and recommend models based on capabilities (text, code, vision, etc.)
- **Flexible Configuration**: Layered configuration system with global defaults and project-specific settings
- **Git Integration**: Commit applied changes, generate meaningful commit messages, and prepare pull requests

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- [Poetry](https://python-poetry.org/docs/#installation) (Python package manager)
- Git
- Docker (optional, for code execution)

### Installation

```bash
# Install from PyPI
pip3 install vaahai

# Or clone the repository
git clone https://github.com/webreinvent/vaahai.git
cd vaahai

# Create a virtual environment in any of your favorite environment managers:
conda create -n vaahai310 python=3.10
conda activate vaahai310

# Install dependencies with Poetry
poetry install
```

### Quick Start

```bash
# Initialize configuration
vaahai config init

# Show current configuration
vaahai config show

# List available models
vaahai model list

# Run a simple test to verify installation
vaahai helloworld run
```

### Development Setup

```bash
# Install development dependencies
poetry install --with dev

# Install pre-commit hooks
pre-commit install

# Run tests
poetry run pytest

# Run tests with coverage
poetry run pytest --cov=vaahai

# Format code
poetry run black vaahai
poetry run isort vaahai

# Lint code
poetry run flake8 vaahai
poetry run mypy vaahai

# Run all pre-commit hooks manually
pre-commit run --all-files
```

For more details on development tools, see [Development Tools Documentation](docs/development/development_tools.md).

### Configuration

```bash
# Run the configuration wizard
poetry run vaahai config init

# Or manually edit the configuration file
nano ~/.vaahai/config.toml
```

## 🛠️ Usage

### CLI Command Structure

VaahAI provides a modular CLI organized into logical command groups. The command structure follows this hierarchy:

```
vaahai [command_group] [command] [action] [options]
```

Where:
- `vaahai` is the main CLI application
- `command_group` is one of the logical groups (core, project, dev)
- `command` is a specific command within that group
- `action` is a subcommand or action for that command
- `options` are additional flags and parameters

#### Enhanced Help System

VaahAI features a Rich-formatted custom help system that provides visually appealing and well-organized help information:

- Styled headers and descriptions with visual separation
- Organized tables for commands, options, and environment variables
- Consistent formatting across all commands and subcommands
- Detailed descriptions and usage examples
- Color-coded elements for improved readability

To access the enhanced help for any command:

```bash
# Main CLI help
vaahai --help

# Command group help
vaahai [command_group] --help

# Specific command help
vaahai [command_group] [command] --help

# Command action help
vaahai [command_group] [command] [action] --help
```

#### Global Options
- `--version`, `-v`: Display the current version of VaahAI and exit
- `--verbose`, `-V`: Enable verbose output with detailed logs and information
- `--quiet`, `-q`: Suppress non-essential output
- `--config`: Specify an alternative configuration file path
- `--help`, `-h`: Show help message and exit

#### Core Commands
- `vaahai config`: Configuration management
  - `vaahai config init`: Set up initial configuration
  - `vaahai config show`: Display current configuration
- `vaahai version`: Display version information

#### Project Commands
- `vaahai review`: Code review commands
  - `vaahai review [PATH]`: Run a code review on specified path
  - `vaahai review --format [rich|markdown|html|interactive]`: Select output format
  - `vaahai review --apply-changes`: Enable code change acceptance in interactive mode
  - `vaahai review --category [security|performance|style|quality]`: Filter by category
  - `vaahai review --severity [critical|high|medium|low]`: Filter by severity
  - `vaahai review --dry-run`: Preview changes without modifying files
  - `vaahai review --backup-dir [PATH]`: Specify directory for file backups
- `vaahai audit`: Security and compliance audit commands
  - `vaahai audit run`: Run a security/compliance audit on specified path

#### Development Commands
- `vaahai dev helloworld`: Test command to verify proper functioning
  - `vaahai dev helloworld run`: Execute the hello world test
  - `vaahai dev helloworld --help`: Show help for the hello world command
  - Shows detailed debug information including provider, prompt template, and rendered prompt
- `vaahai helloworld`: Simplified version of the hello world command
  - Features location-based personalization with culturally relevant greetings
  - Detects user's location/timezone automatically
  - Use `--dev` flag to see detailed information
- `vaahai dev showcase`: Demonstrate Rich formatting capabilities
- `vaahai dev prompts`: Demonstrate InquirerPy prompt capabilities

All commands support the `--help` flag for detailed usage information. For backward compatibility, direct command access (e.g., `vaahai helloworld` instead of `vaahai dev helloworld`) is also supported.

### Interactive Prompts

VaahAI CLI uses InquirerPy to provide interactive command-line prompts with rich styling. The prompt utilities include:

- Text input with validation
- Password input with masking
- Confirmation prompts (yes/no)
- Selection from a list of options
- Multi-selection from a list of options
- Fuzzy search selection
- Number input with range validation
- Path selection with auto-completion

All prompts support non-interactive mode with default values or appropriate error handling.

### Basic Commands

```bash
# Show help information
vaahai --help

# Show help for a specific command group
vaahai dev --help

# Show help for a specific command
vaahai dev helloworld --help

# Test installation and configuration
vaahai dev helloworld run
# Or using backward compatibility
vaahai helloworld run

# Review code in a file or directory
vaahai review ./my_project --category security --severity high
# Or with interactive code change acceptance
vaahai review ./my_project --format interactive --apply-changes

# Audit a project for security and compliance
vaahai audit run --path ./my_project --security --compliance owasp

# Show version information
vaahai version

# Apply suggested changes
vaahai apply --file review_suggestions.json

# Commit the changes
vaahai commit --message "Fix code quality issues in app.py"
```

### Example Workflow

```bash
# Initialize configuration
vaahai config init

# Review a Python file with interactive code changes
vaahai review ./app.py --format interactive --apply-changes

# Or generate an HTML report
vaahai review ./app.py --format html

# Apply suggested changes
vaahai apply --file review_suggestions.json

# Commit the changes
vaahai commit --message "Fix code quality issues in app.py"
```

### Terminal Output

VaahAI CLI uses Rich for consistent, styled terminal output. Output behavior can be controlled with:

- Verbose mode: Set `--verbose` flag or `VAAHAI_VERBOSE=1` environment variable
- Quiet mode: Set `--quiet` flag or `VAAHAI_QUIET=1` environment variable

For more details on the Rich integration, see the [Rich Integration Documentation](/docs/cli/rich_integration.md).

## 🧪 Testing

VaahAI includes a comprehensive test suite organized into unit tests and integration tests:

```
vaahai/test/
├── unit/                 # Tests for individual components
│   ├── test_cli_utils.py # Tests for console output utilities
│   ├── test_help_utils.py # Tests for help formatting utilities
│   └── test_version.py   # Tests for version command
└── integration/          # Tests for component interactions
    └── test_config_integration.py # Tests for config command
```

Run the test suite:

```bash
# Run all tests
poetry run pytest

# Run tests with coverage report
poetry run pytest --cov=vaahai

# Run specific test file
poetry run pytest vaahai/test/unit/test_cli_utils.py

# Run tests matching a pattern
poetry run pytest -k "config"
```

For more details on testing, see [Testing Guide](docs/development/testing.md) and [Test Implementation](docs/development/test_implementation.md).

## 🏗️ Project Structure

```
vaahai/
├── ai_docs/         # AI-specific documentation
├── ai_prompts/      # Prompt templates for AI agents
├── docs/            # User and developer documentation
│   └── cli/         # CLI-specific documentation
├── specs/           # Project specifications and requirements
├── vaahai/          # Main package
│   ├── agents/      # Agent implementations
│   ├── cli/         # CLI commands and handlers
│   │   ├── commands/  # Command implementations
│   │   │   ├── core/      # Core command group
│   │   │   │   ├── config/    # Configuration commands
│   │   │   │   └── version/   # Version commands
│   │   │   ├── project/   # Project command group
│   │   │   │   ├── audit/     # Audit commands
│   │   │   │   └── review/    # Code review commands
│   │   │   ├── dev/       # Development command group
│   │   │   │   ├── helloworld/  # Hello world test command
│   │   │   │   └── showcase/   # Rich formatting showcase
│   │   │   └── helloworld/  # Legacy direct command (for backward compatibility)
│   │   ├── main.py     # CLI entry point
│   │   └── utils/      # CLI utilities
│   │       ├── console.py  # Rich formatting utilities
│   │       └── help.py     # Custom help formatting
│   ├── config/      # Configuration management
│   ├── llm/         # LLM provider integrations
│   └── utils/       # Utility functions and helpers
└── tests/           # Test suite
    └── cli/         # CLI tests
```

## 📝 Documentation

For more detailed documentation, please refer to:

- [Project Plan](/specs/project_plan.md)
- [Features Specification](/specs/features.md)
- [Technical Architecture](/specs/technical_architecture.md)
- [User Guide](/docs/user_guide.md)
- [API Reference](/docs/api_reference.md)
- [CLI Documentation](/docs/cli/)
  - [Rich Integration Guide](/docs/cli/rich_integration.md)
  - [Command Groups Structure](/docs/cli/command_groups.md)
  - [CLI Architecture](/docs/architecture/cli_architecture.md)
  - [Configuration Management](/docs/cli/config_command.md)
  - [Model Selection](/docs/cli/model_command.md)
  - [Review Command](/docs/cli/review_command.md)
- [Review System Documentation](/docs/review/)
  - [Review Steps Registry](/docs/review/steps_registry.md)
  - [Interactive Diff Reporter](/docs/reporting/interactive_diff_reporter.md)
  - [Markdown Reporter](/docs/reporting/markdown_reporter.md)
  - [HTML Reporter](/docs/reporting/html_reporter.md)
  - [Code Change Manager](/docs/utils/code_change_manager.md)

## 🤝 Contributing

We welcome contributions from the community! Please see our [Contributing Guidelines](CONTRIBUTING.md) for more details on how to get involved.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgements

- [Microsoft Autogen Framework](https://github.com/microsoft/autogen)
- [Typer](https://typer.tiangolo.com/)
- [InquirerPy](https://github.com/kazhala/InquirerPy)
- All our contributors and supporters
