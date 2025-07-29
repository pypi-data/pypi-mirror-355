"""
Configuration schema for VaahAI.

This module defines the schema for VaahAI configuration, which is used for validation
and documentation purposes. The schema defines the structure, types, and constraints
for configuration values.
"""

from typing import Dict, Any, List, Union, Optional, Tuple
from dataclasses import dataclass, field


# Model capabilities
MODEL_CAPABILITY_TEXT = "text"
MODEL_CAPABILITY_CODE = "code"
MODEL_CAPABILITY_VISION = "vision"
MODEL_CAPABILITY_AUDIO = "audio"
MODEL_CAPABILITY_EMBEDDING = "embedding"
MODEL_CAPABILITY_FUNCTION_CALLING = "function_calling"

# Model lists for validation with capabilities
# Format: (model_name, [capabilities], max_context_length, description)
OPENAI_MODELS_INFO: List[Tuple[str, List[str], int, str]] = [
    ("gpt-4", [MODEL_CAPABILITY_TEXT, MODEL_CAPABILITY_CODE, MODEL_CAPABILITY_FUNCTION_CALLING], 8192, "Powerful model for text and code generation"),
    ("gpt-4-turbo", [MODEL_CAPABILITY_TEXT, MODEL_CAPABILITY_CODE, MODEL_CAPABILITY_FUNCTION_CALLING], 128000, "Enhanced GPT-4 with larger context window"),
    ("gpt-4-32k", [MODEL_CAPABILITY_TEXT, MODEL_CAPABILITY_CODE, MODEL_CAPABILITY_FUNCTION_CALLING], 32768, "GPT-4 with extended context window"),
    ("gpt-3.5-turbo", [MODEL_CAPABILITY_TEXT, MODEL_CAPABILITY_CODE, MODEL_CAPABILITY_FUNCTION_CALLING], 16385, "Fast and cost-effective model for most tasks"),
    ("gpt-3.5-turbo-16k", [MODEL_CAPABILITY_TEXT, MODEL_CAPABILITY_CODE, MODEL_CAPABILITY_FUNCTION_CALLING], 16385, "GPT-3.5 with extended context window"),
    ("gpt-4o", [MODEL_CAPABILITY_TEXT, MODEL_CAPABILITY_CODE, MODEL_CAPABILITY_VISION, MODEL_CAPABILITY_FUNCTION_CALLING], 128000, "Latest multimodal model with vision capabilities"),
    ("gpt-4o-mini", [MODEL_CAPABILITY_TEXT, MODEL_CAPABILITY_CODE, MODEL_CAPABILITY_FUNCTION_CALLING], 128000, "Smaller version of GPT-4o for faster responses")
]

CLAUDE_MODELS_INFO: List[Tuple[str, List[str], int, str]] = [
    ("claude-3-opus-20240229", [MODEL_CAPABILITY_TEXT, MODEL_CAPABILITY_CODE, MODEL_CAPABILITY_VISION, MODEL_CAPABILITY_FUNCTION_CALLING], 200000, "Most powerful Claude model with vision capabilities"),
    ("claude-3-sonnet-20240229", [MODEL_CAPABILITY_TEXT, MODEL_CAPABILITY_CODE, MODEL_CAPABILITY_VISION, MODEL_CAPABILITY_FUNCTION_CALLING], 200000, "Balanced Claude model for most tasks"),
    ("claude-3-haiku-20240307", [MODEL_CAPABILITY_TEXT, MODEL_CAPABILITY_CODE, MODEL_CAPABILITY_VISION], 200000, "Fast and efficient Claude model"),
    ("claude-2.1", [MODEL_CAPABILITY_TEXT, MODEL_CAPABILITY_CODE], 100000, "Previous generation Claude model"),
    ("claude-2.0", [MODEL_CAPABILITY_TEXT, MODEL_CAPABILITY_CODE], 100000, "Previous generation Claude model"),
    ("claude-instant-1.2", [MODEL_CAPABILITY_TEXT, MODEL_CAPABILITY_CODE], 100000, "Fast previous generation Claude model")
]

JUNIE_MODELS_INFO: List[Tuple[str, List[str], int, str]] = [
    ("junie-8b", [MODEL_CAPABILITY_TEXT, MODEL_CAPABILITY_CODE], 8192, "Compact 8B parameter model for text and code"),
    ("junie-20b", [MODEL_CAPABILITY_TEXT, MODEL_CAPABILITY_CODE], 16384, "Mid-sized 20B parameter model with extended capabilities"),
    ("junie-large", [MODEL_CAPABILITY_TEXT, MODEL_CAPABILITY_CODE, MODEL_CAPABILITY_FUNCTION_CALLING], 32768, "Largest Junie model with function calling support")
]

