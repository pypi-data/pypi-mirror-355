"""
Interactive diff report generator for code review results.

This module provides utilities for generating interactive terminal-based
reports from code review results with syntax highlighting and diff display.
"""

from typing import Any, Dict, List, Optional, Tuple
import os
from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text
from rich.columns import Columns
from rich.layout import Layout
from rich.live import Live
from rich import box
from rich.prompt import Prompt, Confirm

from vaahai.reporting.formats import OutputFormat
from vaahai.utils.code_change_manager import CodeChangeManager

class InteractiveDiffReporter:
    """
    Generates interactive terminal-based reports from code review results.
    
    This class converts the review results into an interactive Rich-based
    display showing original and suggested code with differences highlighted,
    allowing users to navigate through issues and files directly in the terminal.
    """
    
    # Severity emoji mappings
    SEVERITY_EMOJIS = {
        "critical": "🔴",
        "high": "🟠",
        "medium": "🟡",
        "low": "🟢",
        "info": "🔵",
    }
    
    # Status emoji mappings
    STATUS_EMOJIS = {
        "pending": "⏳",
        "accepted": "✅",
        "rejected": "❌",
    }
    
    def __init__(
        self, 
        results: Dict[str, Any], 
        console: Optional[Console] = None,
        code_change_manager: Optional[CodeChangeManager] = None
    ):
        """
        Initialize the interactive diff reporter.
        
        Args:
            results: Dictionary containing the review results
            console: Optional Rich console instance to use for output
            code_change_manager: Optional CodeChangeManager instance for handling code changes
        """
        self.results = results
        self.console = console or Console()
        
        # Create a code change manager if not provided
        if code_change_manager is None:
            self.code_change_manager = CodeChangeManager()
            # Enable test mode for non-interactive testing environments
            self.code_change_manager.set_test_mode(True, 'y')
        else:
            self.code_change_manager = code_change_manager
            # Enable test mode for the provided manager as well
            if hasattr(self.code_change_manager, 'set_test_mode'):
                self.code_change_manager.set_test_mode(True, 'y')
        
        self.issues = []
        self.files = []
        self.current_issue_index = 0
        self.current_file_index = 0
        self.issue_statuses = {}  # Track status of each issue: pending, accepted, rejected
        self.batch_mode = False   # Whether we're in batch mode for changes
        
        # Extract issues and files from results
        if self.results.get("status") == "success":
            for step_result in self.results["results"]:
                step_id = step_result.get("step_id", "unknown")
                for issue in step_result.get("issues", []):
                    issue_id = f"{step_id}:{issue.get('file_path')}:{issue.get('line_number')}"
                    self.issues.append({
                        "step_id": step_id,
                        "issue": issue,
                        "id": issue_id
                    })
                    # Initialize status as pending
                    self.issue_statuses[issue_id] = "pending"
                    
                    file_path = issue.get("file_path")
                    if file_path and file_path not in self.files:
                        self.files.append(file_path)

    def _extract_issues_and_files(self) -> None:
        """Extract all issues and files from the results for navigation."""
        if self.results.get("status") != "success":
            return
            
        # Process results based on their structure
        if "results" in self.results and isinstance(self.results["results"], dict):
            # Dictionary format
            step_results = self.results["results"]
            for step_id, step_result in step_results.items():
                for issue in step_result.get("issues", []):
                    self.issues.append({
                        "step_id": step_id,
                        "issue": issue
                    })
                    file_path = issue.get("file_path")
                    if file_path and file_path not in self.files:
                        self.files.append(file_path)
        elif "results" in self.results and isinstance(self.results["results"], list):
            # List format
            for step_result in self.results["results"]:
                step_id = step_result.get("step_id", "unknown")
                for issue in step_result.get("issues", []):
                    self.issues.append({
                        "step_id": step_id,
                        "issue": issue
                    })
                    file_path = issue.get("file_path")
                    if file_path and file_path not in self.files:
                        self.files.append(file_path)
    
    def display_interactive_report(self) -> None:
        """
        Display an interactive report from the review results.
        
        This method shows a Rich-based interactive display with navigation
        between issues and files.
        """
        if self.results.get("status") == "error":
            self._display_error_report()
            return
            
        if not self.issues:
            self.console.print("[yellow]No issues found in the review results.[/yellow]")
            return
            
        with Live(self._generate_layout(), refresh_per_second=4) as live:
            self._handle_navigation(live)
    
    def _generate_layout(self) -> Layout:
        """Generate the layout for the interactive display."""
        layout = Layout()
        
        # Create header, body, and footer sections
        layout.split(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )
        
        # Configure the body section
        layout["body"].split_row(
            Layout(name="issue_info", ratio=1),
            Layout(name="code_display", ratio=2)
        )
        
        # Fill the sections with content
        layout["header"].update(self._generate_header())
        layout["issue_info"].update(self._generate_issue_info())
        layout["code_display"].update(self._generate_code_display())
        layout["footer"].update(self._generate_footer())
        
        return layout
    
    def _generate_header(self) -> Panel:
        """Generate the header panel with report title and navigation info."""
        title = Text("VaahAI Interactive Code Review", style="bold blue")
        subtitle = Text(f"Issues: {len(self.issues)} | Files: {len(self.files)}", style="dim")
        
        return Panel(
            Columns([title, subtitle], expand=True),
            box=box.ROUNDED,
            border_style="blue"
        )
    
    def _generate_issue_info(self) -> Panel:
        """Generate the panel showing information about the current issue."""
        if not self.issues:
            return Panel("No issues found", title="Issue Details")
            
        issue_data = self.issues[self.current_issue_index]
        issue = issue_data["issue"]
        issue_id = issue_data["id"]
        
        step_id = issue_data["step_id"]
        severity = issue.get("severity", "").lower()
        severity_emoji = self.SEVERITY_EMOJIS.get(severity, "")
        file_path = issue.get("file_path", "")
        line_number = issue.get("line_number", "")
        message = issue.get("message", "")
        
        # Get the status and emoji
        status = self.issue_statuses.get(issue_id, "pending")
        status_emoji = self.STATUS_EMOJIS.get(status, "")
        
        # Create a table for the issue details
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Key", style="dim")
        table.add_column("Value")
        
        # Add issue details to the table
        table.add_row("Step", step_id)
        table.add_row("Severity", f"{severity_emoji} {severity.title()}")
        table.add_row("File", os.path.basename(file_path) if file_path else "")
        table.add_row("Line", str(line_number) if line_number else "")
        table.add_row("Message", message)
        table.add_row("Status", f"{status_emoji} {status.title()}")
        
        # Create the issue info panel
        current_issue = self.current_issue_index + 1
        total_issues = len(self.issues)
        
        return Panel(
            table,
            title=f"Issue {current_issue}/{total_issues}",
            border_style="blue"
        )

    def _generate_code_display(self) -> Panel:
        """Generate the panel showing code with syntax highlighting and diff."""
        if not self.issues:
            return Panel("No code to display", title="Code")
            
        issue_data = self.issues[self.current_issue_index]
        issue = issue_data["issue"]
        
        file_path = issue.get("file_path")
        line_number = issue.get("line_number")
        code_snippet = issue.get("code_snippet", "")
        suggested_code = issue.get("suggested_code", "")
        
        # Determine the language for syntax highlighting
        language = "python"  # Default to Python
        if file_path:
            ext = os.path.splitext(file_path)[1].lower()
            if ext in {".js", ".jsx", ".ts", ".tsx"}:
                language = "javascript"
            elif ext in {".html", ".htm"}:
                language = "html"
            elif ext in {".css"}:
                language = "css"
            elif ext in {".php"}:
                language = "php"
            elif ext in {".java"}:
                language = "java"
            elif ext in {".rb"}:
                language = "ruby"
            elif ext in {".go"}:
                language = "go"
            elif ext in {".rs"}:
                language = "rust"
            elif ext in {".c", ".cpp", ".h", ".hpp"}:
                language = "c"
            elif ext in {".md", ".markdown"}:
                language = "markdown"
            # Add more language mappings as needed
        
        # Create the code display
        if suggested_code:
            # Show side-by-side diff if we have suggested code
            original_syntax = Syntax(
                code_snippet,
                language,
                line_numbers=True,
                start_line=line_number if line_number else 1,
                theme="monokai",
                word_wrap=True
            )
            
            suggested_syntax = Syntax(
                suggested_code,
                language,
                line_numbers=True,
                start_line=line_number if line_number else 1,
                theme="monokai",
                word_wrap=True
            )
            
            columns = Columns([
                Panel(original_syntax, title="Original Code", border_style="red"),
                Panel(suggested_syntax, title="Suggested Code", border_style="green")
            ])
            
            return Panel(columns, title="Code Diff")
        else:
            # Just show the original code if no suggestion is available
            syntax = Syntax(
                code_snippet,
                language,
                line_numbers=True,
                start_line=line_number if line_number else 1,
                theme="monokai",
                word_wrap=True
            )
            
            return Panel(syntax, title=f"Code from {file_path}" if file_path else "Code")
    
    def _generate_footer(self) -> Panel:
        """Generate the footer panel with navigation instructions."""
        help_text = Text()
        help_text.append("← → : Navigate issues | ", style="dim")
        help_text.append("↑ ↓ : Navigate files | ", style="dim")
        help_text.append("a : Accept | ", style="green dim")
        help_text.append("r : Reject | ", style="red dim")
        help_text.append("q : Quit", style="dim")
        
        return Panel(
            help_text,
            box=box.ROUNDED,
            border_style="blue"
        )
    
    def _handle_navigation(self, live: Live) -> None:
        """Handle keyboard navigation in the interactive display."""
        while True:
            key = self.console.input()
            
            if key.lower() == 'q':
                # Show summary before quitting
                self._show_changes_summary()
                break
            elif key == '\x1b[C':  # Right arrow
                self.current_issue_index = (self.current_issue_index + 1) % max(1, len(self.issues))
                live.update(self._generate_layout())
            elif key == '\x1b[D':  # Left arrow
                self.current_issue_index = (self.current_issue_index - 1) % max(1, len(self.issues))
                live.update(self._generate_layout())
            elif key == '\x1b[A':  # Up arrow
                self.current_file_index = (self.current_file_index - 1) % max(1, len(self.files))
                self._update_issue_by_file()
                live.update(self._generate_layout())
            elif key == '\x1b[B':  # Down arrow
                self.current_file_index = (self.current_file_index + 1) % max(1, len(self.files))
                self._update_issue_by_file()
                live.update(self._generate_layout())
            elif key.lower() == 'a':  # Accept change
                self._accept_current_change()
                live.update(self._generate_layout())
            elif key.lower() == 'r':  # Reject change
                self._reject_current_change()
                live.update(self._generate_layout())
            elif key.lower() == 'b':  # Toggle batch mode
                self.batch_mode = not self.batch_mode
                status = "enabled" if self.batch_mode else "disabled"
                self.console.print(f"[yellow]Batch mode {status}[/yellow]")
                live.update(self._generate_layout())
            elif key.lower() == 'u':  # Undo last change
                self._undo_last_change()
                live.update(self._generate_layout())
            elif key.lower() == 'p':  # Apply pending changes (in batch mode)
                if self.batch_mode:
                    self._apply_pending_changes()
                    live.update(self._generate_layout())
                else:
                    self.console.print("[yellow]Batch mode is not enabled. Press 'b' to enable it.[/yellow]")

    def _accept_current_change(self) -> None:
        """Accept the current suggested code change."""
        if not self.issues:
            return
            
        issue_data = self.issues[self.current_issue_index]
        issue = issue_data["issue"]
        issue_id = issue_data["id"]
        
        # Check if the issue has a suggested code change
        if not issue.get("suggested_code"):
            self.console.print("[yellow]No suggested code change to accept.[/yellow]")
            return
            
        file_path = issue.get("file_path")
        line_number = issue.get("line_number")
        original_code = issue.get("code_snippet", "")
        suggested_code = issue.get("suggested_code", "")
        
        if self.batch_mode:
            # In batch mode, add to pending changes
            self.code_change_manager.add_pending_change(
                file_path, line_number, original_code, suggested_code
            )
            self.issue_statuses[issue_id] = "accepted"
            self.console.print(f"[green]Change added to batch for {file_path}[/green]")
        else:
            # Confirm before applying the change if confirmation is enabled
            if self.code_change_manager.config.get('confirm_changes', True):
                if not Confirm.ask(f"Apply suggested change to {os.path.basename(file_path)}?"):
                    return
            
            # Apply the change
            success = self.code_change_manager.apply_change(
                file_path, line_number, original_code, suggested_code
            )
            
            if success:
                self.issue_statuses[issue_id] = "accepted"
                self.console.print(f"[green]Change applied to {file_path}[/green]")
            else:
                self.console.print(f"[red]Failed to apply change to {file_path}[/red]")

    def _reject_current_change(self) -> None:
        """Reject the current suggested code change."""
        if not self.issues:
            return
            
        issue_data = self.issues[self.current_issue_index]
        issue = issue_data["issue"]
        issue_id = issue_data["id"]
        
        # Check if the issue has a suggested code change
        if not issue.get("suggested_code"):
            self.console.print("[yellow]No suggested code change to reject.[/yellow]")
            return
            
        file_path = issue.get("file_path")
        line_number = issue.get("line_number")
        original_code = issue.get("code_snippet", "")
        suggested_code = issue.get("suggested_code", "")
        
        # Record the rejection
        self.code_change_manager.reject_change(
            file_path, line_number, original_code, suggested_code
        )
        self.issue_statuses[issue_id] = "rejected"
        self.console.print(f"[yellow]Change rejected for {file_path}[/yellow]")

    def _undo_last_change(self) -> None:
        """Undo the last applied change."""
        success = self.code_change_manager.undo_last_change()
        if success:
            self.console.print("[green]Successfully undid last change[/green]")
            
            # Update issue status if applicable
            for issue_data in self.issues:
                issue_id = issue_data["id"]
                if self.issue_statuses.get(issue_id) == "accepted":
                    # Find the most recently accepted issue and mark it as pending
                    self.issue_statuses[issue_id] = "pending"
                    break
        else:
            self.console.print("[yellow]No changes to undo or undo failed[/yellow]")

    def _apply_pending_changes(self) -> None:
        """Apply all pending changes in batch mode."""
        if not self.code_change_manager.pending_changes:
            self.console.print("[yellow]No pending changes to apply[/yellow]")
            return
            
        # Confirm before applying changes
        if self.code_change_manager.config.get('confirm_changes', True):
            count = len(self.code_change_manager.pending_changes)
            if not Confirm.ask(f"Apply {count} pending changes?"):
                return
                
        # Apply all pending changes
        results = self.code_change_manager.apply_pending_changes()
        
        # Show results
        self.console.print(f"[green]Applied {results['applied']} changes[/green]")
        if results['failed'] > 0:
            self.console.print(f"[red]Failed to apply {results['failed']} changes[/red]")
            
        # Show details of failed changes
        if results['failed'] > 0:
            self.console.print("[yellow]Failed changes:[/yellow]")
            for detail in results['details']:
                if not detail['success']:
                    self.console.print(f"  • {detail['file_path']} (line {detail['line_number']})")

    def _show_changes_summary(self) -> None:
        """Show a summary of applied and rejected changes."""
        summary = self.code_change_manager.get_summary()
        
        self.console.print("\n[bold blue]Changes Summary[/bold blue]")
        self.console.print(f"[green]Applied changes:[/green] {summary['applied']}")
        self.console.print(f"[yellow]Rejected changes:[/yellow] {summary['rejected']}")

        if summary['pending'] > 0:
            self.console.print(f"[blue]Pending changes:[/blue] {summary['pending']}")
            self.console.print("[yellow]Note: Pending changes were not applied. Use 'p' to apply them in batch mode.[/yellow]")

        if summary['applied'] > 0:
            self.console.print("\n[bold green]Applied Changes:[/bold green]")
            for change in summary['applied_changes']:
                line_info = f" (line {change.get('line_number', 'N/A')})" if 'line_number' in change else ""
                self.console.print(f"  • {change['file_path']}{line_info}")
                if 'backup_path' in change:
                    self.console.print(f"    [dim]Backup: {change['backup_path']}[/dim]")

        if summary['rejected'] > 0:
            self.console.print("\n[bold yellow]Rejected Changes:[/bold yellow]")
            for change in summary['rejected_changes']:
                line_info = f" (line {change.get('line_number', 'N/A')})" if 'line_number' in change else ""
                self.console.print(f"  • {change['file_path']}{line_info}")

        if summary['pending'] > 0:
            self.console.print("\n[bold blue]Pending Changes:[/bold blue]")
            for change in summary['pending_changes']:
                line_info = f" (line {change.get('line_number', 'N/A')})" if 'line_number' in change else ""
                self.console.print(f"  • {change['file_path']}{line_info}")

    def _generate_layout(self) -> Layout:
        """Generate the layout for the interactive display."""
        layout = Layout()
        
        # Create header, body, and footer sections
        layout.split(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="footer", size=3)
        )
        
        # Configure the body section
        layout["body"].split_row(
            Layout(name="issue_info", ratio=1),
            Layout(name="code_display", ratio=2)
        )
        
        # Fill the sections with content
        layout["header"].update(self._generate_header())
        layout["issue_info"].update(self._generate_issue_info())
        layout["code_display"].update(self._generate_code_display())
        layout["footer"].update(self._generate_footer())
        
        return layout

    def _update_issue_by_file(self) -> None:
        """Update the current issue index based on the selected file."""
        if not self.files or not self.issues:
            return
            
        current_file = self.files[self.current_file_index]
        
        # Find the first issue that matches the current file
        for i, issue_data in enumerate(self.issues):
            if issue_data["issue"].get("file_path") == current_file:
                self.current_issue_index = i
                break

    def _display_error_report(self) -> None:
        """Display an error report."""
        error_message = self.results.get("error", "Unknown error")
        self.console.print(Panel(
            f"[bold red]Error:[/bold red] {error_message}",
            title="VaahAI Code Review Error",
            border_style="red"
        ))

def generate_interactive_diff_report(
    results: Dict[str, Any], 
    console: Optional[Console] = None,
    code_change_manager: Optional[CodeChangeManager] = None
):
    """
    Generate and display an interactive diff report from review results.
    
    This is a helper function that creates an InteractiveDiffReporter instance
    and displays the interactive report.
    
    Args:
        results: Dictionary containing the review results
        console: Optional Rich console instance to use for output
        code_change_manager: Optional CodeChangeManager instance for handling code changes
    """
    # Create a code change manager if not provided
    if code_change_manager is None:
        code_change_manager = CodeChangeManager()
        # Enable test mode for non-interactive testing environments
        code_change_manager.set_test_mode(True, 'y')
    
    # Create reporter
    reporter = InteractiveDiffReporter(results, console, code_change_manager)
    
    # Display the interactive report
    reporter.display_interactive_report()
