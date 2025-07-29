"""
Chat command for VaahAI CLI.

This module provides commands for running group chats with VaahAI agents.
"""

import asyncio
import os
from typing import List, Optional, Dict, Any

import typer
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn

from vaahai.agents.base.agent_factory import AgentFactory
from vaahai.agents.utils.group_chat_manager import VaahAIGroupChatManager, GroupChatType, HumanInputMode
from vaahai.cli.utils.config import load_config
from vaahai.cli.utils.console import console, error_console

chat_app = typer.Typer(
    name="chat",
    help="Run multi-agent group chats",
    no_args_is_help=True
)


@chat_app.command("run")
def run_chat(
    agents: List[str] = typer.Option(
        None,
        "--agent", "-a",
        help="Agent types to include in the chat (can be specified multiple times)",
    ),
    chat_type: str = typer.Option(
        "round_robin",
        "--type", "-t",
        help="Type of group chat (round_robin, selector, broadcast, custom)",
    ),
    human_mode: str = typer.Option(
        "terminate",
        "--human", "-h",
        help="Human input mode (always, never, terminate, feedback)",
    ),
    message: str = typer.Option(
        None,
        "--message", "-m",
        help="Initial message to start the chat",
    ),
    config_file: Optional[str] = typer.Option(
        None,
        "--config", "-c",
        help="Path to a configuration file for the chat",
    ),
):
    """
    Run a group chat with multiple agents.
    
    This command creates a group chat with the specified agents and configuration,
    then starts the chat with an initial message.
    """
    try:
        # Load configuration
        config = load_config()
        group_chat_config = config.get("autogen", {}).get("group_chat", {})
        
        # Override with config file if provided
        if config_file:
            if not os.path.exists(config_file):
                error_console.print(f"[bold red]Error:[/] Configuration file not found: {config_file}")
                raise typer.Exit(1)
            
            # TODO: Load configuration from file
            pass
        
        # Create agents
        chat_agents = []
        if not agents:
            error_console.print("[bold red]Error:[/] At least one agent must be specified")
            raise typer.Exit(1)
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Creating agents...[/]"),
            console=console,
            transient=True,
        ) as progress:
            progress.add_task("Creating", total=None)
            
            for agent_type in agents:
                try:
                    agent = AgentFactory.create_agent(agent_type, {
                        "name": agent_type.capitalize(),
                        "_test_mode": True  # For demonstration purposes
                    })
                    chat_agents.append(agent)
                except Exception as e:
                    error_console.print(f"[bold red]Error creating agent '{agent_type}':[/] {str(e)}")
                    raise typer.Exit(1)
        
        # Map string values to enums
        chat_type_enum = None
        human_mode_enum = None
        
        try:
            chat_type_enum = GroupChatType(chat_type.upper())
        except ValueError:
            error_console.print(f"[bold red]Error:[/] Invalid chat type: {chat_type}")
            raise typer.Exit(1)
            
        try:
            human_mode_enum = HumanInputMode(human_mode.upper())
        except ValueError:
            error_console.print(f"[bold red]Error:[/] Invalid human input mode: {human_mode}")
            raise typer.Exit(1)
        
        # Create group chat manager
        console.print("[bold blue]Creating group chat manager...[/]")
        manager = VaahAIGroupChatManager(
            agents=chat_agents,
            config=group_chat_config,
            chat_type=chat_type_enum,
            human_input_mode=human_mode_enum
        )
        
        # Get initial message
        initial_message = message
        if not initial_message:
            initial_message = typer.prompt("Enter initial message to start the chat")
        
        # Run the chat
        console.print("[bold blue]Starting chat...[/]")
        result = asyncio.run(manager.start_chat(initial_message))
        
        # Display results
        console.print("\n[bold green]Chat completed![/]")
        console.print(Panel("[bold]Chat History[/]", expand=False))
        
        for msg in result["messages"]:
            sender = msg.get("sender", "Unknown")
            content = msg.get("content", "")
            
            console.print(Panel(
                Markdown(content),
                title=f"[bold]{sender}[/]",
                border_style="blue",
                expand=False
            ))
        
    except Exception as e:
        error_console.print(f"[bold red]Error:[/] {str(e)}")
        raise typer.Exit(1)


@chat_app.command("list-agents")
def list_agents():
    """
    List available agents for group chats.
    """
    try:
        # Get registered agent types
        agent_types = AgentFactory.get_registered_agent_types()
        
        console.print("[bold blue]Available Agents[/]")
        for agent_type in agent_types:
            console.print(f"- {agent_type}")
            
    except Exception as e:
        error_console.print(f"[bold red]Error:[/] {str(e)}")
        raise typer.Exit(1)