OLLAMA_MODELS_INFO: List[Tuple[str, List[str], int, str]] = [
    ("llama3", [MODEL_CAPABILITY_TEXT, MODEL_CAPABILITY_CODE], 8192, "Meta's Llama 3 model for local deployment"),
    ("llama2", [MODEL_CAPABILITY_TEXT, MODEL_CAPABILITY_CODE], 4096, "Meta's Llama 2 model for local deployment"),
    ("mistral", [MODEL_CAPABILITY_TEXT, MODEL_CAPABILITY_CODE], 8192, "Mistral AI's efficient open model"),
    ("mixtral", [MODEL_CAPABILITY_TEXT, MODEL_CAPABILITY_CODE], 32768, "Mixture of experts model with extended capabilities"),
    ("phi3", [MODEL_CAPABILITY_TEXT, MODEL_CAPABILITY_CODE], 4096, "Microsoft's Phi-3 model for local deployment"),
    ("gemma", [MODEL_CAPABILITY_TEXT, MODEL_CAPABILITY_CODE], 8192, "Google's Gemma model for local deployment"),
    ("codellama", [MODEL_CAPABILITY_TEXT, MODEL_CAPABILITY_CODE], 16384, "Code-specialized Llama model"),
    ("qwen", [MODEL_CAPABILITY_TEXT, MODEL_CAPABILITY_CODE], 8192, "Alibaba's Qwen model for local deployment"),
    ("vicuna", [MODEL_CAPABILITY_TEXT, MODEL_CAPABILITY_CODE], 4096, "Fine-tuned Llama model for dialogue"),
    ("orca-mini", [MODEL_CAPABILITY_TEXT], 4096, "Lightweight model for basic text tasks")
]

# Extract just the model names for backward compatibility
OPENAI_MODELS = [model[0] for model in OPENAI_MODELS_INFO]
CLAUDE_MODELS = [model[0] for model in CLAUDE_MODELS_INFO]
JUNIE_MODELS = [model[0] for model in JUNIE_MODELS_INFO]
OLLAMA_MODELS = [model[0] for model in OLLAMA_MODELS_INFO]

# Dictionary mapping provider to model info
PROVIDER_MODEL_INFO = {
    "openai": OPENAI_MODELS_INFO,
    "claude": CLAUDE_MODELS_INFO,
    "junie": JUNIE_MODELS_INFO,
    "ollama": OLLAMA_MODELS_INFO
}


@dataclass
class OpenAIConfig:
    """
    Configuration for OpenAI provider.
    
    Attributes:
        api_key: API key for OpenAI
        api_base: Base URL for API requests (for Azure OpenAI or proxies)
        organization: Organization ID for OpenAI
        model: Model to use (e.g., gpt-4, gpt-3.5-turbo)
        temperature: Temperature for sampling (0.0 to 1.0)
        max_tokens: Maximum number of tokens to generate
        top_p: Nucleus sampling parameter
        frequency_penalty: Penalty for token frequency
        presence_penalty: Penalty for token presence
        timeout: Request timeout in seconds
    """
    
    api_key: str = ""
    api_base: str = ""
    organization: str = ""
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 4000
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    timeout: int = 120


@dataclass
class ClaudeConfig:
    """
    Configuration for Anthropic Claude provider.
    
    Attributes:
        api_key: API key for Anthropic
        api_base: Base URL for API requests (for proxies)
        model: Model to use (e.g., claude-3-opus-20240229)
        temperature: Temperature for sampling (0.0 to 1.0)
        max_tokens: Maximum number of tokens to generate
        top_p: Nucleus sampling parameter
        top_k: Top-k sampling parameter
        timeout: Request timeout in seconds
    """
    
    api_key: str = ""
    api_base: str = ""
    model: str = "claude-3-sonnet-20240229"
    temperature: float = 0.7
    max_tokens: int = 4000
    top_p: float = 1.0
    top_k: int = 40
    timeout: int = 120


@dataclass
class JunieConfig:
    """
    Configuration for Junie provider.
    
    Attributes:
        api_key: API key for Junie
        api_base: Base URL for API requests
        model: Model to use (e.g., junie-8b)
        temperature: Temperature for sampling (0.0 to 1.0)
        max_tokens: Maximum number of tokens to generate
        top_p: Nucleus sampling parameter
        timeout: Request timeout in seconds
    """
    
    api_key: str = ""
    api_base: str = ""
    model: str = "junie-8b"
    temperature: float = 0.7
    max_tokens: int = 4000
    top_p: float = 1.0
    timeout: int = 120


