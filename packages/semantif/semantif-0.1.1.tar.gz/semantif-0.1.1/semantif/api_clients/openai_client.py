"""
HTTP OpenAI API client wrapper for semantif library.
Uses standard library for chat completions and error translation.
"""

import json
from typing import List, Dict, Any
from urllib import request, error

from ..config import get_api_key, get_model_name
from ..errors import SemantifError

def _call_openai_api(
    messages: List[Dict[str, Any]],
    model: str = None,
    temperature: float = 0.0,
    **kwargs: Any
) -> str:
    """
    Call OpenAI chat completion API with provided messages.
    Returns the content of the first choice.
    Raises SemantifError on API errors.
    """
    api_key = get_api_key()
    model_to_use = model or get_model_name()
    url = "https://api.openai.com/v1/chat/completions"
    payload = {"model": model_to_use, "messages": messages, "temperature": temperature}
    payload.update(kwargs or {})
    data = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    req = request.Request(url, data=data, headers=headers, method="POST")
    try:
        with request.urlopen(req) as resp:
            resp_data = resp.read().decode("utf-8")
            obj = json.loads(resp_data)
            return obj["choices"][0]["message"]["content"]
    except error.HTTPError as e:
        try:
            msg = e.read().decode("utf-8")
        except Exception:
            msg = str(e)
        if e.code in (401, 429):
            raise SemantifError(f"OpenAI API error: {msg}")
        
        raise SemantifError(f"Unexpected error calling OpenAI API: {msg}")
    
    except Exception as e:
        
        raise SemantifError(f"Unexpected error calling OpenAI API: {str(e)}")
