"""
VaahAI review command implementation.

This module contains the implementation of the review command,
which is used to perform code reviews on files or directories.
"""

import os
import logging
import time
import threading
from pathlib import Path
from typing import List, Optional
import sys
from datetime import datetime

import typer
from InquirerPy import inquirer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.tree import Tree
from rich.emoji import Emoji
from rich.text import Text
from rich.columns import Columns

from vaahai.cli.utils.help import CustomHelpCommand, create_typer_app
from vaahai.review.steps.registry import ReviewStepRegistry
from vaahai.review.runner import ReviewRunner
from vaahai.review.steps.base import ReviewStep, ReviewStepCategory, ReviewStepSeverity
from vaahai.review.steps.progress import ReviewStepStatus
from vaahai.reporting.formats import OutputFormat
from vaahai.reporting.markdown_reporter import MarkdownReporter, generate_markdown_report
from vaahai.reporting.html_reporter import HTMLReporter, generate_html_report
from vaahai.reporting.interactive_diff_reporter import InteractiveDiffReporter, generate_interactive_diff_report
from vaahai.utils.code_change_manager import CodeChangeManager

# Import built-in review steps to ensure they are registered
from vaahai.review.steps.built_in import LineLength, IndentationConsistency
from vaahai.review.steps.built_in import HardcodedSecrets, SQLInjection
from vaahai.review.steps.built_in import InefficientLoops, LargeMemoryUsage

# Import detection agents
from vaahai.agents.applications.language_detection.agent import LanguageDetectionAgent
from vaahai.agents.applications.framework_detection.agent import FrameworkDetectionAgent

# Create a rich console for formatted output
console = Console()

# Status emoji mapping for visual indicators
STATUS_EMOJI = {
    ReviewStepStatus.PENDING: "⏳",
    ReviewStepStatus.IN_PROGRESS: "🔄",
    ReviewStepStatus.COMPLETED: "✅",
    ReviewStepStatus.FAILED: "❌",
    ReviewStepStatus.SKIPPED: "⏭️"
}

# Severity emoji for different severity levels
SEVERITY_EMOJI = {
    "critical": "🔴",
    "high": "🟠",
    "medium": "🟡",
    "low": "🟢",
    "info": "🔵",
}

# Category emoji for different categories
CATEGORY_EMOJI = {
    "security": "🔒",
    "performance": "⚡",
    "style": "✨",
    "complexity": "🧩",
    "maintainability": "🔧",
    "best_practice": "📚",
    "convention": "📏",
    "error": "💥",
    "warning": "⚠️",
    "other": "❓",
}

# Create the review command group with custom help formatting
review_app = create_typer_app(
    name="review",
    help="Perform code reviews on files or directories",
    add_completion=False,
)


@review_app.callback()
def callback():
    """
    Perform code reviews on files or directories.
    """
    pass


