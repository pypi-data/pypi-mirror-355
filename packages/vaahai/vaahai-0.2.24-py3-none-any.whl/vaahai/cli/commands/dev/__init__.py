"""
Development and testing commands for VaahAI CLI.

This module contains commands for development and testing purposes.
"""

import typer

from vaahai.cli.commands.dev.prompts import prompts_app
from vaahai.cli.commands.dev.showcase import showcase_app
from vaahai.cli.commands.helloworld.command import helloworld_app
from vaahai.cli.utils.help import create_typer_app

# Create a Typer instance for the dev command group with custom help formatting
dev_app = create_typer_app(
    name="dev",
    help="Development and testing commands",
    add_completion=True,
    no_args_is_help=True,
)

# Register subcommands
dev_app.add_typer(helloworld_app, name="helloworld")
dev_app.add_typer(showcase_app, name="showcase")
dev_app.add_typer(prompts_app, name="prompts")
