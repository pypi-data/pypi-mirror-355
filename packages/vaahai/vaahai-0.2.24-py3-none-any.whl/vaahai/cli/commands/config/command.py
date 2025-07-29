"""
VaahAI config command implementation.

This module contains the implementation of the config command,
which is used to manage VaahAI configuration settings.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any, List

import typer
from rich.console import Console
from rich.table import Table
from InquirerPy import inquirer
from InquirerPy.base.control import Choice

from vaahai.cli.utils.console import (
    print_error, 
    print_info, 
    print_panel, 
    print_success, 
    print_warning,
    print_key_value,
    format_key,
    format_value,
)
from vaahai.cli.utils.help import CustomHelpCommand, create_typer_app
from vaahai.config.manager import ConfigManager
from vaahai.config.llm_utils import list_providers, list_models, get_model_capabilities

# Create a rich console for formatted output
console = Console()

# Create the config command group with custom help formatting
config_app = create_typer_app(
    name="config",
    help="Manage VaahAI configuration settings",
    add_completion=True,
    no_args_is_help=True,
)


@config_app.callback(invoke_without_command=True)
def callback(ctx: typer.Context):
    """
    Manage VaahAI configuration settings.
    """
    if ctx.invoked_subcommand is None:
        ctx.invoke(show)


@config_app.command("init", cls=CustomHelpCommand)
def init(
    ctx: typer.Context,
    config_dir: Optional[Path] = typer.Option(
        None,
        "--dir",
        "-d",
        help="Custom configuration directory path",
    ),
):
    """
    Initialize VaahAI configuration with interactive prompts.

    This command guides you through setting up your VaahAI configuration,
    including LLM provider selection, API keys, model preferences, and Docker settings.
    """
    # Access global options
    verbose = (
        ctx.parent.obj.get("verbose", False) if ctx.parent and ctx.parent.obj else False
    )
    quiet = (
        ctx.parent.obj.get("quiet", False) if ctx.parent and ctx.parent.obj else False
    )

    # Determine config directory
    if not config_dir:
        config_dir = Path(os.environ.get("VAAHAI_CONFIG_DIR", Path.home() / ".vaahai"))

    if verbose:
        print_info(f"Using configuration directory: {config_dir}")

    # Only show the panel if not in quiet mode
    if not quiet:
        print_panel(
            "[bold blue]VaahAI Configuration Wizard[/bold blue]\n\n"
            "This wizard will guide you through setting up your VaahAI configuration.\n"
            "You'll configure:\n"
            "- LLM provider selection\n"
            "- API keys\n"
            "- Model preferences\n"
            "- Docker settings",
            title="Configuration Wizard",
            style="blue",
        )

    # Create config directory if it doesn't exist
    if not config_dir.exists():
        if verbose:
            print_info(f"Creating configuration directory: {config_dir}")
        config_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize config manager
    config_manager = ConfigManager(config_dir / "config.toml")
    
    # Get available providers
    providers = list_providers()
    
    # Select provider
    provider = inquirer.select(
        message="Select your preferred LLM provider:",
        choices=providers,
        default=config_manager.get_current_provider(),
    ).execute()
    
    # Set the selected provider as the default provider
    config_manager.set_provider(provider)
    print_success(f"Set {provider} as the default LLM provider")
    
    # Save the provider to both user-level and project-level configurations
    # This ensures the provider is consistent across both configuration levels
    config_manager.save(user_level=True)
    
    # Also save to project level if we're in a project
    if config_manager.exists(level="project"):
        project_config = ConfigManager(config_manager.project_config_dir / "config.toml")
        project_config.set_provider(provider)
        project_config.save(user_level=False)
        print_success(f"Updated project-level configuration with {provider} as default provider")
    
    # Set API key
    current_api_key = config_manager.get_api_key(provider)
    masked_key = "********" if current_api_key else ""
    
    api_key = inquirer.secret(
        message=f"Enter your {provider} API key:",
        default=masked_key,
        transformer=lambda x: "********" if x else "",
    ).execute()
    
    # Only update if user entered a new key (not empty and not the masked placeholder)
    if api_key and api_key != "********":
        try:
            config_manager.set_api_key(api_key, provider)
            print_success(f"API key for {provider} set successfully!")
        except ValueError as e:
            print_warning(f"Could not validate API key: {str(e)}")
            print_info("The key will be saved but might not work correctly.")
            # Save it anyway as it might be a new valid key not recognized by validation
            config_path = f"providers.{provider}.api_key"
            config_manager.set(config_path, api_key)
    
    # Select model
    try:
        models = list_models(provider)
        if models:
            current_model = config_manager.get_model(provider)
            model = inquirer.select(
                message=f"Select your preferred {provider} model:",
                choices=models,
                default=current_model if current_model in models else models[0],
            ).execute()
            
            config_manager.set_model(model, provider)
            print_success(f"Model for {provider} set to {model}")
    except Exception as e:
        print_warning(f"Could not retrieve models for {provider}: {str(e)}")
        print_info("You can set your model later with 'vaahai model set'")
    
    # Configure Docker settings
    use_docker = inquirer.confirm(
        message="Do you want to use Docker for running LLMs?",
        default=config_manager.get("docker.enabled", False),
    ).execute()
    
    config_manager.set("docker.enabled", use_docker)
    
    if use_docker:
        docker_image = inquirer.text(
            message="Enter Docker image for LLMs:",
            default=config_manager.get("docker.image", ""),
        ).execute()
        
        config_manager.set("docker.image", docker_image)
        
        docker_memory = inquirer.text(
            message="Enter Docker memory limit (e.g., 8g):",
            default=config_manager.get("docker.memory", "8g"),
        ).execute()
        
        config_manager.set("docker.memory", docker_memory)
    
    # Save configuration
    if config_manager.save(user_level=True):
        print_success("Configuration saved successfully!")
    else:
        print_error("Failed to save configuration!")
        raise typer.Exit(code=1)


@config_app.command("show", cls=CustomHelpCommand)
def show(
    ctx: typer.Context,
    config_file: Optional[Path] = typer.Option(
        None,
        "--file",
        "-f",
        help="Path to specific configuration file to display",
    ),
):
    """
    Display current VaahAI configuration settings.

    This command shows your current VaahAI configuration settings,
    including LLM provider, API keys (masked), model preferences, and Docker settings.
    """
    # Access global options
    verbose = (
        ctx.parent.obj.get("verbose", False) if ctx.parent and ctx.parent.obj else False
    )
    quiet = (
        ctx.parent.obj.get("quiet", False) if ctx.parent and ctx.parent.obj else False
    )

    # Initialize config manager with specified file or default
    try:
        config_manager = ConfigManager(config_file)
    except Exception as e:
        print_error(f"Error loading configuration: {str(e)}")
        print_info("Run 'vaahai config init' to create a configuration file")
        raise typer.Exit(code=1)
    
    # Check if configuration exists
    if not config_manager.exists():
        print_error("Configuration file not found")
        print_info("Run 'vaahai config init' to create a configuration file")
        raise typer.Exit(code=1)
    
    # Get full configuration
    config = config_manager.get_full_config()
    
    # Display general settings
    print_panel(
        "[bold blue]VaahAI Configuration[/bold blue]",
        title="Current Configuration",
        style="blue",
    )
    
    # Display provider settings
    provider = config_manager.get_current_provider()
    print_info(f"[bold]Active LLM Provider:[/bold] {provider}")
    
    # Create a table for provider settings
    table = Table(title="Provider Settings", show_header=True, header_style="bold")
    table.add_column("Provider", style="cyan")
    table.add_column("Default", style="magenta")
    table.add_column("API Key", style="green")
    table.add_column("Model", style="yellow")
    
    for p in list_providers():
        try:
            api_key = config_manager.get_api_key(p)
            model = config_manager.get_model(p)
            
            # Mask API key
            masked_key = "********" if api_key else "[not set]"
            model_display = model if model else "[not set]"
            
            # Add default indicator for the active provider
            is_default = p == provider
            default_indicator = "✓" if is_default else ""
            
            table.add_row(
                p,
                default_indicator,
                masked_key,
                model_display,
            )
        except Exception:
            table.add_row(p, "", "[error]", "[error]")
    
    console.print(table)
    print_info("[dim]✓ indicates the active provider[/dim]")
    
    # Display Docker settings
    docker_enabled = config_manager.get("docker.enabled", False)
    print_info(f"\n[bold]Docker Settings:[/bold]")
    print_key_value("Enabled", str(docker_enabled))
    
    if docker_enabled:
        docker_image = config_manager.get("docker.image", "")
        docker_memory = config_manager.get("docker.memory", "")
        
        print_key_value("Image", docker_image if docker_image else "[not set]")
        print_key_value("Memory Limit", docker_memory if docker_memory else "[not set]")
    
    # Display output settings
    print_info(f"\n[bold]Output Settings:[/bold]")
    output_format = config_manager.get("output.format", "text")
    output_color = config_manager.get("output.color", True)
    
    print_key_value("Format", output_format)
    print_key_value("Color", str(output_color))
    
    # Display validation warnings if any
    errors = config_manager.validate()
    if errors:
        print_warning("\nConfiguration Warnings:")
        for error in errors:
            print_warning(f"- {error}")


@config_app.command("get", cls=CustomHelpCommand)
def get(
    ctx: typer.Context,
    key: str = typer.Argument(..., help="Configuration key in dot notation (e.g., llm.provider)"),
):
    """
    Get a specific configuration value.

    This command retrieves a specific configuration value using dot notation.
    For example: vaahai config get llm.provider
    """
    # Initialize config manager
    config_manager = ConfigManager()
    
    # Get the value
    try:
        value = config_manager.get(key)
        if value is None:
            print_error(f"Configuration key not found: {key}")
            raise typer.Exit(code=1)
        
        # Print the value
        print_key_value(key, str(value))
    except Exception as e:
        print_error(f"Error getting configuration value: {str(e)}")
        raise typer.Exit(code=1)


@config_app.command("set", cls=CustomHelpCommand)
def set_config(
    ctx: typer.Context,
    key: str = typer.Argument(..., help="Configuration key in dot notation (e.g., llm.provider)"),
    value: str = typer.Argument(..., help="Value to set"),
    project_level: bool = typer.Option(
        False,
        "--project",
        "-p",
        help="Set at project level instead of user level",
    ),
):
    """
    Set a specific configuration value.

    This command sets a specific configuration value using dot notation.
    For example: vaahai config set llm.provider openai
    """
    # Initialize config manager
    config_manager = ConfigManager()
    
    # Set the value
    try:
        # Convert value to appropriate type
        if value.lower() == "true":
            typed_value = True
        elif value.lower() == "false":
            typed_value = False
        elif value.isdigit():
            typed_value = int(value)
        elif value.replace(".", "", 1).isdigit() and value.count(".") == 1:
            typed_value = float(value)
        else:
            typed_value = value
        
        config_manager.set(key, typed_value)
        
        # Save the configuration
        if config_manager.save(user_level=not project_level):
            print_success(f"Configuration value set: {key} = {value}")
        else:
            print_error("Failed to save configuration!")
            raise typer.Exit(code=1)
    except Exception as e:
        print_error(f"Error setting configuration value: {str(e)}")
        raise typer.Exit(code=1)


@config_app.command("reset", cls=CustomHelpCommand)
def reset(
    ctx: typer.Context,
    confirm: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Skip confirmation prompt",
    ),
):
    """
    Reset configuration to defaults.

    This command resets the configuration to default values.
    """
    # Confirm reset if not explicitly confirmed
    if not confirm:
        confirmed = inquirer.confirm(
            message="Are you sure you want to reset the configuration to defaults?",
            default=False,
        ).execute()
        
        if not confirmed:
            print_info("Reset cancelled")
            return
    
    # Initialize config manager
    config_manager = ConfigManager()
    
    # Reset configuration
    config_manager.reset()
    
    # Save the configuration
    if config_manager.save(user_level=True):
        print_success("Configuration reset to defaults")
    else:
        print_error("Failed to reset configuration!")
        raise typer.Exit(code=1)
