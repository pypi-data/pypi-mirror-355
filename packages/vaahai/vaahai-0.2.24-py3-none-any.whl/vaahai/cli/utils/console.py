"""
Console output utilities for VaahAI CLI.

This module provides utility functions for consistent console output formatting
using Rich library across all CLI commands.
"""

from contextlib import contextmanager
from typing import Any, Dict, Generator, List, Optional, Union

from rich import print
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

# Create a shared console instance for consistent styling
console = Console()
# Create an error console that outputs to stderr
error_console = Console(stderr=True, style="bold red")


def print_header(title: str, subtitle: Optional[str] = None) -> None:
    """
    Print a formatted header with optional subtitle.

    Args:
        title: The main title text
        subtitle: Optional subtitle text
    """
    console.print(f"[bold blue]{title}[/bold blue]")
    if subtitle:
        console.print(f"[dim]{subtitle}[/dim]")
    console.print("")


def print_success(message: str) -> None:
    """
    Print a success message.

    Args:
        message: The success message to print
    """
    console.print(f"[bold green]✓ {message}[/bold green]")


def print_error(message: str) -> None:
    """
    Print an error message.

    Args:
        message: The error message to print
    """
    console.print(f"[bold red]✗ {message}[/bold red]")


def print_warning(message: str) -> None:
    """
    Print a warning message.

    Args:
        message: The warning message to print
    """
    console.print(f"[bold yellow]⚠ {message}[/bold yellow]")


def print_info(message: str) -> None:
    """
    Print an info message.

    Args:
        message: The info message to print
    """
    console.print(f"[bold cyan]ℹ {message}[/bold cyan]")


def print_verbose(message: str) -> None:
    """
    Print a verbose message, only if verbose mode is active.
    (Note: Actual verbose check needs to be handled by the calling command
    based on CLI flags, this function just provides the formatting).

    Args:
        message: The verbose message to print.
    """
    # In a real scenario, you'd check a global verbose flag here.
    # For now, we'll assume it's controlled by the caller.
    console.print(f"[dim]VERBOSE: {message}[/dim]")


def print_section(title: str) -> None:
    """
    Print a section header.

    Args:
        title: The title of the section.
    """
    console.print(f"\n[bold magenta]--- {title} ---[/bold magenta]\n")


def print_panel(
    content: str,
    title: Optional[str] = None,
    style: str = "blue",
    expand: bool = True,
) -> None:
    """
    Print content in a panel with optional title.

    Args:
        content: The content to display in the panel
        title: Optional title for the panel
        style: Color style for the panel border
        expand: Whether to expand the panel to fill the terminal width
    """
    panel = Panel(
        content,
        title=title,
        border_style=style,
        expand=expand,
    )
    console.print(panel)


def print_code(
    code: str,
    language: str = "python",
    line_numbers: bool = True,
    title: Optional[str] = None,
) -> None:
    """
    Print formatted code with syntax highlighting.

    Args:
        code: The code to print
        language: The programming language for syntax highlighting
        line_numbers: Whether to show line numbers
        title: Optional title for the code block
    """
    syntax = Syntax(
        code,
        language,
        line_numbers=line_numbers,
        theme="monokai",
    )
    if title:
        console.print(f"[bold]{title}[/bold]")
    console.print(syntax)


def print_markdown(markdown_text: str) -> None:
    """
    Print formatted markdown text.

    Args:
        markdown_text: The markdown text to print
    """
    md = Markdown(markdown_text)
    console.print(md)


def print_key_value(
    key: str, value: Any, key_style: str = "bold cyan", value_style: str = "white"
) -> None:
    """
    Print a key-value pair.

    Args:
        key: The key to print.
        value: The value to print.
        key_style: The Rich style for the key.
        value_style: The Rich style for the value.
    """
    console.print(
        f"[{key_style}]{key}:[/{key_style}] [{value_style}]{value}[/{value_style}]"
    )


def print_list(
    items: List[Any], title: Optional[str] = None, style: str = "* "
) -> None:
    """
    Print a list of items with optional title.

    Args:
        items: A list of items to print.
        title: Optional title for the list.
        style: The style prefix for each list item.
    """
    if title:
        console.print(f"[bold]{title}[/bold]")
    for item in items:
        console.print(f"{style}{item}")
    console.print()  # Add a blank line after the list


def print_tree(data: Dict[str, Any], title: Optional[str] = None) -> None:
    """
    Print a dictionary as a tree structure.

    Args:
        data: The dictionary to print as a tree.
        title: Optional title for the tree.
    """
    from rich.tree import Tree

    if title:
        console.print(f"[bold]{title}[/bold]")

    def add_nodes(tree_node: Tree, dictionary_item: Dict[str, Any]):
        for key, value in dictionary_item.items():
            if isinstance(value, dict):
                branch = tree_node.add(f"[bold blue]{key}[/bold blue]")
                add_nodes(branch, value)
            else:
                tree_node.add(f"[cyan]{key}[/cyan]: {value}")

    root_key = list(data.keys())[0]  # Assuming single root for simplicity here
    tree = Tree(f"[bold green]{root_key}[/bold green]")
    add_nodes(tree, data[root_key])
    console.print(tree)
    console.print()


