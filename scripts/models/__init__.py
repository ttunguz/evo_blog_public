"""
Model integration module for blog post generation
Provides unified interface for all AI models
"""

from .base import ModelClient, ModelResponse
from .claude_client import ClaudeClient
from .openai_client import OpenAIClient
from .gemini_client import GeminiClient
from .local_client import LocalClient

__all__ = [
    'ModelClient',
    'ModelResponse', 
    'ClaudeClient',
    'OpenAIClient',
    'GeminiClient',
    'LocalClient'
]