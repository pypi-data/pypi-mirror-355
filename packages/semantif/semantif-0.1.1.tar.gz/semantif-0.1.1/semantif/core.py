"""
Core logic for semantif library.
Implements judge() function for semantic boolean evaluation.
"""

from typing import Any, Dict, List
from .config import get_api_provider, get_model_name, init
from .errors import SemantifError

# Import provider clients
from .api_clients import openai_client

# Auto-initialize configuration from environment
init()

def judge(
    semantic_condition: str,
    text_to_evaluate: str,
    *,
    temperature: float = 0.0,
    **kwargs: Any
) -> bool:
    """
    Evaluate whether the text meets the given semantic condition.
    Returns True if LLM responds with TRUE, False otherwise.

    :param semantic_condition: Description of the condition to evaluate.
    :param text_to_evaluate: Text that should be evaluated against the condition.
    :param temperature: Sampling temperature for the LLM call.
    :param kwargs: Additional parameters passed to the LLM client.
    """
    # Build messages for LLM
    system_msg = (
        "You are a semantic judgment engine. "
        "Given a condition and a text, respond with exactly TRUE or FALSE."
    )

    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": system_msg},
        {
            "role": "user",
            "content": (
                f"Condition: {semantic_condition}\n"
                f"Text: {text_to_evaluate}\n"
                "Respond with TRUE or FALSE."
            ),
        },
    ]

    try:
        # For now, only 'openai' provider is supported
        provider = get_api_provider()

        if provider == "openai":
            response = openai_client._call_openai_api(
                messages, model=get_model_name(), temperature=temperature, **kwargs
            )

        else:
            raise SemantifError(f"Unsupported API provider: {provider}")
        
        # Normalize and parse boolean
        normalized = response.strip().lower()
        if normalized.startswith("true"):
            return True
        return False

    except SemantifError:
        raise
