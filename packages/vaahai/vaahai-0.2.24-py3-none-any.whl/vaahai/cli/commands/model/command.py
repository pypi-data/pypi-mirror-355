"""
VaahAI model command implementation.

This module contains the implementation of the model command,
which is used to manage LLM models for VaahAI.
"""

import os
from pathlib import Path
from typing import Optional, List

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown

from vaahai.cli.utils.console import print_error, print_info, print_success, print_panel
from vaahai.cli.utils.help import CustomHelpCommand, create_typer_app
from vaahai.config.manager import ConfigManager
from vaahai.config.llm_utils import (
    list_providers,
    list_models,
    get_all_capabilities,
    get_providers_with_capability,
)

# Create a rich console for formatted output
console = Console()

# Create the model command group with custom help formatting
model_app = create_typer_app(
    name="model",
    help="Manage LLM models for VaahAI",
    add_completion=True,
    no_args_is_help=True,
)


@model_app.callback(invoke_without_command=True)
def callback(ctx: typer.Context):
    """
    Manage LLM models for VaahAI.
    """
    if ctx.invoked_subcommand is None:
        ctx.invoke(list_cmd)


@model_app.command("list", cls=CustomHelpCommand)
def list_cmd(
    ctx: typer.Context,
    provider: Optional[str] = typer.Option(
        None,
        "--provider",
        "-p",
        help="Filter models by provider",
    ),
    capability: Optional[str] = typer.Option(
        None,
        "--capability",
        "-c",
        help="Filter models by capability (text, code, vision, audio, embedding, function_calling)",
    ),
    min_context: Optional[int] = typer.Option(
        None,
        "--min-context",
        "-m",
        help="Filter models by minimum context length",
    ),
    show_details: bool = typer.Option(
        False,
        "--details",
        "-d",
        help="Show detailed information about models",
    ),
):
    """
    List available LLM models.

    This command shows available LLM models for all providers or a specific provider.
    You can filter models by capability or minimum context length.
    """
    config_manager = ConfigManager()
    
    # Get current provider and model
    current_provider = config_manager.get_current_provider()
    current_model = config_manager.get_model()
    
    # If provider is specified, validate it
    if provider and provider not in list_providers():
        print_error(f"Unsupported provider: {provider}")
        raise typer.Exit(1)
    
    # Get providers to list models for
    providers = [provider] if provider else list_providers()
    
    # Create a table for each provider
    for p in providers:
        try:
            # Get models for the provider
            models = list_models(p)
            
            # Filter by capability if specified
            if capability:
                models = config_manager.filter_models_by_capability(capability, p)
                if not models:
                    continue
            
            # Filter by minimum context length if specified
            if min_context:
                models = config_manager.filter_models_by_context_length(min_context, p)
                if not models:
                    continue
            
            # Create a table for the provider
            table = Table(title=f"{p.upper()} Models")
            
            # Add columns based on detail level
            table.add_column("Model", style="cyan")
            if show_details:
                table.add_column("Capabilities", style="green")
                table.add_column("Context Length", style="yellow")
                table.add_column("Description", style="blue")
            
            # Add rows for each model
            for model in models:
                # Check if this is the current model for the current provider
                is_current = (p == current_provider and model == current_model)
                model_name = f"{model} [bold yellow]*[/bold yellow]" if is_current else model
                
                if show_details:
                    # Get model details
                    model_info = config_manager.get_model_info(model, p)
                    capabilities = ", ".join(model_info["capabilities"])
                    context_length = f"{model_info['context_length']:,}"
                    description = model_info["description"]
                    
                    table.add_row(model_name, capabilities, context_length, description)
                else:
                    table.add_row(model_name)
            
            # Print the table
            console.print(table)
            
            # Add a note if this is the current provider
            if p == current_provider:
                print_info(f"[bold yellow]*[/bold yellow] = Current model")
                
        except Exception as e:
            print_error(f"Error listing models for provider {p}: {str(e)}")
    
    # Print a message if no models were found
    if not any(list_models(p) for p in providers):
        print_error("No models found matching the specified criteria")


@model_app.command("info", cls=CustomHelpCommand)
def info(
    ctx: typer.Context,
    model: Optional[str] = typer.Argument(
        None,
        help="Model name to get information about",
    ),
    provider: Optional[str] = typer.Option(
        None,
        "--provider",
        "-p",
        help="Provider name (required if model name is ambiguous)",
    ),
):
    """
    Show detailed information about a specific model.

    If no model is specified, shows information about the current model.
    """
    config_manager = ConfigManager()
    
    # Get current provider and model if not specified
    if not provider:
        provider = config_manager.get_current_provider()
    
    if not model:
        model = config_manager.get_model(provider)
    
    try:
        # Get model information
        model_info = config_manager.get_model_info(model, provider)
        
        # Create a markdown string with model information
        md = f"""
        # {model_info['name']} ({provider.upper()})
        
        {model_info['description']}
        
        ## Capabilities
        
        {', '.join(model_info['capabilities'])}
        
        ## Context Length
        
        {model_info['context_length']:,} tokens
        
        ## Provider
        
        {provider.upper()}
        """
        
        # Print the markdown
        console.print(Panel(Markdown(md), title=f"Model Information", expand=False))
        
    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)


