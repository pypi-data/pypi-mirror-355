"""
Prompt management system for VaahAI agents.

This module provides the PromptManager class for loading, managing, and rendering
prompt templates for agents. It supports both agent-specific and shared prompt templates.
"""

import os
from typing import Any, Dict, List, Optional
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape


class PromptManager:
    """
    Manages prompt templates for agents.
    
    The PromptManager loads templates from multiple locations (agent-specific and shared)
    and renders them using Jinja2 with context variables.
    """
    
    def __init__(self, agent_type: str, agent_name: Optional[str] = None):
        """
        Initialize the prompt manager.
        
        Args:
            agent_type: Type of agent (e.g., "code_executor", "hello_world")
            agent_name: Optional custom name for the agent (defaults to agent_type)
        """
        self.agent_type = agent_type
        self.agent_name = agent_name or agent_type
        self.prompt_dirs = self._get_prompt_directories()
        self.env = self._create_template_environment()
        
    def _get_prompt_directories(self) -> List[str]:
        """
        Get the directories containing prompt templates.
        
        Returns:
            List of directory paths to search for templates, in order of precedence
        """
        # Start with base project directory
        base_dir = Path(__file__).parent.parent.parent
        
        # List of directories to check for templates, in order of precedence
        dirs = []
        
        # 1. Agent-specific prompts (core or applications)
        for agent_category in ["core", "applications"]:
            agent_dir = base_dir / "agents" / agent_category / self.agent_type
            if agent_dir.exists():
                prompt_dir = agent_dir / "prompts"
                if prompt_dir.exists():
                    dirs.append(str(prompt_dir))
        
        # 2. Shared prompts directory
        shared_dir = base_dir / "agents" / "prompts"
        if shared_dir.exists():
            dirs.append(str(shared_dir))
            
        # If no directories found, use a default location
        if not dirs:
            dirs = [str(base_dir / "agents" / "prompts")]
            
            # Create the directory if it doesn't exist
            os.makedirs(dirs[0], exist_ok=True)
            
        return dirs
        
    def _create_template_environment(self) -> Environment:
        """
        Create a Jinja2 template environment.
        
        Returns:
            Configured Jinja2 Environment object
        """
        return Environment(
            loader=FileSystemLoader(self.prompt_dirs),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
    def render_prompt(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        Render a prompt template with the given context.
        
        Args:
            template_name: Name of the template (without extension)
            context: Dictionary of variables to use in the template
            
        Returns:
            The rendered template as a string
            
        Raises:
            ValueError: If the template cannot be found or rendered
        """
        try:
            # Try with .md extension first
            template_path = f"{template_name}.md"
            if template_path in self.env.list_templates():
                template = self.env.get_template(template_path)
                return template.render(**context)
                
            # Try without extension
            if template_name in self.env.list_templates():
                template = self.env.get_template(template_name)
                return template.render(**context)
                
            raise ValueError(f"Template not found: {template_name}")
        except Exception as e:
            raise ValueError(f"Error rendering template {template_name}: {str(e)}")
            
    def get_template_path(self, template_name: str) -> Optional[str]:
        """
        Get the path to a template file.
        
        Args:
            template_name: Name of the template (without extension)
            
        Returns:
            The full path to the template file, or None if not found
        """
        # Try with .md extension
        for ext in [".md", ""]:
            template_path = f"{template_name}{ext}"
            if template_path in self.env.list_templates():
                for prompt_dir in self.prompt_dirs:
                    full_path = os.path.join(prompt_dir, template_path)
                    if os.path.exists(full_path):
                        return full_path
        return None
        
    def list_templates(self) -> List[str]:
        """
        List all available templates.
        
        Returns:
            List of template names (without extensions)
        """
        templates = self.env.list_templates()
        # Remove extensions
        return [os.path.splitext(t)[0] for t in templates]
