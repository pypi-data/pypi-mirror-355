"""
VaahAI helloworld command implementation.

This module contains the implementation of the helloworld command,
which demonstrates the Hello World agent functionality using the new
autogen-agentchat and autogen-ext packages.
"""

import typer
from typing import Optional
import asyncio
import locale
try:
    from zoneinfo import ZoneInfo
except ImportError:
    ZoneInfo = None
try:
    import tzlocal
except ImportError:
    tzlocal = None
import os

from vaahai.cli.utils.console import console, print_panel, print_success, print_error, progress_spinner
from vaahai.cli.utils.help import CustomHelpCommand, create_typer_app
from vaahai.agents.base.agent_factory import AgentFactory

# Create the helloworld command group with custom help formatting
helloworld_app = create_typer_app(
    name="helloworld",
    help="Demonstrate the Hello World agent functionality",
    add_completion=False,
    no_args_is_help=False,  # Don't show help when no args are provided
)


def detect_user_location():
    # Try to get country from locale
    try:
        loc = locale.getdefaultlocale()
        if loc and loc[0]:
            country = loc[0].split('_')[-1]
            if len(country) == 2:
                return country
    except Exception:
        pass
    # Try to get timezone
    try:
        if tzlocal:
            tz = tzlocal.get_localzone()
            return str(tz)
        elif ZoneInfo:
            import time
            return time.tzname[0]
    except Exception:
        pass
    return "unknown"


@helloworld_app.callback(invoke_without_command=True)
def callback(
    ctx: typer.Context,
    test_mode: bool = typer.Option(
        False, "--test", "-t", help="Run in test mode without using the OpenAI API"
    ),
    temperature: float = typer.Option(
        0.7, "--temperature", "-T", help="Temperature for response generation"
    ),
    dev_mode: bool = typer.Option(
        False, "--dev", "-d", help="Run in developer mode with additional details"
    ),
):
    """
    Run the Hello World agent to demonstrate VaahAI agent functionality.
    
    This command creates and runs a Hello World agent that generates
    a friendly and humorous greeting using the AutoGen framework.
    """
    # Only run if called directly (not as a parent command)
    if ctx.invoked_subcommand is None:
        try:
            # Check if we're running from the dev namespace
            # The command path will be "dev helloworld" if run from dev namespace
            is_dev_namespace = "dev" in ctx.command_path.split()
            # Use either explicit dev_mode flag or dev namespace
            show_details = dev_mode or is_dev_namespace
            
            # Create the Hello World agent
            config = {
                "name": "HelloWorldAgent",
                "provider": "openai",
                "temperature": temperature,
                "_test_mode": test_mode
            }
            
            agent = AgentFactory.create_agent("hello_world", config)
            
            # Detect user location
            user_location = detect_user_location()
            
            # Get prompt template content for dev mode
            prompt_template_content = None
            rendered_prompt = None
            if show_details:
                try:
                    from vaahai.agents.utils.prompt_manager import PromptManager
                    prompt_manager = PromptManager(agent_type="hello_world", agent_name="HelloWorldAgent")
                    template_path = prompt_manager.get_template_path("greeting")
                    
                    if template_path and os.path.exists(template_path):
                        with open(template_path, 'r') as f:
                            prompt_template_content = f.read()
                        
                        # Also get the rendered prompt with location
                        prompt_vars = {"location": user_location or "the world"}
                        rendered_prompt = prompt_manager.render_prompt("greeting", prompt_vars)
                    else:
                        prompt_template_content = "Template file not found"
                except Exception as e:
                    prompt_template_content = f"Error loading prompt: {str(e)}"
            
            # Run the agent asynchronously
            try:
                # Try to get existing event loop
                loop = asyncio.get_event_loop()
            except RuntimeError:
                # Create new event loop if one doesn't exist
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
            # Show spinner while waiting for agent response
            with progress_spinner("Waiting for agent response..."):
                result = loop.run_until_complete(agent.run(location=user_location))
            
            if result.get("status") == "success":
                # Display the agent's response
                print_panel(
                    f"[bold blue]Response:[/bold blue] {result.get('response')}",
                    title="VaahAI Hello World Agent Response",
                    style="green",
                )
                
                # Display additional details only in dev mode
                if show_details:
                    print_panel(
                        "\n".join([
                            f"[bold blue]Provider:[/bold blue] {config.get('provider', 'unknown')}",
                            f"[bold blue]Temperature:[/bold blue] {config.get('temperature', 0.7)}",
                            f"[bold blue]Location:[/bold blue] {user_location}",
                            f"[bold blue]Test Mode:[/bold blue] {'Yes' if config.get('_test_mode', False) else 'No'}",
                            f"[bold blue]Prompt Template:[/bold blue] greeting.md"
                        ]),
                        title="Agent Configuration and Runtime Details",
                        style="blue",
                    )
                    
                    # Show prompt template content
                    if prompt_template_content:
                        print_panel(
                            prompt_template_content,
                            title="Prompt Template",
                            style="yellow",
                        )
                    
                    # Show rendered prompt with variables substituted
                    if rendered_prompt:
                        print_panel(
                            rendered_prompt,
                            title="Rendered Prompt (Sent to Agent)",
                            style="magenta",
                        )
                
                print_success("Hello World agent response generated successfully!")
            else:
                # Display error message
                print_error(f"Error: {result.get('error', 'Unknown error')}")
        except Exception as e:
            print_error(f"Failed to run Hello World agent: {str(e)}")