@model_app.command("set", cls=CustomHelpCommand)
def set_cmd(
    ctx: typer.Context,
    model: str = typer.Argument(
        ...,
        help="Model name to set as current",
    ),
    provider: Optional[str] = typer.Option(
        None,
        "--provider",
        "-p",
        help="Provider name (required if model name is ambiguous)",
    ),
    save: bool = typer.Option(
        True,
        "--save/--no-save",
        help="Save the configuration after setting the model",
    ),
):
    """
    Set the current model for a provider.

    This command sets the current model for the specified provider or the current provider.
    """
    config_manager = ConfigManager()
    
    # Get current provider if not specified
    if not provider:
        provider = config_manager.get_current_provider()
    
    try:
        # Set the model
        config_manager.set_model(model, provider)
        
        # Save the configuration if requested
        if save:
            config_manager.save()
            print_success(f"Set model to {model} for provider {provider} and saved configuration")
        else:
            print_success(f"Set model to {model} for provider {provider} (configuration not saved)")
        
    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)


@model_app.command("recommend", cls=CustomHelpCommand)
def recommend(
    ctx: typer.Context,
    capabilities: List[str] = typer.Option(
        None,
        "--capability",
        "-c",
        help="Required capabilities (can be specified multiple times)",
    ),
    provider: Optional[str] = typer.Option(
        None,
        "--provider",
        "-p",
        help="Provider name (defaults to current provider)",
    ),
    set_model: bool = typer.Option(
        False,
        "--set",
        "-s",
        help="Set the recommended model as current",
    ),
    save: bool = typer.Option(
        False,
        "--save",
        help="Save the configuration after setting the model (only if --set is used)",
    ),
):
    """
    Get recommended model based on capabilities.

    This command shows the recommended model for the specified provider based on the required capabilities.
    """
    config_manager = ConfigManager()
    
    # Get current provider if not specified
    if not provider:
        provider = config_manager.get_current_provider()
    
    try:
        # Get the recommended model
        model = config_manager.get_recommended_model(capabilities, provider)
        
        # Get model information
        model_info = config_manager.get_model_info(model, provider)
        
        # Print the recommendation
        print_panel(
            f"Recommended model for {provider}: [bold cyan]{model}[/bold cyan]\n\n"
            f"Description: {model_info['description']}\n\n"
            f"Capabilities: {', '.join(model_info['capabilities'])}\n\n"
            f"Context Length: {model_info['context_length']:,} tokens",
            title="Model Recommendation"
        )
        
        # Set the model if requested
        if set_model:
            config_manager.set_model(model, provider)
            
            # Save the configuration if requested
            if save:
                config_manager.save()
                print_success(f"Set model to {model} for provider {provider} and saved configuration")
            else:
                print_success(f"Set model to {model} for provider {provider} (configuration not saved)")
        
    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)


@model_app.command("capabilities", cls=CustomHelpCommand)
def capabilities(
    ctx: typer.Context,
    provider: Optional[str] = typer.Option(
        None,
        "--provider",
        "-p",
        help="Filter by provider",
    ),
    capability: Optional[str] = typer.Option(
        None,
        "--capability",
        "-c",
        help="Show providers and models with this capability",
    ),
):
    """
    List available model capabilities.

    This command shows available model capabilities and which providers support them.
    """
    config_manager = ConfigManager()
    
    # If capability is specified, show providers and models with that capability
    if capability:
        # Get providers with the capability
        providers = get_providers_with_capability(capability)
        
        if not providers:
            print_error(f"No providers found with capability: {capability}")
            raise typer.Exit(1)
        
        # Filter by provider if specified
        if provider:
            if provider not in providers:
                print_error(f"Provider {provider} does not have models with capability: {capability}")
                raise typer.Exit(1)
            providers = [provider]
        
        # Create a table for each provider
        for p in providers:
            # Get models with the capability
            models = config_manager.filter_models_by_capability(capability, p)
            
            # Create a table for the provider
            table = Table(title=f"{p.upper()} Models with {capability} capability")
            table.add_column("Model", style="cyan")
            table.add_column("Context Length", style="yellow")
            table.add_column("Description", style="blue")
            
            # Add rows for each model
            for model in models:
                # Get model details
                model_info = config_manager.get_model_info(model, p)
                context_length = f"{model_info['context_length']:,}"
                description = model_info["description"]
                
                table.add_row(model, context_length, description)
            
            # Print the table
            console.print(table)
            
    else:
        # Show all capabilities
        capabilities = get_all_capabilities()
        
        # Create a table for capabilities
        table = Table(title="Available Model Capabilities")
        table.add_column("Capability", style="cyan")
        table.add_column("Description", style="blue")
        table.add_column("Providers", style="green")
        
        # Add rows for each capability
        for cap in capabilities:
            # Get providers with the capability
            providers = get_providers_with_capability(cap)
            providers_str = ", ".join(providers) if providers else "None"
            
            # Get description based on capability
            if cap == "text":
                description = "Basic text generation and understanding"
            elif cap == "code":
                description = "Code generation and understanding"
            elif cap == "vision":
                description = "Image understanding and processing"
            elif cap == "audio":
                description = "Audio transcription and understanding"
            elif cap == "embedding":
                description = "Vector embedding generation"
            elif cap == "function_calling":
                description = "Structured function calling capabilities"
            else:
                description = ""
            
            table.add_row(cap, description, providers_str)
        
        # Print the table
        console.print(table)