@dataclass
class OllamaConfig:
    """
    Configuration for Ollama provider.
    
    Attributes:
        api_base: Base URL for Ollama API (default: http://localhost:11434)
        model: Model to use (e.g., llama3)
        temperature: Temperature for sampling (0.0 to 1.0)
        max_tokens: Maximum number of tokens to generate
        top_p: Nucleus sampling parameter
        top_k: Top-k sampling parameter
        repeat_penalty: Penalty for repeated tokens
        timeout: Request timeout in seconds
    """
    
    api_base: str = "http://localhost:11434"
    model: str = "llama3"
    temperature: float = 0.7
    max_tokens: int = 4000
    top_p: float = 1.0
    top_k: int = 40
    repeat_penalty: float = 1.1
    timeout: int = 120


@dataclass
class LLMConfig:
    """
    Configuration for LLM providers.
    
    Attributes:
        provider: LLM provider to use (openai, claude, junie, ollama)
        openai: OpenAI-specific configuration
        claude: Claude-specific configuration
        junie: Junie-specific configuration
        ollama: Ollama-specific configuration
    """
    
    provider: str = "openai"
    openai: OpenAIConfig = field(default_factory=OpenAIConfig)
    claude: ClaudeConfig = field(default_factory=ClaudeConfig)
    junie: JunieConfig = field(default_factory=JunieConfig)
    ollama: OllamaConfig = field(default_factory=OllamaConfig)


@dataclass
class DockerResourceLimits:
    """Resource limits for Docker containers."""
    
    cpu: float = 2.0
    memory: str = "2g"


@dataclass
class DockerConfig:
    """Configuration for Docker execution environment."""
    
    enabled: bool = True
    image: str = "vaahai/execution:latest"
    resource_limits: DockerResourceLimits = field(default_factory=DockerResourceLimits)


@dataclass
class OutputConfig:
    """Configuration for output formatting."""
    
    format: str = "terminal"
    verbosity: str = "normal"
    color: bool = True


@dataclass
class AgentConfig:
    """Configuration for AI agents."""
    
    timeout: int = 300
    max_iterations: int = 10
    memory: bool = True
    logging: bool = True


@dataclass
class VaahAIConfig:
    """Root configuration for VaahAI."""
    
    llm: LLMConfig = field(default_factory=LLMConfig)
    docker: DockerConfig = field(default_factory=DockerConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)


def validate_config(config: Dict[str, Any]) -> List[str]:
    """
    Validate a configuration dictionary against the schema.
    
    Args:
        config (Dict[str, Any]): Configuration dictionary to validate
    
    Returns:
        List[str]: List of validation errors, empty if valid
    """
    errors = []
    
    # Validate LLM provider
    provider = config.get("llm", {}).get("provider", "")
    if provider not in ["openai", "claude", "junie", "ollama"]:
        errors.append(f"Invalid LLM provider: {provider}")
    
    # Validate OpenAI model
    if provider == "openai":
        model = config.get("llm", {}).get("openai", {}).get("model", "")
        if model not in OPENAI_MODELS:
            errors.append(f"Invalid OpenAI model: {model}")
    
    # Validate Claude model
    if provider == "claude":
        model = config.get("llm", {}).get("claude", {}).get("model", "")
        if model not in CLAUDE_MODELS:
            errors.append(f"Invalid Claude model: {model}")
    
    # Validate Junie model
    if provider == "junie":
        model = config.get("llm", {}).get("junie", {}).get("model", "")
        if model not in JUNIE_MODELS:
            errors.append(f"Invalid Junie model: {model}")
    
    # Validate Ollama model
    if provider == "ollama":
        model = config.get("llm", {}).get("ollama", {}).get("model", "")
        if model not in OLLAMA_MODELS:
            errors.append(f"Invalid Ollama model: {model}")
    
    # Validate output format
    output_format = config.get("output", {}).get("format", "")
    if output_format not in ["terminal", "markdown", "html", "json"]:
        errors.append(f"Invalid output format: {output_format}")
    
    # Validate verbosity
    verbosity = config.get("output", {}).get("verbosity", "")
    if verbosity not in ["quiet", "normal", "verbose", "debug"]:
        errors.append(f"Invalid verbosity level: {verbosity}")
    
    return errors


