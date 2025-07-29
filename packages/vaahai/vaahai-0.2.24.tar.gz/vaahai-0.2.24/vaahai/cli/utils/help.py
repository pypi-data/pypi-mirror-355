"""
Custom help formatting utilities for VaahAI CLI.

This module provides utilities for enhancing Typer's help output with Rich formatting.
"""

from typing import Any, Callable, Dict, List, Optional

import typer
from rich.box import ROUNDED, SIMPLE
from rich.columns import Columns
from rich.console import Console
from rich.markdown import Markdown
from rich.padding import Padding
from rich.panel import Panel
from rich.style import Style
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from typer.core import TyperCommand, TyperGroup

console = Console()

# Define consistent styles for help formatting
STYLES = {
    "app_name": "bold cyan",
    "app_description": "italic",
    "section_title": "bold magenta",
    "command_group": "magenta",
    "command": "cyan",
    "option": "green",
    "argument": "yellow",
    "example": "green",
    "usage": "bold",
    "default": "dim",
    "header_border": "cyan",
    "table_border": "blue",
}


class CustomHelpCommand(TyperCommand):
    """Custom command class that overrides the help display."""

    def get_help(self, ctx: typer.Context) -> str:
        """Override the default help command to use Rich formatting."""
        # Use our custom help formatter instead of the default
        format_command_help(ctx)
        return ""

    def list_commands(self, ctx: typer.Context) -> List[str]:
        """Return list of commands sorted alphabetically."""
        return sorted(super().list_commands(ctx))


class CustomHelpGroup(TyperGroup):
    """Custom group class that overrides the help display."""

    def get_help(self, ctx: typer.Context) -> str:
        """Override the default help command to use Rich formatting."""
        # Use our custom help formatter for the main app
        if ctx.parent is None:
            show_custom_help(ctx)
        else:
            format_command_help(ctx)
        return ""

    def list_commands(self, ctx: typer.Context) -> List[str]:
        """Return list of commands sorted alphabetically."""
        return sorted(super().list_commands(ctx))


def create_typer_app(
    name: str,
    help: str,
    add_completion: bool = True,
    no_args_is_help: bool = True,
    **kwargs,
) -> typer.Typer:
    """
    Create a Typer app with custom help formatting.

    Args:
        name: Name of the command
        help: Help text for the command
        add_completion: Whether to add shell completion
        no_args_is_help: Whether to show help when no args are provided
        **kwargs: Additional arguments to pass to Typer

    Returns:
        A Typer app with custom help formatting
    """
    # Set default context settings if not provided
    if "context_settings" not in kwargs:
        kwargs["context_settings"] = {"help_option_names": ["--help", "-h"]}

    return typer.Typer(
        name=name,
        help=help,
        add_completion=add_completion,
        no_args_is_help=no_args_is_help,
        cls=CustomHelpGroup,
        **kwargs,
    )


def custom_callback(ctx: typer.Context):
    """
    Custom callback for the main CLI app to enhance help output.

    Args:
        ctx: Typer context object
    """
    if ctx.invoked_subcommand is None:
        show_custom_help(ctx)


