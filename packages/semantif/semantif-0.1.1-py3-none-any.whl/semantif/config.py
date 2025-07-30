"""
Configuration management for the semantif library.
Stores global API settings provided via semantif.init().
"""

# Module-level globals for configuration
import os
_api_key = None
_api_provider = None
_model_name = None

def init(api_key: str = None, api_provider: str = "openai", model_name: str = "gpt-3.5-turbo") -> None:
    """
    Initialize global configuration for semantif.

    :param api_key: API key for the LLM provider (optional if using env var)
    :param api_provider: Identifier of the API provider (e.g., 'openai')
    :param model_name: Name of the model to use (e.g., 'gpt-3.5-turbo')
    """
    global _api_key, _api_provider, _model_name
    if api_key:
        _api_key = api_key
    _api_provider = api_provider
    _model_name = model_name

def get_api_key() -> str:
    """Return the configured API key or raise if missing."""
    if _api_key:
        return _api_key

    provider = get_api_provider()
    env_var_map = {
        "openai": "OPENAI_API_KEY",
    }

    env_var = env_var_map.get(provider)
    if env_var:
        env_key = os.getenv(env_var)
        if env_key:
            return env_key

    raise RuntimeError(
        f"API key not set. Please set the environment variable {env_var} or call init()."
    )

def get_api_provider() -> str:
    """Return the configured API provider."""
    return _api_provider

def get_model_name() -> str:
    """Return the configured model name."""
    return _model_name