def print_columns(*columns_data: List[Any], title: Optional[str] = None) -> None:
    """
    Print data in a columnar layout.

    Args:
        *columns_data: A variable number of lists, where each list represents a column.
                       All lists should have the same length.
        title: Optional title for the columns.
    """
    if not columns_data:
        return

    if title:
        console.print(f"[bold]{title}[/bold]")

    # Use Rich Table with grid for a simple column layout
    table = Table.grid(expand=True)
    num_cols = len(columns_data)
    for _ in range(num_cols):
        table.add_column()

    # Ensure all columns have the same number of rows
    num_rows = len(columns_data[0])
    for col_data in columns_data:
        if len(col_data) != num_rows:
            print_error(
                "All columns must have the same number of rows for print_columns."
            )
            return

    for i in range(num_rows):
        row_data = [str(columns_data[j][i]) for j in range(num_cols)]
        table.add_row(*row_data)

    console.print(table)
    console.print()


def print_json(data: Any, title: Optional[str] = None) -> None:
    """
    Print data as formatted JSON.

    Args:
        data: The data to print as JSON (should be JSON serializable).
        title: Optional title for the JSON output.
    """
    import json

    from rich.syntax import Syntax

    if title:
        console.print(f"[bold]{title}[/bold]")

    try:
        json_string = json.dumps(data, indent=4)
        syntax = Syntax(json_string, "json", theme="monokai", line_numbers=True)
        console.print(syntax)
    except TypeError as e:
        print_error(f"Could not serialize data to JSON: {e}")
        console.print(str(data))  # Print raw data if serialization fails
    console.print()


def print_command_start(command: str) -> None:
    """
    Print a message indicating the start of a command execution.

    Args:
        command: The command string that is being executed.
    """
    console.print(f"[bold blue]❯ Executing: {command}[/bold blue]")


def print_command_result(output: str, error: bool = False) -> None:
    """
    Print the result of a command execution.

    Args:
        output: The output string from the command.
        error: Whether the command resulted in an error.
    """
    if error:
        console.print(f"[red]{output}[/red]")
    else:
        console.print(output)
    console.print()  # Add a blank line after the result


def print_step(step_number: Union[int, str], description: str) -> None:
    """
    Print a formatted step in a process.

    Args:
        step_number: The number or identifier of the step.
        description: A description of the step.
    """
    console.print(f"[bold yellow]Step {step_number}:[/bold yellow] {description}")


def format_highlight(text: str) -> str:
    """
    Format text to be highlighted.

    Args:
        text: The text to highlight.

    Returns:
        The highlighted text string (Rich markup).
    """
    return f"[bold magenta]{text}[/bold magenta]"


def format_path(path: str) -> str:
    """
    Format a filesystem path for styled terminal output.

    Args:
        path: The filesystem path to format.

    Returns:
        The formatted path string (Rich markup).
    """
    return f"[cyan]{path}[/cyan]"


def format_command(command: str) -> str:
    """
    Format a command string for styled terminal output.

    Args:
        command: The command to format.

    Returns:
        The formatted command string (Rich markup).
    """
    return f"[green]{command}[/green]"


def format_url(url: str) -> str:
    """
    Format a URL for styled terminal output.

    Args:
        url: The URL to format.

    Returns:
        The formatted URL string (Rich markup).
    """
    return f"[blue underline]{url}[/blue underline]"


def format_key(key: str) -> str:
    """
    Format a key (as in key-value pair) for styled terminal output.

    Args:
        key: The key to format.

    Returns:
        The formatted key string (Rich markup).
    """
    return f"[bold cyan]{key}[/bold cyan]"


def format_value(value: Any) -> str:
    """
    Format a value (as in key-value pair) for styled terminal output.

    Args:
        value: The value to format.

    Returns:
        The formatted value string (Rich markup).
    """
    return f"[yellow]{value}[/yellow]"


def format_status(status: str, success: bool = True) -> str:
    """
    Format a status string for styled terminal output.

    Args:
        status: The status text to format.
        success: Whether the status indicates success (True) or failure (False).

    Returns:
        The formatted status string (Rich markup).
    """
    if success:
        return f"[bold green]{status}[/bold green]"
    else:
        return f"[bold red]{status}[/bold red]"


@contextmanager
def progress_spinner(
    message: str, success_message: Optional[str] = None
) -> Generator[None, None, None]:
    """
    A context manager that displays a spinner while a task is in progress.

    Args:
        message: The message to display while the spinner is active.
        success_message: Optional message to display upon successful completion.
                         If None, the original message with "Done" appended will be shown.

    Usage:
        ```python
        with progress_spinner("Downloading file..."):
            # Do some work
            download_file()
        # Spinner stops automatically with a success message
        ```
    """
    with console.status(f"[bold blue]{message}[/bold blue]", spinner="dots") as status:
        try:
            yield
            if success_message:
                console.print(f"[bold green]✓[/bold green] {success_message}")
            else:
                console.print(f"[bold green]✓[/bold green] {message} Done")
        except Exception as e:
            console.print(f"[bold red]✗[/bold red] {message} Failed: {str(e)}")
            raise


def create_table(
    columns: List[str],
    rows: List[List[Any]],
    title: Optional[str] = None,
) -> Table:
    """
    Create a formatted table.

    Args:
        columns: List of column headers
        rows: List of rows, each containing values for each column
        title: Optional title for the table

    Returns:
        A Rich Table object that can be printed with console.print()
    """
    table = Table(title=title)

    # Add columns
    for column in columns:
        table.add_column(column)

    # Add rows
    for row in rows:
        table.add_row(*[str(cell) for cell in row])

    return table
