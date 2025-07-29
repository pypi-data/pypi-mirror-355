"""
LLM provider utilities for VaahAI.

This module provides utility functions for working with LLM providers,
including listing available providers and models, validating API keys,
and getting default models.
"""

import os
from typing import List, Dict, Any, Optional, Tuple, Set

from vaahai.config.schema import (
    OPENAI_MODELS,
    CLAUDE_MODELS,
    JUNIE_MODELS,
    OLLAMA_MODELS,
    PROVIDER_MODEL_INFO,
    MODEL_CAPABILITY_TEXT,
    MODEL_CAPABILITY_CODE,
    MODEL_CAPABILITY_VISION,
    MODEL_CAPABILITY_AUDIO,
    MODEL_CAPABILITY_EMBEDDING,
    MODEL_CAPABILITY_FUNCTION_CALLING,
)


# Available LLM providers
PROVIDERS = ["openai", "claude", "junie", "ollama"]


def list_providers() -> List[str]:
    """
    List all available LLM providers.
    
    Returns:
        List[str]: List of provider names
    """
    return PROVIDERS


def list_models(provider: str) -> List[str]:
    """
    List available models for a provider.
    
    Args:
        provider (str): Provider name
        
    Returns:
        List[str]: List of model names
        
    Raises:
        ValueError: If provider is not supported
    """
    if provider == "openai":
        return OPENAI_MODELS
    elif provider == "claude":
        return CLAUDE_MODELS
    elif provider == "junie":
        return JUNIE_MODELS
    elif provider == "ollama":
        return OLLAMA_MODELS
    else:
        raise ValueError(f"Unsupported provider: {provider}")


def get_model_info(provider: str, model: str) -> Tuple[str, List[str], int, str]:
    """
    Get detailed information about a specific model.
    
    Args:
        provider (str): Provider name
        model (str): Model name
        
    Returns:
        Tuple[str, List[str], int, str]: Tuple containing (model_name, capabilities, context_length, description)
        
    Raises:
        ValueError: If provider or model is not supported
    """
    if provider not in PROVIDERS:
        raise ValueError(f"Unsupported provider: {provider}")
    
    model_info_list = PROVIDER_MODEL_INFO.get(provider, [])
    for model_info in model_info_list:
        if model_info[0] == model:
            return model_info
    
    raise ValueError(f"Unsupported model: {model} for provider {provider}")


def get_model_capabilities(provider: str, model: str) -> List[str]:
    """
    Get capabilities of a specific model.
    
    Args:
        provider (str): Provider name
        model (str): Model name
        
    Returns:
        List[str]: List of capability names
        
    Raises:
        ValueError: If provider or model is not supported
    """
    _, capabilities, _, _ = get_model_info(provider, model)
    return capabilities


def get_model_context_length(provider: str, model: str) -> int:
    """
    Get the maximum context length of a specific model.
    
    Args:
        provider (str): Provider name
        model (str): Model name
        
    Returns:
        int: Maximum context length in tokens
        
    Raises:
        ValueError: If provider or model is not supported
    """
    _, _, context_length, _ = get_model_info(provider, model)
    return context_length


def get_model_description(provider: str, model: str) -> str:
    """
    Get the description of a specific model.
    
    Args:
        provider (str): Provider name
        model (str): Model name
        
    Returns:
        str: Model description
        
    Raises:
        ValueError: If provider or model is not supported
    """
    _, _, _, description = get_model_info(provider, model)
    return description


def filter_models_by_capability(provider: str, capability: str) -> List[str]:
    """
    Filter models by a specific capability.
    
    Args:
        provider (str): Provider name
        capability (str): Capability to filter by
        
    Returns:
        List[str]: List of model names with the specified capability
        
    Raises:
        ValueError: If provider is not supported
    """
    if provider not in PROVIDERS:
        raise ValueError(f"Unsupported provider: {provider}")
    
    model_info_list = PROVIDER_MODEL_INFO.get(provider, [])
    return [model[0] for model in model_info_list if capability in model[1]]


def filter_models_by_capabilities(provider: str, capabilities: List[str]) -> List[str]:
    """
    Filter models by multiple capabilities (model must have ALL capabilities).
    
    Args:
        provider (str): Provider name
        capabilities (List[str]): List of capabilities to filter by
        
    Returns:
        List[str]: List of model names with all specified capabilities
        
    Raises:
        ValueError: If provider is not supported
    """
    if provider not in PROVIDERS:
        raise ValueError(f"Unsupported provider: {provider}")
    
    model_info_list = PROVIDER_MODEL_INFO.get(provider, [])
    return [
        model[0] for model in model_info_list 
        if all(cap in model[1] for cap in capabilities)
    ]


