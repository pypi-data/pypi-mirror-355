"""
Interactive prompt utilities for VaahAI CLI.

This module provides utility functions for creating consistent interactive
prompts using InquirerPy across all CLI commands.
"""

from typing import Any, Callable, Dict, List, Optional, Union

from InquirerPy import inquirer
from InquirerPy.base.control import Choice
from InquirerPy.validator import EmptyInputValidator, NumberValidator, PathValidator


def text_prompt(
    message: str,
    default: Optional[str] = None,
    validate: bool = False,
    transformer: Optional[Callable[[str], str]] = None,
    instruction: Optional[str] = None,
) -> str:
    """
    Display a text input prompt.

    Args:
        message: The prompt message to display
        default: Optional default value
        validate: Whether to validate that input is not empty
        transformer: Optional function to transform the input
        instruction: Optional help text shown below the prompt

    Returns:
        The user's input as a string
    """
    validator = EmptyInputValidator() if validate else None
    return inquirer.text(
        message=message,
        default=default,
        validate=validator,
        transformer=transformer,
        instruction=instruction,
    ).execute()


def password_prompt(
    message: str,
    validate: bool = False,
    instruction: Optional[str] = None,
) -> str:
    """
    Display a password input prompt (input is masked).

    Args:
        message: The prompt message to display
        validate: Whether to validate that input is not empty
        instruction: Optional help text shown below the prompt

    Returns:
        The user's input as a string
    """
    validator = EmptyInputValidator() if validate else None
    return inquirer.secret(
        message=message,
        validate=validator,
        instruction=instruction,
    ).execute()


def confirm_prompt(
    message: str,
    default: bool = False,
    instruction: Optional[str] = None,
) -> bool:
    """
    Display a yes/no confirmation prompt.

    Args:
        message: The prompt message to display
        default: Default value (True for Yes, False for No)
        instruction: Optional help text shown below the prompt

    Returns:
        Boolean representing the user's choice
    """
    return inquirer.confirm(
        message=message,
        default=default,
        instruction=instruction,
    ).execute()


def select_prompt(
    message: str,
    choices: List[Union[str, Choice]],
    default: Optional[str] = None,
    instruction: Optional[str] = None,
) -> str:
    """
    Display a selection prompt with a list of choices.

    Args:
        message: The prompt message to display
        choices: List of choices (strings or Choice objects)
        default: Optional default choice
        instruction: Optional help text shown below the prompt

    Returns:
        The selected choice
    """
    return inquirer.select(
        message=message,
        choices=choices,
        default=default,
        instruction=instruction,
    ).execute()


def multiselect_prompt(
    message: str,
    choices: List[Union[str, Choice]],
    min_selections: int = 0,
    max_selections: Optional[int] = None,
    default: Optional[List[str]] = None,
    instruction: Optional[str] = None,
) -> List[str]:
    """
    Display a multi-selection prompt allowing multiple choices.

    Args:
        message: The prompt message to display
        choices: List of choices (strings or Choice objects)
        min_selections: Minimum number of selections required
        max_selections: Maximum number of selections allowed
        default: Optional list of default selected choices
        instruction: Optional help text shown below the prompt

    Returns:
        List of selected choices
    """
    return inquirer.checkbox(
        message=message,
        choices=choices,
        min_selections=min_selections,
        max_selections=max_selections,
        default=default,
        instruction=instruction,
    ).execute()


def path_prompt(
    message: str,
    default: Optional[str] = None,
    only_directories: bool = False,
    only_files: bool = False,
    instruction: Optional[str] = None,
) -> str:
    """
    Display a prompt for file or directory path input with validation.

    Args:
        message: The prompt message to display
        default: Optional default path
        only_directories: Whether to only accept directories
        only_files: Whether to only accept files
        instruction: Optional help text shown below the prompt

    Returns:
        The validated path as a string
    """
    validator = PathValidator(
        is_dir=only_directories,
        is_file=only_files,
    )
    return inquirer.filepath(
        message=message,
        default=default,
        validate=validator,
        instruction=instruction,
    ).execute()


def editor_prompt(
    message: str,
    default: str = "",
    file_extension: str = ".txt",
    instruction: Optional[str] = None,
) -> str:
    """
    Open an editor for multi-line text input.

    Args:
        message: The prompt message to display
        default: Optional default text
        file_extension: File extension for syntax highlighting
        instruction: Optional help text shown below the prompt

    Returns:
        The text entered in the editor
    """
    return inquirer.editor(
        message=message,
        default=default,
        file_extension=file_extension,
        instruction=instruction,
    ).execute()


def fuzzy_prompt(
    message: str,
    choices: List[Union[str, Choice]],
    default: Optional[str] = None,
    instruction: Optional[str] = None,
) -> str:
    """
    Display a fuzzy search prompt for selecting from a large list of choices.

    Args:
        message: The prompt message to display
        choices: List of choices (strings or Choice objects)
        default: Optional default choice
        instruction: Optional help text shown below the prompt

    Returns:
        The selected choice
    """
    return inquirer.fuzzy(
        message=message,
        choices=choices,
        default=default,
        instruction=instruction,
    ).execute()


def number_prompt(
    message: str,
    default: Optional[int] = None,
    min_allowed: Optional[int] = None,
    max_allowed: Optional[int] = None,
    instruction: Optional[str] = None,
) -> int:
    """
    Display a numeric input prompt with optional range validation.

    Args:
        message: The prompt message to display
        default: Optional default value
        min_allowed: Optional minimum allowed value
        max_allowed: Optional maximum allowed value
        instruction: Optional help text shown below the prompt

    Returns:
        The entered number as an integer
    """
    validator = None
    if min_allowed is not None or max_allowed is not None:
        validator = NumberValidator(
            min_allowed=min_allowed,
            max_allowed=max_allowed,
        )

    return inquirer.number(
        message=message,
        default=default,
        validate=validator,
        instruction=instruction,
    ).execute()


def create_choice(
    name: str,
    value: Any = None,
    enabled: bool = False,
) -> Choice:
    """
    Create a Choice object for use in selection prompts.

    Args:
        name: Display name of the choice
        value: Value to return when selected (defaults to name if None)
        enabled: Whether the choice is pre-selected in checkbox prompts

    Returns:
        A Choice object
    """
    # Note: disabled parameter is not used as it's not supported in InquirerPy 0.3.4
    return Choice(
        name=name,
        value=value if value is not None else name,
        enabled=enabled,
    )
