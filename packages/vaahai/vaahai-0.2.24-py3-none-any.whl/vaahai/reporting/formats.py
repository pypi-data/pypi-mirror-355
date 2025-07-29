"""OutputFormat enum for selecting report format."""
from enum import Enum

class OutputFormat(str, Enum):
    """Supported output formats for review reports."""

    RICH = "rich"  # default CLI output using Rich
    MARKDOWN = "markdown"
    HTML = "html"
    INTERACTIVE = "interactive"

    @classmethod
    def list(cls):
        """Return list of all values (for Typer choices)."""
        return [f.value for f in cls]
