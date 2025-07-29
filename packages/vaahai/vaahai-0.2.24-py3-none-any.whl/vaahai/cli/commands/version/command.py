"""
VaahAI version command implementation.

This module contains the implementation of the version command,
which displays the current version of VaahAI.
"""

import importlib.metadata

import typer

from vaahai.cli.utils.console import console, print_panel
from vaahai.cli.utils.help import CustomHelpCommand, create_typer_app

# Create the version command group with custom help formatting
version_app = create_typer_app(
    name="version",
    help="Display VaahAI version information",
    add_completion=False,
)


@version_app.callback()
def callback():
    """
    Display VaahAI version information.
    """
    pass


@version_app.command("show", cls=CustomHelpCommand)
def show():
    """
    Show the current version of VaahAI.
    """
    try:
        version = importlib.metadata.version("vaahai")
    except importlib.metadata.PackageNotFoundError:
        version = "unknown (development mode)"

    print_panel(
        f"VaahAI version: [bold green]{version}[/bold green]",
        title="Version Information",
        style="blue",
    )