def config_to_schema(config: Dict[str, Any]) -> VaahAIConfig:
    """
    Convert a configuration dictionary to a schema object.
    
    Args:
        config (Dict[str, Any]): Configuration dictionary
    
    Returns:
        VaahAIConfig: Schema object
    """
    # Create the root config object
    schema_config = VaahAIConfig()
    
    # LLM configuration
    if "llm" in config:
        llm_config = config["llm"]
        if "provider" in llm_config:
            schema_config.llm.provider = llm_config["provider"]
        
        # OpenAI configuration
        if "openai" in llm_config:
            openai_config = llm_config["openai"]
            for key, value in openai_config.items():
                if hasattr(schema_config.llm.openai, key):
                    setattr(schema_config.llm.openai, key, value)
        
        # Claude configuration
        if "claude" in llm_config:
            claude_config = llm_config["claude"]
            for key, value in claude_config.items():
                if hasattr(schema_config.llm.claude, key):
                    setattr(schema_config.llm.claude, key, value)
        
        # Junie configuration
        if "junie" in llm_config:
            junie_config = llm_config["junie"]
            for key, value in junie_config.items():
                if hasattr(schema_config.llm.junie, key):
                    setattr(schema_config.llm.junie, key, value)
        
        # Ollama configuration
        if "ollama" in llm_config:
            ollama_config = llm_config["ollama"]
            for key, value in ollama_config.items():
                if hasattr(schema_config.llm.ollama, key):
                    setattr(schema_config.llm.ollama, key, value)
    
    # Docker configuration
    if "docker" in config:
        docker_config = config["docker"]
        if "enabled" in docker_config:
            schema_config.docker.enabled = docker_config["enabled"]
        if "image" in docker_config:
            schema_config.docker.image = docker_config["image"]
        if "resource_limits" in docker_config:
            resource_limits = docker_config["resource_limits"]
            if "cpu" in resource_limits:
                schema_config.docker.resource_limits.cpu = resource_limits["cpu"]
            if "memory" in resource_limits:
                schema_config.docker.resource_limits.memory = resource_limits["memory"]
    
    # Output configuration
    if "output" in config:
        output_config = config["output"]
        if "format" in output_config:
            schema_config.output.format = output_config["format"]
        if "verbosity" in output_config:
            schema_config.output.verbosity = output_config["verbosity"]
        if "color" in output_config:
            schema_config.output.color = output_config["color"]
    
    # Agent configuration
    if "agent" in config:
        agent_config = config["agent"]
        if "timeout" in agent_config:
            schema_config.agent.timeout = agent_config["timeout"]
        if "max_iterations" in agent_config:
            schema_config.agent.max_iterations = agent_config["max_iterations"]
        if "memory" in agent_config:
            schema_config.agent.memory = agent_config["memory"]
        if "logging" in agent_config:
            schema_config.agent.logging = agent_config["logging"]
    
    return schema_config


def schema_to_config(schema: VaahAIConfig) -> Dict[str, Any]:
    """
    Convert a schema object to a configuration dictionary.
    
    Args:
        schema (VaahAIConfig): Schema object
    
    Returns:
        Dict[str, Any]: Configuration dictionary
    """
    config = {
        "llm": {
            "provider": schema.llm.provider,
            "openai": {
                "api_key": schema.llm.openai.api_key,
                "api_base": schema.llm.openai.api_base,
                "organization": schema.llm.openai.organization,
                "model": schema.llm.openai.model,
                "temperature": schema.llm.openai.temperature,
                "max_tokens": schema.llm.openai.max_tokens,
                "top_p": schema.llm.openai.top_p,
                "frequency_penalty": schema.llm.openai.frequency_penalty,
                "presence_penalty": schema.llm.openai.presence_penalty,
                "timeout": schema.llm.openai.timeout
            },
            "claude": {
                "api_key": schema.llm.claude.api_key,
                "api_base": schema.llm.claude.api_base,
                "model": schema.llm.claude.model,
                "temperature": schema.llm.claude.temperature,
                "max_tokens": schema.llm.claude.max_tokens,
                "top_p": schema.llm.claude.top_p,
                "top_k": schema.llm.claude.top_k,
                "timeout": schema.llm.claude.timeout
            },
            "junie": {
                "api_key": schema.llm.junie.api_key,
                "api_base": schema.llm.junie.api_base,
                "model": schema.llm.junie.model,
                "temperature": schema.llm.junie.temperature,
                "max_tokens": schema.llm.junie.max_tokens,
                "top_p": schema.llm.junie.top_p,
                "timeout": schema.llm.junie.timeout
            },
            "ollama": {
                "api_base": schema.llm.ollama.api_base,
                "model": schema.llm.ollama.model,
                "temperature": schema.llm.ollama.temperature,
                "max_tokens": schema.llm.ollama.max_tokens,
                "top_p": schema.llm.ollama.top_p,
                "top_k": schema.llm.ollama.top_k,
                "repeat_penalty": schema.llm.ollama.repeat_penalty,
                "timeout": schema.llm.ollama.timeout
            }
        },
        "docker": {
            "enabled": schema.docker.enabled,
            "image": schema.docker.image,
            "resource_limits": {
                "cpu": schema.docker.resource_limits.cpu,
                "memory": schema.docker.resource_limits.memory
            }
        },
        "output": {
            "format": schema.output.format,
            "verbosity": schema.output.verbosity,
            "color": schema.output.color
        },
        "agent": {
            "timeout": schema.agent.timeout,
            "max_iterations": schema.agent.max_iterations,
            "memory": schema.agent.memory,
            "logging": schema.agent.logging
        }
    }
    
    return config