def show_custom_help(ctx: typer.Context):
    """
    Display custom formatted help using Rich.

    Args:
        ctx: Typer context object
    """
    # Get the command name
    command_name = ctx.command.name or "vaahai"

    # Create header
    header = Text()
    header.append(f"\n{command_name} ", style=STYLES["app_name"])
    header.append(
        "- A multi AI agent CLI tool using Microsoft Autogen Framework\n",
        style=STYLES["app_description"],
    )

    # Create usage section
    usage = Text("Usage: ", style=STYLES["usage"])
    usage.append(f"{command_name} [OPTIONS] COMMAND [ARGS]...\n\n")

    # Create command groups table
    groups_table = Table(
        title="Command Groups",
        box=ROUNDED,
        padding=(0, 2),
        expand=True,
        border_style=STYLES["table_border"],
        style=STYLES["section_title"],
    )
    groups_table.add_column("Group", style=STYLES["command_group"], no_wrap=True)
    groups_table.add_column("Description")
    groups_table.add_column("Example", style=STYLES["example"])

    # Command group examples dictionary
    group_examples: Dict[str, str] = {
        "core": f"{command_name} core config init",
        "project": f"{command_name} project review run ./my-project",
        "dev": f"{command_name} dev helloworld run",
    }

    # Add command groups to table
    group_commands = {
        "core": "Essential VaahAI commands",
        "project": "Project analysis commands",
        "dev": "Development and testing commands",
    }

    for name, description in sorted(group_commands.items()):
        example = group_examples.get(name, f"{command_name} {name}")
        groups_table.add_row(name, description, example)

    # Create commands table for backward compatibility
    commands_table = Table(
        title="Commands (Direct Access)",
        box=ROUNDED,
        padding=(0, 2),
        expand=True,
        border_style=STYLES["table_border"],
        style=STYLES["section_title"],
    )
    commands_table.add_column("Command", style=STYLES["command"], no_wrap=True)
    commands_table.add_column("Description")
    commands_table.add_column("Example", style=STYLES["example"])

    # Command examples dictionary
    examples: Dict[str, str] = {
        "helloworld": f"{command_name} helloworld run",
        "config": f"{command_name} config init",
        "review": f"{command_name} review run ./my-project",
        "audit": f"{command_name} audit run ./my-project --security",
        "version": f"{command_name} version show",
    }

    # Filter out command groups from direct commands
    direct_commands = {}
    for name, command in sorted(ctx.command.commands.items()):
        if name not in group_commands:
            direct_commands[name] = command

    # Add commands to table
    for name, command in sorted(direct_commands.items()):
        example = examples.get(name, f"{command_name} {name}")
        commands_table.add_row(name, getattr(command, "help", ""), example)

    # Create options table
    options_table = Table(
        title="Global Options",
        box=ROUNDED,
        padding=(0, 2),
        expand=True,
        border_style=STYLES["table_border"],
        style=STYLES["section_title"],
    )
    options_table.add_column("Option", style=STYLES["option"], no_wrap=True)
    options_table.add_column("Description")
    options_table.add_column("Default", style=STYLES["default"])

    # Add options to table
    for param in ctx.command.params:
        options = []
        for opt in getattr(param, "opts", []):
            options.append(opt)
        options_str = ", ".join(options)

        # Get default value if any
        default = ""
        if (
            hasattr(param, "default")
            and param.default is not None
            and param.default is not ...
        ):
            default = str(param.default)

        help_text = getattr(param, "help", "")
        options_table.add_row(options_str, help_text, default)

    # Create environment variables panel
    env_vars_md = """
    **Environment Variables:**

    * `VAAHAI_DEBUG=1` - Enable debug mode with full error tracebacks
    * `VAAHAI_CONFIG_DIR` - Override default config directory location
    """

    # Create quick reference section
    quick_reference = Text("Quick Reference:\n", style=STYLES["section_title"])
    quick_reference.append("• Show version: ", style="bold")
    quick_reference.append(f"{command_name} --version\n", style=STYLES["example"])
    quick_reference.append("• Show command help: ", style="bold")
    quick_reference.append(f"{command_name} COMMAND --help\n", style=STYLES["example"])
    quick_reference.append("• Enable shell completion: ", style="bold")
    quick_reference.append(
        f"{command_name} --install-completion\n", style=STYLES["example"]
    )

    # Print everything
    console.print(Panel(header, border_style=STYLES["header_border"], expand=False))
    console.print(usage)
    console.print(groups_table)
    console.print(commands_table)
    console.print(options_table)
    console.print(
        Panel(
            Markdown(env_vars_md),
            title="Environment Variables",
            border_style=STYLES["table_border"],
            style=STYLES["section_title"],
        )
    )
    console.print(
        Panel(
            quick_reference,
            title="Quick Reference",
            border_style=STYLES["table_border"],
            style=STYLES["section_title"],
        )
    )
    console.print(
        "\nRun a command with --help to see command-specific options and examples.\n"
    )


