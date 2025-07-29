"""
InquirerPy prompt showcase for VaahAI CLI.

This module demonstrates the InquirerPy prompt capabilities of the VaahAI CLI.
It serves as both a test and an example of how to use the prompt utilities.
"""

from pathlib import Path
from typing import List, Optional

import typer

from vaahai.cli.utils.console import (
    format_highlight,
    print_code,
    print_error,
    print_header,
    print_info,
    print_key_value,
    print_section,
    print_success,
)
from vaahai.cli.utils.help import CustomHelpCommand, create_typer_app
from vaahai.cli.utils.prompts import (
    confirm_prompt,
    create_choice,
    editor_prompt,
    fuzzy_prompt,
    multiselect_prompt,
    number_prompt,
    password_prompt,
    path_prompt,
    select_prompt,
    text_prompt,
)

# Create a Typer instance for the prompt showcase command with custom help formatting
prompts_app = create_typer_app(
    name="prompts",
    help="Demonstrate InquirerPy prompt capabilities",
    add_completion=False,
)


@prompts_app.callback(invoke_without_command=True)
def callback(ctx: typer.Context):
    """Demonstrate InquirerPy prompt capabilities."""
    if ctx.invoked_subcommand is None:
        run_showcase()


@prompts_app.command("all", cls=CustomHelpCommand)
def all_prompts():
    """Run all prompt showcase examples."""
    showcase_all()


@prompts_app.command("basic", cls=CustomHelpCommand)
def basic_prompts():
    """Demonstrate basic prompt types."""
    showcase_basic()


@prompts_app.command("selection", cls=CustomHelpCommand)
def selection_prompts():
    """Demonstrate selection prompt types."""
    showcase_selection()


@prompts_app.command("advanced", cls=CustomHelpCommand)
def advanced_prompts():
    """Demonstrate advanced prompt types."""
    showcase_advanced()


def run_showcase():
    """Run the InquirerPy prompt showcase."""
    print_header("InquirerPy Prompt Showcase")
    print_info("Demonstrating interactive prompt capabilities")
    print("")

    try:
        # Check if we're in an interactive terminal
        import sys

        if not sys.stdin.isatty():
            print_info("This showcase requires an interactive terminal.")
            print_info("Please run this command in a regular terminal session.")
            return

        # Let the user choose which showcase to run
        showcase_type = select_prompt(
            message="Select a showcase type:",
            choices=[
                "Basic Prompts",
                "Selection Prompts",
                "Advanced Prompts",
                "All Prompts",
            ],
            instruction="Choose the type of prompts to showcase",
        )

        if showcase_type == "Basic Prompts":
            showcase_basic()
        elif showcase_type == "Selection Prompts":
            showcase_selection()
        elif showcase_type == "Advanced Prompts":
            showcase_advanced()
        else:
            showcase_all()

        print_success("Prompt showcase completed successfully!")
    except Exception as e:
        print_error(f"Error running prompt showcase: {str(e)}")
        print_info("This showcase requires an interactive terminal.")
        print_info("Please run this command in a regular terminal session.")


def showcase_basic():
    """Demonstrate basic prompt types."""
    print_section("Basic Prompt Types")

    # Text prompt
    name = text_prompt(
        message="What's your name?",
        default="User",
        validate=True,
        instruction="Enter your name (cannot be empty)",
    )
    print_key_value("Name", name)

    # Password prompt
    password = password_prompt(
        message="Enter a password:",
        validate=True,
        instruction="Password will not be displayed as you type",
    )
    print_key_value("Password length", str(len(password)))

    # Confirm prompt
    confirmed = confirm_prompt(
        message="Do you like interactive prompts?",
        default=True,
        instruction="Press Y for Yes or N for No",
    )
    print_key_value("Your response", "Yes" if confirmed else "No")

    print_success("Basic prompt showcase completed!")


def showcase_selection():
    """Demonstrate selection prompt types."""
    print_section("Selection Prompt Types")

    # Select prompt
    language = select_prompt(
        message="Select your favorite programming language:",
        choices=["Python", "JavaScript", "Rust", "Go", "Java"],
        default="Python",
        instruction="Use arrow keys to navigate and Enter to select",
    )
    print_key_value("Selected language", language)

    # Multiselect prompt
    frameworks = multiselect_prompt(
        message="Select frameworks you're familiar with:",
        choices=["Django", "Flask", "FastAPI", "React", "Vue", "Angular"],
        default=["FastAPI"],
        min_selections=1,
        instruction="Use space to select, enter to confirm (min: 1)",
    )
    print_key_value("Selected frameworks", ", ".join(frameworks))

    # Advanced selection with Choice objects
    cloud_choices = [
        create_choice("AWS", "aws"),
        create_choice("Google Cloud", "gcp"),
        create_choice("Azure", "azure"),
        create_choice("Oracle Cloud", "oracle"),
        create_choice("DigitalOcean", "do"),
    ]
    cloud = select_prompt(
        message="Select a cloud provider:",
        choices=cloud_choices,
        instruction="Disabled options cannot be selected",
    )
    print_key_value("Selected cloud", cloud)

    # Fuzzy prompt
    tool = fuzzy_prompt(
        message="Search for a development tool:",
        choices=[
            "VS Code",
            "PyCharm",
            "IntelliJ IDEA",
            "Sublime Text",
            "Vim",
            "Emacs",
            "Atom",
            "WebStorm",
            "Eclipse",
            "Xcode",
        ],
        instruction="Type to search",
    )
    print_key_value("Selected tool", tool)

    print_success("Selection prompt showcase completed!")


def showcase_advanced():
    """Demonstrate advanced prompt types."""
    print_section("Advanced Prompt Types")

    # Number prompt
    age = number_prompt(
        message="Enter your age:",
        min_allowed=0,
        max_allowed=120,
        default=30,
        instruction="Must be between 0 and 120",
    )
    print_key_value("Age", str(age))

    # Path prompt
    try:
        file_path = path_prompt(
            message="Select a file:",
            default=str(Path.home()),
            only_files=True,
            instruction="Must be an existing file",
        )
        print_key_value("Selected file", file_path)
    except KeyboardInterrupt:
        print_info("Path selection canceled")

    # Editor prompt
    if confirm_prompt("Would you like to try the editor prompt?", default=False):
        try:
            notes = editor_prompt(
                message="Enter some notes:",
                default="# My Notes\n\nEnter your notes here...",
                file_extension=".md",
                instruction="Your default editor will open",
            )
            print_code(
                notes[:100] + "..." if len(notes) > 100 else notes, language="markdown"
            )
        except Exception as e:
            print_info(f"Editor prompt not available: {str(e)}")

    print_success("Advanced prompt showcase completed!")


def showcase_all():
    """Run all prompt showcase examples."""
    showcase_basic()
    showcase_selection()
    showcase_advanced()

    print_section("Summary")
    print_success("All prompt showcases completed!")
    print_info(
        f"These prompt utilities can be used throughout the VaahAI CLI to create interactive and user-friendly experiences."
    )
    print_info(
        f"Check out the {format_highlight('vaahai.cli.utils.prompts')} module for more details."
    )


if __name__ == "__main__":
    prompts_app()
