"""
Rich formatting showcase for VaahAI CLI.

This module demonstrates the Rich formatting capabilities of the VaahAI CLI.
It serves as both a test and an example of how to use the console utilities.
"""

import time
from typing import List, Optional

import typer
from rich.table import Table

from vaahai.cli.utils.console import (
    console,
    format_command,
    format_highlight,
    format_key,
    format_path,
    format_status,
    format_url,
    format_value,
    print_code,
    print_columns,
    print_command_result,
    print_command_start,
    print_error,
    print_header,
    print_info,
    print_json,
    print_key_value,
    print_list,
    print_markdown,
    print_panel,
    print_section,
    print_step,
    print_success,
    print_tree,
    print_verbose,
    print_warning,
    progress_spinner,
)
from vaahai.cli.utils.help import CustomHelpCommand, create_typer_app

# Create a Typer instance for the showcase command with custom help formatting
showcase_app = create_typer_app(
    name="showcase",
    help="Demonstrate Rich formatting capabilities",
    add_completion=False,
)


@showcase_app.callback(invoke_without_command=True)
def callback(ctx: typer.Context):
    """Demonstrate Rich formatting capabilities."""
    if ctx.invoked_subcommand is None:
        run_showcase()


@showcase_app.command("basic", cls=CustomHelpCommand)
def basic_formatting():
    """Demonstrate basic Rich formatting."""
    showcase_basic()


@showcase_app.command("advanced", cls=CustomHelpCommand)
def advanced_formatting():
    """Demonstrate advanced Rich formatting."""
    showcase_advanced()


@showcase_app.command("all", cls=CustomHelpCommand)
def all_formatting():
    """Run all Rich formatting showcases."""
    showcase_all()


def run_showcase():
    """Run the Rich formatting showcase."""
    print_header(
        "Rich Formatting Showcase", "Demonstrating console output capabilities"
    )

    # Show menu of available showcases
    options = [
        "Basic Formatting (headers, messages, panels)",
        "Advanced Formatting (tables, trees, code blocks)",
        "All Formatting Examples",
    ]

    for i, option in enumerate(options, 1):
        print_info(f"{i}. {option}")

    choice = ""
    while choice not in ["1", "2", "3"]:
        choice = input("\nSelect an option (1-3): ")

    if choice == "1":
        showcase_basic()
    elif choice == "2":
        showcase_advanced()
    elif choice == "3":
        showcase_all()


def showcase_basic():
    """Demonstrate basic Rich formatting."""
    print_section("Basic Message Types")

    print_success("This is a success message")
    print_error("This is an error message")
    print_warning("This is a warning message")
    print_info("This is an info message")
    print_verbose("This is a verbose message (only shown in verbose mode)")

    print_section("Panels")

    print_panel(
        "Panels are useful for highlighting important information",
        title="Panel Example",
        expand=False,
    )

    print_section("Formatting Helpers")

    print(f"You can {format_highlight('highlight')} important text")
    print(f"Format paths like {format_path('/path/to/file.txt')}")
    print(f"Format commands like {format_command('vaahai helloworld')}")
    print(f"Format URLs like {format_url('https://example.com')}")
    print(f"Format key-value pairs like {format_key('name')}: {format_value('value')}")
    print(f"Format status like {format_status('success', 'green')}")

    print_success("Basic formatting showcase completed!")


def showcase_advanced():
    """Demonstrate advanced Rich formatting."""
    print_section("Key-Value Pairs")

    print_key_value("Name", "VaahAI")
    print_key_value("Version", "0.2.17")
    print_key_value(
        "Description", "A multi AI agent CLI tool using Microsoft Autogen Framework"
    )

    print_section("Lists")

    print_list(
        ["Item 1", "Item 2", "Item 3"],
        title="Simple List",
    )

    print_section("Trees")

    tree_data = {
        "vaahai": {
            "cli": {
                "commands": {
                    "core": {},
                    "dev": {},
                    "project": {},
                },
                "utils": {
                    "console.py": None,
                    "prompts.py": None,
                },
            },
            "agents": {
                "impl": {},
                "factory.py": None,
            },
        }
    }
    print_tree(tree_data, title="Project Structure")

    print_section("Tables")

    table = Table(title="Command Groups")
    table.add_column("Name", style="cyan")
    table.add_column("Description", style="green")
    table.add_column("Status", style="magenta")

    table.add_row("core", "Core commands for VaahAI", "Implemented")
    table.add_row("project", "Project management commands", "In Progress")
    table.add_row("dev", "Development and testing commands", "Implemented")

    console.print(table)

    print_section("Columns")

    print_columns(
        ["Column 1", "Column 2", "Column 3"],
        ["Value 1", "Value 2", "Value 3"],
        ["Another 1", "Another 2", "Another 3"],
    )

    print_section("JSON")

    json_data = {
        "name": "VaahAI",
        "version": "0.2.17",
        "commands": ["core", "project", "dev"],
        "features": {
            "rich_integration": True,
            "inquirerpy_integration": True,
        },
    }
    print_json(json_data)

    print_section("Code Blocks")

    print_code(
        'def hello_world():\n    print("Hello, World!")\n\nhello_world()',
        language="python",
        title="Python Example",
    )

    print_section("Markdown")

    markdown = """
# Markdown Example

This is a **bold** text and this is an *italic* text.

## Lists

- Item 1
- Item 2
- Item 3

## Code

```python
def example():
    return "Hello, Markdown!"
```
"""
    print_markdown(markdown)

    print_success("Advanced formatting showcase completed!")


def showcase_command_execution():
    """Demonstrate command execution formatting."""
    print_section("Command Execution")

    print_command_start("ls -la")
    time.sleep(1)  # Simulate command execution
    print_command_result("total 40\ndrwxr-xr-x  5 user  staff  160 Jun  6 12:00 .\n...")

    print_step("Step 1", "Initialize project")
    time.sleep(1)  # Simulate step execution
    print_success("Project initialized")

    print_step("Step 2", "Install dependencies")
    time.sleep(1)  # Simulate step execution
    print_success("Dependencies installed")

    with progress_spinner("Processing files"):
        time.sleep(2)  # Simulate long-running process

    print_success("Command execution showcase completed!")


def showcase_all():
    """Run all Rich formatting showcases."""
    showcase_basic()
    showcase_advanced()
    showcase_command_execution()

    print_section("Summary")
    print_success("All formatting showcases completed!")
    print_info(
        "These formatting utilities can be used throughout the VaahAI CLI for consistent and visually appealing output."
    )


if __name__ == "__main__":
    showcase_app()