def format_command_help(ctx: typer.Context):
    """
    Format help for a specific command.

    Args:
        ctx: Typer context object for the command
    """
    command = ctx.command
    command_path = " ".join(ctx.command_path.split())

    # Create header
    header = Text()
    header.append(f"\n{command_path}\n", style=STYLES["app_name"])

    if command.help:
        header.append(f"\n{command.help}\n", style=STYLES["app_description"])

    # Create usage section
    usage = Text("Usage: ", style=STYLES["usage"])
    usage.append(f"{command_path} [OPTIONS]")

    if command.params:
        for param in command.params:
            if param.param_type_name == "argument":
                required = getattr(param, "required", True)
                if required:
                    usage.append(f" {param.name.upper()}")
                else:
                    usage.append(f" [{param.name.upper()}]")

    usage.append("\n\n")

    # Create options table if there are options
    has_options = False
    for param in command.params:
        if param.param_type_name == "option":
            has_options = True
            break

    if has_options:
        options_table = Table(
            title="Options",
            box=ROUNDED,
            padding=(0, 2),
            expand=True,
            border_style=STYLES["table_border"],
            style=STYLES["section_title"],
        )
        options_table.add_column("Option", style=STYLES["option"], no_wrap=True)
        options_table.add_column("Description")
        options_table.add_column("Default", style=STYLES["default"])

        for param in command.params:
            if param.param_type_name == "option":
                options = []
                for opt in getattr(param, "opts", []):
                    options.append(opt)
                options_str = ", ".join(options)

                # Get default value if any
                default = ""
                if (
                    hasattr(param, "default")
                    and param.default is not None
                    and param.default is not ...
                ):
                    default = str(param.default)

                help_text = getattr(param, "help", "")
                options_table.add_row(options_str, help_text, default)

    # Create arguments table if there are arguments
    has_args = False
    for param in command.params:
        if param.param_type_name == "argument":
            has_args = True
            break

    if has_args:
        args_table = Table(
            title="Arguments",
            box=ROUNDED,
            padding=(0, 2),
            expand=True,
            border_style=STYLES["table_border"],
            style=STYLES["section_title"],
        )
        args_table.add_column("Argument", style=STYLES["argument"], no_wrap=True)
        args_table.add_column("Description")
        args_table.add_column("Type", style=STYLES["default"])
        args_table.add_column("Required", style=STYLES["default"])

        for param in command.params:
            if param.param_type_name == "argument":
                arg_type = getattr(param.type, "__name__", str(param.type))
                help_text = getattr(param, "help", "")
                required = getattr(param, "required", True)
                required_str = "Yes" if required else "No"
                args_table.add_row(param.name, help_text, arg_type, required_str)

    # Create examples section if available
    examples = get_command_examples(command_path)

    # Print everything
    console.print(Panel(header, border_style=STYLES["header_border"], expand=False))
    console.print(usage)

    if has_args:
        console.print(args_table)

    if has_options:
        console.print(options_table)

    # Print subcommands if any
    if hasattr(command, "commands") and command.commands:
        subcommands_table = Table(
            title="Subcommands",
            box=ROUNDED,
            padding=(0, 2),
            expand=True,
            border_style=STYLES["table_border"],
            style=STYLES["section_title"],
        )
        subcommands_table.add_column("Command", style=STYLES["command"], no_wrap=True)
        subcommands_table.add_column("Description")

        for name, subcmd in sorted(command.commands.items()):
            subcommands_table.add_row(name, getattr(subcmd, "help", ""))

        console.print(subcommands_table)

    # Print examples if available
    if examples:
        examples_panel = Panel(
            Padding(Markdown(examples), (1, 2)),
            title="Examples",
            border_style=STYLES["table_border"],
            style=STYLES["section_title"],
            expand=True,
        )
        console.print(examples_panel)

    console.print("\nRun a subcommand with --help to see command-specific options.\n")


def get_command_examples(command_path: str) -> str:
    """
    Get examples for a specific command.

    Args:
        command_path: The command path (e.g., "vaahai config init")

    Returns:
        Markdown formatted string with examples
    """
    # Dictionary of command examples
    examples = {
        "vaahai config": """
```bash
# Initialize configuration
vaahai config init

# Show current configuration
vaahai config show

# Set a specific configuration value
vaahai config set api.key "your-api-key"
```
        """,
        "vaahai config init": """
```bash
# Run interactive configuration wizard
vaahai config init

# Run configuration with defaults
vaahai config init --defaults
```
        """,
        "vaahai review": """
```bash
# Review a specific file
vaahai review run ./path/to/file.py

# Review an entire directory
vaahai review run ./path/to/project --recursive

# Review with specific focus
vaahai review run ./path/to/file.py --focus security
```
        """,
        "vaahai audit": """
```bash
# Audit a specific file
vaahai audit run ./path/to/file.py

# Audit an entire directory
vaahai audit run ./path/to/project --recursive

# Audit with specific focus
vaahai audit run ./path/to/project --security --compliance
```
        """,
        "vaahai dev helloworld": """
```bash
# Run the hello world test
vaahai dev helloworld run

# Run with verbose output
vaahai dev helloworld run --verbose
```
        """,
    }

    # Try to find the most specific example first, then fall back to more general ones
    if command_path in examples:
        return examples[command_path]

    # Try to match partial command paths
    for cmd, example in examples.items():
        if command_path.startswith(cmd):
            return example

    return ""
