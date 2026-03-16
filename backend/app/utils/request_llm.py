"""
Helper to create an LLMClient from the current request's headers.

The frontend sends the user's API key, base URL, and model choice
via X-LLM-* headers on every request. This helper reads those headers
and falls back to server-side .env configuration if not provided.
"""

from flask import request
from .llm_client import LLMClient
from ..config import Config


def get_llm_client_from_request() -> LLMClient:
    """
    Build an LLMClient using the user's settings from request headers,
    falling back to server-side config.
    """
    api_key = request.headers.get('X-LLM-API-Key') or Config.LLM_API_KEY
    base_url = request.headers.get('X-LLM-Base-URL') or Config.LLM_BASE_URL
    model = request.headers.get('X-LLM-Model') or Config.LLM_MODEL_NAME

    return LLMClient(api_key=api_key, base_url=base_url, model=model)
