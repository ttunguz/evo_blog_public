"""
Claude (Anthropic) model client implementation
"""

import os
import time
from typing import Dict, Any, Optional
import anthropic
from .base import ModelClient, ModelResponse


class ClaudeClient(ModelClient):
    """Client for Anthropic's Claude models"""
    
    # Pricing per 1K tokens (as of 2025)
    PRICING = {
        'claude-sonnet-4-20250514': {
            'input': 0.003,   # $3 per 1M input tokens
            'output': 0.015   # $15 per 1M output tokens
        },
        'claude-opus-4-20250805': {
            'input': 0.015,   # $15 per 1M input tokens
            'output': 0.075   # $75 per 1M output tokens
        },
        # Legacy models for compatibility
        'claude-3-5-sonnet-latest': {
            'input': 0.003,
            'output': 0.015
        },
        'claude-3-5-haiku-20241022': {
            'input': 0.00025,  
            'output': 0.00125  
        },
        'claude-3-opus-20240229': {
            'input': 0.015,   
            'output': 0.075   
        }
    }
    
    def __init__(self, api_key: str = None, config: Dict = None):
        """
        Initialize Claude client
        
        Args:
            api_key: Anthropic API key (or from environment)
            config: Additional configuration
        """
        config = config or {}
        super().__init__(api_key, config)
        
        # Get API key from parameter or environment
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("Anthropic API key required")
        
        # Initialize client
        self.client = anthropic.Anthropic(api_key=self.api_key)
        
        # Default model - Use Claude Sonnet 4 as default
        self.default_model = config.get('model', 'claude-sonnet-4-20250514')
        self.max_tokens = config.get('max_tokens', 2000)
        self.temperature = config.get('temperature', 0.7)
    
    def generate(self, prompt: str, **kwargs) -> ModelResponse:
        """
        Generate content using Claude
        
        Args:
            prompt: The input prompt
            **kwargs: Additional parameters (model, temperature, max_tokens, etc.)
            
        Returns:
            ModelResponse with generated content
        """
        model = kwargs.get('model', self.default_model)
        temperature = kwargs.get('temperature', self.temperature)
        max_tokens = kwargs.get('max_tokens', self.max_tokens)
        system_message = kwargs.get('system_message', None)
        
        # Track timing
        start_time = time.time()
        
        try:
            # Build messages
            messages = [{"role": "user", "content": prompt}]
            
            # Make API call with retry
            response = self.retry_with_backoff(
                self._call_api,
                model=model,
                messages=messages,
                system=system_message,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Calculate metrics
            latency = time.time() - start_time
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            total_tokens = input_tokens + output_tokens
            cost = self.calculate_cost_for_model(
                model, input_tokens, output_tokens
            )
            
            return ModelResponse(
                content=response.content[0].text,
                model=model,
                tokens_used=total_tokens,
                cost=cost,
                latency_seconds=latency,
                raw_response={
                    'id': response.id,
                    'model': response.model,
                    'usage': {
                        'input_tokens': input_tokens,
                        'output_tokens': output_tokens
                    }
                }
            )
            
        except Exception as e:
            return ModelResponse(
                content="",
                model=model,
                tokens_used=0,
                cost=0,
                latency_seconds=time.time() - start_time,
                raw_response={},
                error=str(e)
            )
    
    def _call_api(self, **kwargs) -> Any:
        """
        Make the actual API call to Claude
        
        Args:
            **kwargs: API parameters
            
        Returns:
            API response
        """
        # Remove None values
        params = {k: v for k, v in kwargs.items() if v is not None}
        
        return self.client.messages.create(**params)
    
    def calculate_cost(self, tokens_in: int, tokens_out: int) -> float:
        """
        Calculate cost for Claude generation
        
        Args:
            tokens_in: Number of input tokens
            tokens_out: Number of output tokens
            
        Returns:
            Cost in USD
        """
        return self.calculate_cost_for_model(
            self.default_model, tokens_in, tokens_out
        )
    
    def calculate_cost_for_model(self, model: str, 
                                tokens_in: int, tokens_out: int) -> float:
        """
        Calculate cost for specific Claude model
        
        Args:
            model: Model name
            tokens_in: Number of input tokens
            tokens_out: Number of output tokens
            
        Returns:
            Cost in USD
        """
        if model not in self.PRICING:
            # Default to Sonnet pricing if model not found
            model = 'claude-3-5-sonnet-latest'
            
        pricing = self.PRICING[model]
        
        # Convert to cost (pricing is per 1K tokens)
        input_cost = (tokens_in / 1000) * pricing['input']
        output_cost = (tokens_out / 1000) * pricing['output']
        
        return round(input_cost + output_cost, 6)
    
    def count_tokens(self, text: str) -> int:
        """
        Estimate token count for Claude
        More accurate than base approximation
        
        Args:
            text: Input text
            
        Returns:
            Estimated token count
        """
        # Claude uses a similar tokenization to ~3.5 characters per token
        return len(text) // 3
    
    def stream_generate(self, prompt: str, **kwargs):
        """
        Generate content with streaming (for future implementation)
        
        Args:
            prompt: The input prompt
            **kwargs: Additional parameters
            
        Yields:
            Chunks of generated text
        """
        model = kwargs.get('model', self.default_model)
        temperature = kwargs.get('temperature', self.temperature)
        max_tokens = kwargs.get('max_tokens', self.max_tokens)
        system_message = kwargs.get('system_message', None)
        
        messages = [{"role": "user", "content": prompt}]
        
        with self.client.messages.stream(
            model=model,
            messages=messages,
            system=system_message,
            temperature=temperature,
            max_tokens=max_tokens
        ) as stream:
            for text in stream.text_stream:
                yield text