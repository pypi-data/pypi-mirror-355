"""
VaahAI CLI main entry point.

This module serves as the entry point for the VaahAI CLI application.
It defines the main Typer app instance and registers all command groups.
"""

import os
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from vaahai.cli.commands.audit.command import audit_app
from vaahai.cli.commands.chat.command import chat_app
from vaahai.cli.commands.config.command import config_app

# Import command groups
from vaahai.cli.commands.core import core_app
from vaahai.cli.commands.dev import dev_app

# Import direct command modules for backward compatibility
from vaahai.cli.commands.helloworld.command import helloworld_app
from vaahai.cli.commands.model.command import model_app
from vaahai.cli.commands.project import project_app
from vaahai.cli.commands.review.command import review_app
from vaahai.cli.commands.version.command import version_app
from vaahai.cli.utils.console import print_error, print_info
from vaahai.cli.utils.help import create_typer_app

# Create the main Typer app instance with custom help formatting
app = create_typer_app(
    name="vaahai",
    help="A multi AI agent CLI tool using Microsoft Autogen Framework",
    add_completion=True,
    no_args_is_help=True,
    context_settings={"help_option_names": ["--help", "-h"]},
)

# Create a rich console for formatted output
console = Console()

# Add command groups to the main app
app.add_typer(core_app, name="core")
app.add_typer(project_app, name="project")
app.add_typer(dev_app, name="dev")

# Add direct commands for backward compatibility
app.add_typer(helloworld_app, name="helloworld")
app.add_typer(audit_app, name="audit")
app.add_typer(review_app, name="review")
app.add_typer(config_app, name="config")
app.add_typer(model_app, name="model")
app.add_typer(version_app, name="version")
app.add_typer(chat_app, name="chat")


@app.callback(invoke_without_command=True)
def callback(
    ctx: typer.Context,
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        help="Show the version and exit",
        is_flag=True,
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-V",
        help="Enable verbose output with detailed logs and information",
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        help="Suppress all non-essential output",
    ),
    config_file: Optional[str] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to custom configuration file",
    ),
):
    """
    VaahAI: A multi AI agent CLI tool using Microsoft Autogen Framework.

    VaahAI provides a suite of AI-powered tools for code analysis, review, and auditing.
    It leverages Microsoft's Autogen Framework to create a multi-agent system that can
    understand, analyze, and improve your codebase.

    Examples:
        vaahai config init                   # Initialize configuration
        vaahai review run ./my-project       # Review code in a directory
        vaahai audit run ./my-project        # Audit code for security issues
    """
    # Store global options in the context for use in commands
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet

    # Show version and exit if --version flag is used
    if version:
        try:
            import importlib.metadata

            version_str = importlib.metadata.version("vaahai")
        except importlib.metadata.PackageNotFoundError:
            version_str = "unknown (development mode)"
        console.print(f"VaahAI version: [bold green]{version_str}[/bold green]")
        raise typer.Exit()

    # Handle conflicting options
    if verbose and quiet:
        print_error("Cannot use both --verbose and --quiet options together")
        raise typer.Exit(code=1)

    # Handle custom config file
    if config_file:
        config_path = Path(config_file)
        if not config_path.exists():
            print_error(f"Config file not found: {config_path}")
            raise typer.Exit(code=1)
        ctx.obj["config_file"] = config_path
        if verbose:
            print_info(f"Using custom config file: {config_path}")

    # Show help if no command is provided
    if ctx.invoked_subcommand is None:
        ctx.obj["help"] = True
        raise typer.Exit()


def main():
    """
    Main entry point function that wraps the Typer app with error handling.
    """
    try:
        app()
    except KeyboardInterrupt:
        print_error("\nOperation cancelled by user")
        sys.exit(130)  # Standard exit code for SIGINT
    except Exception as e:
        print_error(f"An unexpected error occurred: {str(e)}")
        if os.environ.get("VAAHAI_DEBUG", "").lower() in ("1", "true", "yes"):
            # Show full traceback in debug mode
            raise
        sys.exit(1)


if __name__ == "__main__":
    main()
