"""
Core command group for VaahAI CLI.

This module contains essential commands for VaahAI operation including
configuration management and version information.
"""

import typer

from vaahai.cli.commands.config.command import config_app
from vaahai.cli.commands.version.command import version_app
from vaahai.cli.utils.help import create_typer_app

# Create the core commands group with custom help formatting
core_app = create_typer_app(
    name="core",
    help="Essential VaahAI commands",
    add_completion=True,
    no_args_is_help=True,
)

# Add commands to the core group
core_app.add_typer(config_app, name="config")
core_app.add_typer(version_app, name="version")