@review_app.command("run", cls=CustomHelpCommand)
def run(
    path: Path = typer.Argument(
        ...,
        help="Path to the file or directory to review",
        exists=True,
    ),
    depth: str = typer.Option(
        "standard",
        "--depth",
        "-d",
        help="Depth of the review (quick, standard, thorough)",
    ),
    focus: Optional[str] = typer.Option(
        None,
        "--focus",
        "-f",
        help="Focus area for the review (style, security, performance)",
    ),
    severity: Optional[str] = typer.Option(
        None,
        "--severity",
        "-s",
        help="Minimum severity level (critical, high, medium, low)",
    ),
    debug: bool = typer.Option(
        False,
        "--debug",
        help="Show debug information",
    ),
    format: str = typer.Option(
        None,
        "--format",
        "-f",
        help="Output format for the report (rich, markdown, html, interactive)",
        case_sensitive=False,
    ),
    apply_changes: bool = typer.Option(
        False,
        "--apply-changes",
        "-a",
        help="Enable applying suggested code changes (only works with interactive format)",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what changes would be made without actually modifying files",
    ),
    backup_dir: Optional[str] = typer.Option(
        None,
        "--backup-dir",
        help="Directory to store backups of modified files (default: ~/.vaahai/backups)",
    ),
    no_confirm: bool = typer.Option(
        False,
        "--no-confirm",
        help="Apply changes without asking for confirmation (use with caution)",
    ),
):
    """
    Run a code review on the specified file or directory.

    This command analyzes the code in the specified path and provides
    feedback on code quality, potential bugs, and suggested improvements.
    """
    # --- Language and Framework Detection ---
    try:
        lang_agent = LanguageDetectionAgent({"name": "LangDetectCLI"})
        lang_result = lang_agent.run(str(path))
        detected_language = lang_result.get("primary_language", {}).get("name", "Unknown")
    except Exception:
        detected_language = "Unknown"

    try:
        fw_agent = FrameworkDetectionAgent({"name": "FrameworkDetectCLI"})
        fw_result = fw_agent.run(str(path))
        detected_framework = fw_result.get("primary_framework", {}).get("name", "Unknown")
    except Exception:
        detected_framework = "Unknown"

    # Enable debug logging if debug flag is set
    if debug:
        logging.basicConfig(level=logging.DEBUG)
        logging.getLogger("vaahai.review").setLevel(logging.DEBUG)
    
    console.print(
        Panel(
            f"[bold]Reviewing:[/bold] {path}\n"
            f"[bold]Language:[/bold] {detected_language}\n"
            f"[bold]Framework:[/bold] {detected_framework}\n"
            f"[bold]Depth:[/bold] {depth}\n"
            f"[bold]Focus:[/bold] {focus or 'All areas'}\n"
            f"[bold]Severity:[/bold] {severity or 'All levels'}",
            title="Code Review",
            border_style="blue",
        )
    )

    # Debug: Check if review steps are registered
    registry = ReviewStepRegistry()
    all_steps = registry.get_all_steps()
    if debug:
        console.print(f"[bold]Debug:[/bold] Found {len(all_steps)} registered review step classes:")
        for step_id, step_class in all_steps.items():
            # Check if the class has severity attribute
            severity_value = getattr(step_class, "severity", None)
            console.print(f"  - {step_id}: {step_class.__name__} (Severity: {severity_value})")

    # Convert focus string to category enum if provided
    category = None
    if focus:
        try:
            category = ReviewStepCategory[focus.upper()]
            if debug:
                console.print(f"[bold]Debug:[/bold] Selected category: {category.name} ({category.value})")
        except KeyError:
            console.print(f"[yellow]Warning:[/yellow] Unknown focus area '{focus}'. Using all areas.")
    
    # Convert severity string to severity enum if provided
    min_severity = None
    if severity:
        try:
            min_severity = ReviewStepSeverity[severity.upper()]
        except KeyError:
            console.print(f"[yellow]Warning:[/yellow] Unknown severity level '{severity}'. Using all levels.")
    
    # Determine severity level based on depth
    if depth == "quick":
        # For quick reviews, use only critical and high severity steps
        min_severity_level = ReviewStepSeverity.HIGH
    elif depth == "thorough":
        # For thorough reviews, use all steps
        min_severity_level = ReviewStepSeverity.LOW
    else:  # standard
        # For standard reviews, exclude low severity steps
        min_severity_level = ReviewStepSeverity.MEDIUM
        
    # Override with user-specified severity if provided
    if min_severity:
        min_severity_level = min_severity
    
    # Create a mapping of severity levels to their ordinal values for comparison
    # Higher severity has lower ordinal value (CRITICAL=0, HIGH=1, etc.)
    severity_order = {
        ReviewStepSeverity.CRITICAL: 0,
        ReviewStepSeverity.HIGH: 1,
        ReviewStepSeverity.MEDIUM: 2,
        ReviewStepSeverity.LOW: 3
    }
    
    min_severity_ordinal = severity_order.get(min_severity_level, 3)
    
    if debug:
        console.print(f"[bold]Debug:[/bold] Minimum severity level: {min_severity_level.name} (ordinal: {min_severity_ordinal})")
    
    # If format not provided, ask with InquirerPy
    if format is None:
        # Skip prompt in non-interactive environments (e.g., during tests)
        if not hasattr(sys.stdin, "isatty") or not sys.stdin.isatty():
            format = OutputFormat.RICH.value
        else:
            format = inquirer.select(
                message="Select output format",
                choices=[
                    ("Rich (default colourful CLI)", OutputFormat.RICH.value),
                    ("Markdown", OutputFormat.MARKDOWN.value),
                    ("HTML", OutputFormat.HTML.value),
                    ("Interactive Rich diff", OutputFormat.INTERACTIVE.value),
                ],
                default=OutputFormat.RICH.value,
            ).execute()
            # If a tuple is returned (edge case), extract value
            if isinstance(format, tuple):
                format = format[1]
    
    # Validate format string to enum (fallback to RICH)
    try:
        output_format = OutputFormat(format.lower())
    except ValueError:
        console.print(f"[yellow]Unknown format '{format}', falling back to 'rich'.[/yellow]")
        output_format = OutputFormat.RICH
    
    # Use a single Progress context manager for all progress reporting
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        # Initialize step instances
        init_task = progress.add_task("Creating review step instances...", total=1)
        
        # Create instances of all review steps
        step_instances = []
        for step_id in all_steps:
            instance = registry.create_step_instance(step_id)
            if instance:
                step_instances.append(instance)
        
        progress.update(init_task, completed=1, description=f"Created {len(step_instances)} review step instances")
        
        # Debug: Show all step instances with their categories and severities
        if debug:
            console.print("\n[bold]Debug:[/bold] All step instances:")
            for step in step_instances:
                step_severity_ordinal = severity_order.get(step.severity, 3)
                console.print(f"  - {step.id}: {step.__class__.__name__} (Category: {step.category.name} ({step.category.value}), Severity: {step.severity.name} (ordinal: {step_severity_ordinal}))")
        
        # Filter step instances based on category and severity
        filter_task = progress.add_task("Filtering review steps...", total=1)
        
        filtered_instances = []
        for step in step_instances:
            # Filter by category if specified
            if category and step.category != category:
                if debug:
                    console.print(f"  - [red]✗[/red] {step.id}: Filtered out due to category mismatch (step: {step.category.name}, filter: {category.name})")
                continue
                
            # Filter by severity based on depth
            step_severity_ordinal = severity_order.get(step.severity, 3)
            if step_severity_ordinal <= min_severity_ordinal:
                filtered_instances.append(step)
                if debug:
                    console.print(f"  - [green]✓[/green] {step.id}: Included in filtered steps")
            else:
                if debug:
                    console.print(f"  - [red]✗[/red] {step.id}: Filtered out due to severity (step: {step.severity.name} (ordinal: {step_severity_ordinal}), min: {min_severity_level.name} (ordinal: {min_severity_ordinal}))")
        
        progress.update(filter_task, completed=1, description=f"Selected {len(filtered_instances)} review steps")
        
        # Debug: Show which steps will be run
        if debug and filtered_instances:
            console.print("\n[bold]Debug:[/bold] Steps that will be run:")
            for step in filtered_instances:
                console.print(f"  - {step.id}: {step.__class__.__name__} (Category: {step.category.name}, Severity: {step.severity.name})")
        elif debug and not filtered_instances:
            console.print("\n[bold red]Debug:[/bold red] No steps will be run after filtering.")
        
        # Create a ReviewRunner with the filtered instances
        runner = ReviewRunner(steps=filtered_instances)
        
        # Create a progress display for the review steps
        if filtered_instances:
            # Add a task for overall progress
            overall_task = progress.add_task(
                "Running review steps...", 
                total=len(filtered_instances)
            )
            
            # Add tasks for each review step
            step_tasks = {}
            for step in filtered_instances:
                step_tasks[step.id] = progress.add_task(
                    f"[cyan]{step.id}[/cyan] ({step.category.name})",
                    total=1,
                    visible=False
                )
            
            # For directory reviews, track file-level progress
            file_progress_task = None
            file_tasks = {}
            
            # Create tasks for statistics and findings display
            statistics_task = progress.add_task("Collecting statistics...", total=1, visible=False)
            findings_task = progress.add_task("Analyzing key findings...", total=1, visible=False)
            
            # Run the review with progress tracking
            try:
                # Start a background thread to update progress
                def update_progress():
                    completed_steps = 0
                    last_stats_update = time.time()
                    stats_update_interval = 2.0  # Update statistics every 2 seconds
                    
                    while completed_steps < len(filtered_instances):
                        # Get current progress
                        progress_info = runner.get_progress().get_progress_summary()
                        
                        # Update overall progress
                        completed_steps = (
                            progress_info["completed_steps"] + 
                            progress_info["failed_steps"] + 
                            progress_info["skipped_steps"]
                        )
                        progress.update(overall_task, completed=completed_steps)
                        
                        # Update individual step progress
                        for step_id, status in runner.get_progress().step_statuses.items():
                            if step_id in step_tasks:
                                # Make the task visible if it's in progress or completed
                                if status in [ReviewStepStatus.IN_PROGRESS, ReviewStepStatus.COMPLETED, ReviewStepStatus.FAILED]:
                                    progress.update(step_tasks[step_id], visible=True)
                                
                                # Update completion status
                                if status in [ReviewStepStatus.COMPLETED, ReviewStepStatus.FAILED]:
                                    duration = runner.get_progress().get_step_duration(step_id)
                                    emoji = STATUS_EMOJI[status]
                                    
                                    progress.update(
                                        step_tasks[step_id], 
                                        completed=1,
                                        visible=True,
                                        description=(
                                            f"{emoji} [green]{step_id}[/green] ({duration:.2f}s)"
                                            if status == ReviewStepStatus.COMPLETED
                                            else f"{emoji} [red]{step_id}[/red] (failed in {duration:.2f}s)"
                                        )
                                    )
                                elif status == ReviewStepStatus.IN_PROGRESS:
                                    emoji = STATUS_EMOJI[status]
                                    progress.update(
                                        step_tasks[step_id],
                                        description=f"{emoji} [yellow]{step_id}[/yellow] (running...)"
                                    )
                                elif status == ReviewStepStatus.SKIPPED:
                                    emoji = STATUS_EMOJI[status]
                                    progress.update(
                                        step_tasks[step_id],
                                        completed=1,
                                        visible=True,
                                        description=f"{emoji} [blue]{step_id}[/blue] (skipped)"
                                    )
                        
                        # Update statistics and findings periodically
                        current_time = time.time()
                        if current_time - last_stats_update >= stats_update_interval:
                            # Get current statistics
                            statistics = runner.get_statistics()
                            if statistics.total_issues > 0:
                                # Make statistics task visible and update
                                progress.update(statistics_task, visible=True)
                                
                                # Create a statistics summary
                                stats_summary = statistics.get_statistics_summary()
                                
                                # Update statistics display
                                stats_description = (
                                    f"📊 [bold]Statistics:[/bold] "
                                    f"{stats_summary.get('total_issues', 0)} issues "
                                    f"({', '.join([f'{count} {sev}' for sev, count in stats_summary.get('issues_by_severity', {}).items()])})"
                                )
                                progress.update(statistics_task, description=stats_description)
                                
                                # Generate and display key findings
                                findings = runner.get_key_findings(max_findings=3)
                                if findings:
                                    # Make findings task visible and update
                                    progress.update(findings_task, visible=True)
                                    
                                    # Create a findings summary
                                    findings_text = []
                                    for finding in findings:
                                        if finding.get("type") == "severity":
                                            severity = finding.get("severity", "")
                                            emoji = SEVERITY_EMOJI.get(severity, "❓")
                                            findings_text.append(f"{emoji} {finding.get('count', 0)} {severity} issues")
                                        elif finding.get("type") == "category":
                                            category = finding.get("category", "")
                                            emoji = CATEGORY_EMOJI.get(category.lower(), "❓")
                                            findings_text.append(f"{emoji} {finding.get('count', 0)} {category} issues")
                                        
                                    findings_description = f"🔍 [bold]Key Findings:[/bold] {' | '.join(findings_text)}"
                                    progress.update(findings_task, description=findings_description)
                                
                                last_stats_update = current_time
                            
                            # Sleep briefly to avoid high CPU usage
                            time.sleep(0.1)
                            
                            # Exit if all steps are completed
                            if completed_steps >= len(filtered_instances):
                                break
                
                # Start the progress update in a separate thread
                progress_thread = threading.Thread(target=update_progress)
                progress_thread.daemon = True
                progress_thread.start()
                
                # Run the review
                if path.is_file():
                    # Run on a single file
                    with open(path, 'r') as f:
                        content = f.read()
                    result = runner.run_on_content(content, file_path=str(path), output_format=output_format)
                else:
                    # For directory reviews, add file progress tracking
                    file_count = sum(1 for _ in Path(path).rglob('*') if _.is_file() and not any(part.startswith('.') for part in _.parts))
                    file_progress_task = progress.add_task(f"Processing files in {path}", total=file_count, visible=True)
                    
                    # Create a file processing callback for the runner
                    def file_progress_callback(file_path, status="processing"):
                        nonlocal file_tasks
                        
                        # Create a task for this file if it doesn't exist
                        if file_path not in file_tasks:
                            file_tasks[file_path] = progress.add_task(
                                f"[cyan]{os.path.basename(file_path)}[/cyan]",
                                total=1,
                                visible=True
                            )
                        
                        # Update the task status
                        if status == "completed":
                            progress.update(file_tasks[file_path], completed=1, description=f"✅ {os.path.basename(file_path)}")
                            progress.update(file_progress_task, advance=1)
                        elif status == "failed":
                            progress.update(file_tasks[file_path], completed=1, description=f"❌ {os.path.basename(file_path)}")
                            progress.update(file_progress_task, advance=1)
                        elif status == "skipped":
                            progress.update(file_tasks[file_path], completed=1, description=f"⏭️ {os.path.basename(file_path)}")
                            progress.update(file_progress_task, advance=1)
                    
                    # Run on a directory with the callback
                    result = runner.run_on_directory(str(path), output_format=output_format, file_callback=file_progress_callback)
                
                # Wait for the progress thread to catch up
                time.sleep(0.5)
                
                # Display timing statistics
                progress_summary = runner.get_progress().get_progress_summary()
                stats_panel = Panel(
                    f"[bold]Total steps:[/bold] {progress_summary['total_steps']}\n"
                    f"[bold]Completed:[/bold] {progress_summary['completed_steps']} ✅\n"
                    f"[bold]Failed:[/bold] {progress_summary['failed_steps']} ❌\n"
                    f"[bold]Skipped:[/bold] {progress_summary['skipped_steps']} ⏭️\n"
                    f"[bold]Total duration:[/bold] {progress_summary['total_duration']:.2f}s",
                    title="Review Progress",
                    border_style="green"
                )
                console.print(stats_panel)
                
                # Display statistics summary
                statistics_summary = result.get("statistics", {})
                if statistics_summary:
                    # Create a statistics panel
                    stats_content = (
                        f"[bold]Files reviewed:[/bold] {statistics_summary.get('total_files', 0)}\n"
                        f"[bold]Files with issues:[/bold] {statistics_summary.get('files_with_issues', 0)} "
                        f"({statistics_summary.get('files_with_issues_percentage', 0):.1f}%)\n"
                        f"[bold]Total issues:[/bold] {statistics_summary.get('total_issues', 0)}\n"
                        f"[bold]Average issues per file:[/bold] {statistics_summary.get('issues_per_file', 0):.2f}"
                    )
                    
                    console.print(Panel(
                        stats_content,
                        title="Review Statistics",
                        border_style="blue"
                    ))
                    
                    # Issues by severity
                    issues_by_severity = statistics_summary.get("issues_by_severity", {})
                    if issues_by_severity:
                        console.print("\n[bold]Issues by Severity:[/bold]")
                        severity_table = Table(show_header=True, header_style="bold")
                        severity_table.add_column("Severity", style="cyan")
                        severity_table.add_column("Count", style="yellow")
                        severity_table.add_column("Percentage", style="green")
                        
                        total_issues = statistics_summary.get("total_issues", 0)
                        for severity, count in issues_by_severity.items():
                            percentage = (count / total_issues * 100) if total_issues > 0 else 0
                            severity_style = {
                                "critical": "bold red",
                                "high": "bold yellow",
                                "medium": "yellow",
                                "low": "green",
                                "info": "blue",
                            }.get(severity, "white")
                            
                            emoji = SEVERITY_EMOJI.get(severity, "")
                            severity_table.add_row(
                                f"{emoji} {severity.capitalize()}" if emoji else severity.capitalize(),
                                str(count),
                                f"{percentage:.1f}%",
                                style=severity_style
                            )
                        
                        console.print(severity_table)
                    
                    # Issues by category
                    issues_by_category = statistics_summary.get("issues_by_category", {})
                    if issues_by_category:
                        console.print("\n[bold]Issues by Category:[/bold]")
                        category_table = Table(show_header=True, header_style="bold")
                        category_table.add_column("Category", style="cyan")
                        category_table.add_column("Count", style="yellow")
                        category_table.add_column("Percentage", style="green")
                        
                        total_issues = statistics_summary.get("total_issues", 0)
                        for category, count in issues_by_category.items():
                            percentage = (count / total_issues * 100) if total_issues > 0 else 0
                            emoji = CATEGORY_EMOJI.get(category.lower(), "")
                            category_table.add_row(
                                f"{emoji} {category}" if emoji else category,
                                str(count),
                                f"{percentage:.1f}%"
                            )
                        
                        console.print(category_table)
                    
                    # Most common issues
                    most_common_issues = statistics_summary.get("most_common_issues", [])
                    if most_common_issues:
                        console.print("\n[bold]Most Common Issues:[/bold]")
                        issues_table = Table(show_header=True, header_style="bold")
                        issues_table.add_column("Issue", style="cyan")
                        issues_table.add_column("Count", style="yellow")
                        
                        for issue, count in most_common_issues:
                            issues_table.add_row(
                                issue[:100] + ("..." if len(issue) > 100 else ""),
                                str(count)
                            )
                        
                        console.print(issues_table)
                
                # Display key findings
                key_findings = result.get("key_findings", [])
                if key_findings:
                    console.print("\n[bold]Key Findings:[/bold]")
                    findings_table = Table(show_header=True, header_style="bold", title="Key Findings", title_style="bold blue")
                    findings_table.add_column("Type", style="cyan")
                    findings_table.add_column("Finding", style="yellow")
                    findings_table.add_column("Count", style="green")
                    
                    for finding in key_findings:
                        if finding.get("type") == "severity":
                            severity = finding.get("severity", "")
                            count = finding.get("count", 0)
                            message = finding.get("message", f"{count} {severity} issues found")
                            
                            severity_style = {
                                "critical": "bold red",
                                "high": "bold yellow",
                                "medium": "yellow",
                                "low": "green",
                                "info": "blue",
                            }.get(severity, "white")
                            
                            emoji = SEVERITY_EMOJI.get(severity, "")
                            findings_table.add_row(
                                f"{emoji} Severity: {severity.capitalize()}" if emoji else f"Severity: {severity.capitalize()}",
                                message,
                                str(count),
                                style=severity_style
                            )
                        elif finding.get("type") == "category":
                            category = finding.get("category", "")
                            count = finding.get("count", 0)
                            message = finding.get("message", f"{count} {category} issues found")
                            
                            emoji = CATEGORY_EMOJI.get(category.lower(), "")
                            findings_table.add_row(
                                f"{emoji} Category: {category}" if emoji else f"Category: {category}",
                                message,
                                str(count)
                            )
                        elif finding.get("type") == "common_issue":
                            message = finding.get("message", "")
                            count = finding.get("count", 0)
                            
                            findings_table.add_row(
                                "Common Issue",
                                message[:100] + ("..." if len(message) > 100 else ""),
                                str(count)
                            )
                    
                    console.print(findings_table)
                
                # Display actionable recommendations
                recommendations = result.get("recommendations", [])
                if recommendations:
                    console.print("\n[bold]Recommendations:[/bold]")
                    recommendations_panel = Panel(
                        "\n".join([f"• {recommendation}" for recommendation in recommendations]),
                        title="Actionable Recommendations",
                        border_style="green"
                    )
                    console.print(recommendations_panel)
                
                # Handle different output formats
                if output_format == OutputFormat.MARKDOWN:
                    # Generate markdown report
                    markdown_report = generate_markdown_report(result)
                    
                    # Create a report file with timestamp
                    report_path = f"vaahai_review_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                    with open(report_path, "w") as f:
                        f.write(markdown_report)
                    
                    console.print(f"\n[green]Markdown report generated:[/green] {report_path}")
                    
                    # Show a preview of the report
                    preview_length = min(500, len(markdown_report))
                    console.print("\n[bold]Report Preview:[/bold]")
                    console.print(Panel(
                        markdown_report[:preview_length] + ("..." if len(markdown_report) > preview_length else ""),
                        title="Markdown Preview",
                        border_style="blue"
                    ))
                    
                    # Return early as we've already handled the output
                    console.print(f"[green]Report format:[/green] {output_format.value}")
                    return report_path
                
                elif output_format == OutputFormat.HTML:
                    # Generate HTML report
                    html_report = generate_html_report(result)
                    
                    # Create a report file with timestamp
                    report_path = f"vaahai_review_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                    with open(report_path, "w") as f:
                        f.write(html_report)
                    
                    console.print(f"\n[green]HTML report generated:[/green] {report_path}")
                    
                    # Show a preview of the report
                    preview_length = min(500, len(html_report))
                    console.print("\n[bold]Report Preview:[/bold]")
                    console.print(Panel(
                        html_report[:preview_length] + ("..." if len(html_report) > preview_length else ""),
                        title="HTML Preview",
                        border_style="blue"
                    ))
                    
                    # Return early as we've already handled the output
                    console.print(f"[green]Report format:[/green] {output_format.value}")
                    return report_path
                
                elif output_format == OutputFormat.INTERACTIVE:
                    # Generate interactive diff report
                    console.print(f"\n[green]Launching interactive code diff display...[/green]")
                    
                    # Configure code change manager based on CLI options
                    config = {
                        'dry_run': dry_run,
                        'confirm_changes': not no_confirm
                    }
                    
                    if backup_dir:
                        config['backup_dir'] = backup_dir
                    
                    # Initialize code change manager
                    code_change_manager = CodeChangeManager(config_path=None)
                    for key, value in config.items():
                        code_change_manager.config[key] = value
                    
                    # Display interactive report with code change manager if apply_changes is enabled
                    if apply_changes:
                        console.print("[yellow]Code change acceptance is enabled. You can accept or reject suggested changes.[/yellow]")
                        console.print("[yellow]Use 'a' to accept, 'r' to reject, arrow keys to navigate, and 'q' to quit.[/yellow]")
                        generate_interactive_diff_report(result, console, code_change_manager=code_change_manager)
                    else:
                        console.print("[yellow]Code change acceptance is disabled. Use --apply-changes to enable.[/yellow]")
                        generate_interactive_diff_report(result, console)
                    
                    # Return early as we've already handled the output
                    console.print(f"[green]Report format:[/green] {output_format.value}")
                    return None
                
                # Display results
                if result["status"] == "success":
                    total_issues = 0
                    step_results = {}
                    
                    # Process results based on their structure
                    if "results" in result and isinstance(result["results"], dict):
                        # Dictionary format
                        step_results = result["results"]
                        for step_result in step_results.values():
                            total_issues += len(step_result.get("issues", []))
                    elif "results" in result and isinstance(result["results"], list):
                        # List format
                        for step_result in result["results"]:
                            step_id = step_result.get("step_id")
                            if step_id:
                                step_results[step_id] = step_result
                                total_issues += len(step_result.get("issues", []))
                    
                    # Display progress summary
                    progress_summary = result.get("progress", {})
                    if progress_summary:
                        console.print("\n[bold]Review Progress Summary:[/bold]")
                        console.print(f"Total steps: {progress_summary.get('total_steps', 0)}")
                        console.print(f"Completed steps: {progress_summary.get('completed_steps', 0)}")
                        console.print(f"Failed steps: {progress_summary.get('failed_steps', 0)}")
                        console.print(f"Skipped steps: {progress_summary.get('skipped_steps', 0)}")
                        console.print(f"Total duration: {progress_summary.get('total_duration', 0):.2f} seconds")
                    
                    # Display statistics summary
                    statistics_summary = result.get("statistics", {})
                    if statistics_summary:
                        console.print("\n[bold]Review Statistics Summary:[/bold]")
                        
                        # File statistics
                        total_files = statistics_summary.get("total_files", 0)
                        files_with_issues = statistics_summary.get("files_with_issues", 0)
                        files_with_issues_percentage = statistics_summary.get("files_with_issues_percentage", 0)
                        
                        console.print(f"Files reviewed: {total_files}")
                        console.print(f"Files with issues: {files_with_issues} ({files_with_issues_percentage:.1f}%)")
                        console.print(f"Total issues: {statistics_summary.get('total_issues', 0)}")
                        console.print(f"Average issues per file: {statistics_summary.get('issues_per_file', 0):.2f}")
                        
                        # Issues by severity
                        issues_by_severity = statistics_summary.get("issues_by_severity", {})
                        if issues_by_severity:
                            console.print("\n[bold]Issues by Severity:[/bold]")
                            severity_table = Table(show_header=True, header_style="bold")
                            severity_table.add_column("Severity", style="cyan")
                            severity_table.add_column("Count", style="yellow")
                            severity_table.add_column("Percentage", style="green")
                            
                            total_issues = statistics_summary.get("total_issues", 0)
                            for severity, count in issues_by_severity.items():
                                percentage = (count / total_issues * 100) if total_issues > 0 else 0
                                severity_style = {
                                    "critical": "bold red",
                                    "high": "bold yellow",
                                    "medium": "yellow",
                                    "low": "green",
                                    "info": "blue",
                                }.get(severity, "white")
                                
                                emoji = SEVERITY_EMOJI.get(severity, "")
                                severity_table.add_row(
                                    f"{emoji} {severity.capitalize()}" if emoji else severity.capitalize(),
                                    str(count),
                                    f"{percentage:.1f}%",
                                    style=severity_style
                                )
                            
                            console.print(severity_table)
                        
                        # Issues by category
                        issues_by_category = statistics_summary.get("issues_by_category", {})
                        if issues_by_category:
                            console.print("\n[bold]Issues by Category:[/bold]")
                            category_table = Table(show_header=True, header_style="bold")
                            category_table.add_column("Category", style="cyan")
                            category_table.add_column("Count", style="yellow")
                            category_table.add_column("Percentage", style="green")
                            
                            for category, count in sorted(issues_by_category.items(), key=lambda x: x[1], reverse=True):
                                percentage = (count / total_issues * 100) if total_issues > 0 else 0
                                emoji = CATEGORY_EMOJI.get(category.lower(), "")
                                category_table.add_row(
                                    f"{emoji} {category}" if emoji else category,
                                    str(count),
                                    f"{percentage:.1f}%"
                                )
                            
                            console.print(category_table)
                        
                        # Most common issues
                        most_common_issues = statistics_summary.get("most_common_issues", [])
                        if most_common_issues:
                            console.print("\n[bold]Most Common Issues:[/bold]")
                            common_issues_table = Table(show_header=True, header_style="bold")
                            common_issues_table.add_column("Issue", style="cyan")
                            common_issues_table.add_column("Count", style="yellow")
                            
                            for issue, count in most_common_issues[:5]:  # Show top 5
                                common_issues_table.add_row(
                                    issue[:100] + ("..." if len(issue) > 100 else ""),  # Truncate long messages
                                    str(count)
                                )
                            
                            console.print(common_issues_table)
                    
                    # Display key findings
                    key_findings = result.get("key_findings", [])
                    if key_findings:
                        console.print("\n[bold yellow]Key Findings:[/bold yellow]")
                        findings_table = Table(show_header=True, header_style="bold")
                        findings_table.add_column("Type", style="cyan")
                        findings_table.add_column("Finding", style="yellow")
                        findings_table.add_column("Count", style="green")
                        
                        for finding in key_findings:
                            finding_type = finding.get("type", "")
                            count = finding.get("count", 0)
                            message = finding.get("message", "")
                            
                            # Determine style based on type and severity
                            if finding_type == "severity":
                                severity = finding.get("severity", "").lower()
                                type_display = f"[bold]{severity.upper()}[/bold]"
                                type_style = {
                                    "critical": "bold red",
                                    "high": "bold yellow",
                                    "medium": "yellow",
                                    "low": "green",
                                    "info": "blue",
                                }.get(severity, "white")
                                
                                findings_table.add_row(
                                    f"[{type_style}]{type_display}[/{type_style}]",
                                    message,
                                    str(count)
                                )
                            elif finding_type == "category":
                                category = finding.get("category", "").upper()
                                findings_table.add_row(
                                    f"[bold cyan]{category}[/bold cyan]",
                                    message,
                                    str(count)
                                )
                            elif finding_type == "common_issue":
                                findings_table.add_row(
                                    "COMMON",
                                    message[:100] + ("..." if len(message) > 100 else ""),
                                    str(count)
                                )
                        
                        console.print(findings_table)
                    
                    # Display recommendations
                    recommendations = result.get("recommendations", [])
                    if recommendations:
                        console.print("\n[bold green]Recommendations:[/bold green]")
                        recommendations_panel = Panel(
                            "\n".join([f"• {rec}" for rec in recommendations]),
                            title="Actionable Steps",
                            border_style="green"
                        )
                        console.print(recommendations_panel)
                    
                    if total_issues > 0:
                        console.print(f"\n[yellow]Found {total_issues} issues[/yellow]\n")
                        
                        # Create a table to display issues by step
                        table = Table(title="Review Results")
                        table.add_column("Step", style="cyan")
                        table.add_column("Category", style="magenta")
                        table.add_column("Issues", style="yellow")
                        table.add_column("Duration (s)", style="blue")
                        
                        for step_id, step_result in step_results.items():
                            # Find the step instance with this ID
                            step_instance = next((s for s in filtered_instances if s.id == step_id), None)
                            category_name = step_instance.category.name if step_instance else "Unknown"
                            issues_count = len(step_result.get("issues", []))
                            duration = step_result.get("duration", 0)
                            table.add_row(
                                step_id, 
                                category_name, 
                                str(issues_count),
                                f"{duration:.2f}"
                            )
                        
                        console.print(table)
                        
                        # Display detailed issues
                        console.print("\n[bold]Detailed Issues:[/bold]")
                        for step_id, step_result in step_results.items():
                            if step_result.get("issues"):
                                console.print(f"\n[bold cyan]{step_id}[/bold cyan]:")
                                for issue in step_result.get("issues", []):
                                    console.print(f"  • {issue}")
                    else:
                        console.print("\n[green]No issues found![/green]")
                else:
                    console.print(f"\n[red]Review failed:[/red] {result.get('message', 'Unknown error')}")
            except Exception as e:
                console.print(f"\n[red]✗ An unexpected error occurred:[/red] {str(e)}")
                if debug:
                    import traceback
                    console.print("\n[bold]Debug: Traceback[/bold]")
                    console.print(traceback.format_exc())
        else:
            console.print("\n[yellow]No review steps selected after filtering.[/yellow]")
            console.print("Try adjusting the focus area or severity level.")
    
    console.print(f"[green]Report format:[/green] {output_format.value}")