def filter_models_by_context_length(provider: str, min_length: int) -> List[str]:
    """
    Filter models by minimum context length.
    
    Args:
        provider (str): Provider name
        min_length (int): Minimum context length in tokens
        
    Returns:
        List[str]: List of model names with at least the specified context length
        
    Raises:
        ValueError: If provider is not supported
    """
    if provider not in PROVIDERS:
        raise ValueError(f"Unsupported provider: {provider}")
    
    model_info_list = PROVIDER_MODEL_INFO.get(provider, [])
    return [model[0] for model in model_info_list if model[2] >= min_length]


def get_default_model(provider: str) -> str:
    """
    Get the default model for a provider.
    
    Args:
        provider (str): Provider name
        
    Returns:
        str: Default model name
        
    Raises:
        ValueError: If provider is not supported
    """
    if provider == "openai":
        return "gpt-4"
    elif provider == "claude":
        return "claude-3-sonnet-20240229"
    elif provider == "junie":
        return "junie-8b"
    elif provider == "ollama":
        return "llama3"
    else:
        raise ValueError(f"Unsupported provider: {provider}")


def get_recommended_model(provider: str, capabilities: Optional[List[str]] = None) -> str:
    """
    Get the recommended model for a provider based on capabilities.
    
    Args:
        provider (str): Provider name
        capabilities (Optional[List[str]]): List of required capabilities
        
    Returns:
        str: Recommended model name
        
    Raises:
        ValueError: If provider is not supported or no model with the required capabilities exists
    """
    if provider not in PROVIDERS:
        raise ValueError(f"Unsupported provider: {provider}")
    
    # If no capabilities specified, return the default model
    if not capabilities:
        return get_default_model(provider)
    
    # Get models that have all the required capabilities
    models = filter_models_by_capabilities(provider, capabilities)
    
    if not models:
        raise ValueError(f"No models found for provider {provider} with capabilities {capabilities}")
    
    # Return the first (usually most capable) model
    return models[0]


def validate_api_key(provider: str, api_key: str) -> bool:
    """
    Validate an API key for a provider.
    
    This is a basic validation that checks if the API key is not empty.
    For actual validation, you would need to make an API call to the provider,
    which is not implemented here to avoid unnecessary API calls.
    
    Args:
        provider (str): Provider name
        api_key (str): API key to validate
        
    Returns:
        bool: True if the API key is valid, False otherwise
    """
    # Basic validation - check if API key is not empty
    if not api_key:
        return False
    
    # Check if the provider is supported
    if provider not in PROVIDERS:
        return False
    
    # For actual validation, you would make an API call to the provider
    # But we'll just return True for now to avoid unnecessary API calls
    return True


def get_api_key_from_env(provider: str) -> Optional[str]:
    """
    Get API key from environment variables.
    
    Checks for environment variables in the following order:
    1. VAAHAI_{PROVIDER}_API_KEY (e.g., VAAHAI_OPENAI_API_KEY)
    2. {PROVIDER}_API_KEY (e.g., OPENAI_API_KEY)
    
    Args:
        provider (str): Provider name
        
    Returns:
        Optional[str]: API key if found, None otherwise
    """
    if provider not in PROVIDERS:
        return None
    
    # Check for VAAHAI_{PROVIDER}_API_KEY
    vaahai_env_var = f"VAAHAI_{provider.upper()}_API_KEY"
    if vaahai_env_var in os.environ:
        return os.environ[vaahai_env_var]
    
    # Check for {PROVIDER}_API_KEY
    env_var = f"{provider.upper()}_API_KEY"
    if env_var in os.environ:
        return os.environ[env_var]
    
    return None


def get_provider_config_path(provider: str) -> str:
    """
    Get the configuration path for a provider in dot notation.
    
    Args:
        provider (str): Provider name
        
    Returns:
        str: Configuration path in dot notation
        
    Raises:
        ValueError: If provider is not supported
    """
    if provider not in PROVIDERS:
        raise ValueError(f"Unsupported provider: {provider}")
    
    return f"llm.{provider}"


def get_all_capabilities() -> List[str]:
    """
    Get a list of all available model capabilities.
    
    Returns:
        List[str]: List of all capability names
    """
    return [
        MODEL_CAPABILITY_TEXT,
        MODEL_CAPABILITY_CODE,
        MODEL_CAPABILITY_VISION,
        MODEL_CAPABILITY_AUDIO,
        MODEL_CAPABILITY_EMBEDDING,
        MODEL_CAPABILITY_FUNCTION_CALLING,
    ]


def get_providers_with_capability(capability: str) -> List[str]:
    """
    Get a list of providers that have models with a specific capability.
    
    Args:
        capability (str): Capability name
        
    Returns:
        List[str]: List of provider names with models supporting the capability
    """
    result = []
    
    for provider in PROVIDERS:
        models = filter_models_by_capability(provider, capability)
        if models:
            result.append(provider)
    
    return result
