"""
OpenAI (GPT) model client implementation
"""

import os
import time
from typing import Dict, Any, Optional
import openai
from openai import OpenAI
from .base import ModelClient, ModelResponse


class OpenAIClient(ModelClient):
    """Client for OpenAI's GPT models"""
    
    # Pricing per 1K tokens (as of 2025)
    PRICING = {
        'gpt-4.1': {
            'input': 0.002,   # $2 per 1M input tokens
            'output': 0.008   # $8 per 1M output tokens
        },
        'gpt-4.1-mini': {
            'input': 0.0004,  # $0.40 per 1M input tokens
            'output': 0.0016  # $1.60 per 1M output tokens
        },
        'gpt-4.1-nano': {
            'input': 0.0001,  # $0.10 per 1M input tokens
            'output': 0.0004  # $0.40 per 1M output tokens
        },
        # Legacy models for compatibility
        'gpt-4-turbo-preview': {
            'input': 0.01,    
            'output': 0.03    
        },
        'gpt-4': {
            'input': 0.03,    
            'output': 0.06    
        },
        'gpt-4o': {
            'input': 0.005,   
            'output': 0.015   
        },
        'gpt-4o-mini': {
            'input': 0.00015, 
            'output': 0.0006  
        },
        'gpt-3.5-turbo': {
            'input': 0.0005,  
            'output': 0.0015  
        }
    }
    
    def __init__(self, api_key: str = None, config: Dict = None):
        """
        Initialize OpenAI client
        
        Args:
            api_key: OpenAI API key (or from environment)
            config: Additional configuration
        """
        config = config or {}
        super().__init__(api_key, config)
        
        # Get API key from parameter or environment
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key required")
        
        # Initialize client
        self.client = OpenAI(api_key=self.api_key)
        
        # Default model - Use GPT-4.1 as default
        self.default_model = config.get('model', 'gpt-4.1')
        self.max_tokens = config.get('max_tokens', 2000)
        self.temperature = config.get('temperature', 0.7)
    
    def generate(self, prompt: str, **kwargs) -> ModelResponse:
        """
        Generate content using GPT
        
        Args:
            prompt: The input prompt
            **kwargs: Additional parameters (model, temperature, max_tokens, etc.)
            
        Returns:
            ModelResponse with generated content
        """
        model = kwargs.get('model', self.default_model)
        temperature = kwargs.get('temperature', self.temperature)
        max_tokens = kwargs.get('max_tokens', self.max_tokens)
        system_message = kwargs.get('system_message', 
                                    "You are a thoughtful technology analyst and writer.")
        
        # Track timing
        start_time = time.time()
        
        try:
            # Build messages
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt})
            
            # Make API call with retry
            response = self.retry_with_backoff(
                self._call_api,
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=kwargs.get('top_p', 1.0),
                frequency_penalty=kwargs.get('frequency_penalty', 0),
                presence_penalty=kwargs.get('presence_penalty', 0)
            )
            
            # Calculate metrics
            latency = time.time() - start_time
            
            # Extract token usage
            usage = response.usage
            input_tokens = usage.prompt_tokens
            output_tokens = usage.completion_tokens
            total_tokens = usage.total_tokens
            
            cost = self.calculate_cost_for_model(
                model, input_tokens, output_tokens
            )
            
            return ModelResponse(
                content=response.choices[0].message.content,
                model=model,
                tokens_used=total_tokens,
                cost=cost,
                latency_seconds=latency,
                raw_response={
                    'id': response.id,
                    'model': response.model,
                    'created': response.created,
                    'usage': {
                        'prompt_tokens': input_tokens,
                        'completion_tokens': output_tokens,
                        'total_tokens': total_tokens
                    },
                    'finish_reason': response.choices[0].finish_reason
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
        Make the actual API call to OpenAI
        
        Args:
            **kwargs: API parameters
            
        Returns:
            API response
        """
        return self.client.chat.completions.create(**kwargs)
    
    def calculate_cost(self, tokens_in: int, tokens_out: int) -> float:
        """
        Calculate cost for GPT generation
        
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
        Calculate cost for specific GPT model
        
        Args:
            model: Model name
            tokens_in: Number of input tokens
            tokens_out: Number of output tokens
            
        Returns:
            Cost in USD
        """
        # Handle model name variations
        if 'gpt-4-turbo' in model or 'gpt-4-1106' in model:
            model = 'gpt-4-turbo-preview'
        elif 'gpt-4o-mini' in model:
            model = 'gpt-4o-mini'
        elif 'gpt-4o' in model:
            model = 'gpt-4o'
        elif 'gpt-4' in model:
            model = 'gpt-4'
        elif 'gpt-3.5' in model:
            model = 'gpt-3.5-turbo'
            
        if model not in self.PRICING:
            # Default to GPT-4 Turbo pricing if model not found
            model = 'gpt-4-turbo-preview'
            
        pricing = self.PRICING[model]
        
        # Convert to cost (pricing is per 1K tokens)
        input_cost = (tokens_in / 1000) * pricing['input']
        output_cost = (tokens_out / 1000) * pricing['output']
        
        return round(input_cost + output_cost, 6)
    
    def count_tokens(self, text: str) -> int:
        """
        Estimate token count for GPT
        Uses tiktoken for accurate counting
        
        Args:
            text: Input text
            
        Returns:
            Estimated token count
        """
        try:
            import tiktoken
            
            # Get encoding for the model
            if 'gpt-4' in self.default_model:
                encoding = tiktoken.encoding_for_model('gpt-4')
            else:
                encoding = tiktoken.encoding_for_model('gpt-3.5-turbo')
                
            return len(encoding.encode(text))
        except ImportError:
            # Fallback to approximation if tiktoken not installed
            # GPT uses ~4 characters per token on average
            return len(text) // 4
    
    def stream_generate(self, prompt: str, **kwargs):
        """
        Generate content with streaming
        
        Args:
            prompt: The input prompt
            **kwargs: Additional parameters
            
        Yields:
            Chunks of generated text
        """
        model = kwargs.get('model', self.default_model)
        temperature = kwargs.get('temperature', self.temperature)
        max_tokens = kwargs.get('max_tokens', self.max_tokens)
        system_message = kwargs.get('system_message',
                                  "You are a thoughtful technology analyst and writer.")
        
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})
        
        stream = self.client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    def generate_with_functions(self, prompt: str, functions: list, **kwargs) -> ModelResponse:
        """
        Generate content with function calling capability
        
        Args:
            prompt: The input prompt
            functions: List of function definitions
            **kwargs: Additional parameters
            
        Returns:
            ModelResponse with generated content
        """
        model = kwargs.get('model', self.default_model)
        
        # Ensure model supports function calling
        if 'gpt-3.5' in model or 'gpt-4' not in model:
            model = 'gpt-4-turbo-preview'
        
        messages = [{"role": "user", "content": prompt}]
        
        start_time = time.time()
        
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                functions=functions,
                function_call=kwargs.get('function_call', 'auto'),
                temperature=kwargs.get('temperature', self.temperature),
                max_tokens=kwargs.get('max_tokens', self.max_tokens)
            )
            
            latency = time.time() - start_time
            
            # Handle function call response
            message = response.choices[0].message
            
            if message.function_call:
                content = f"Function: {message.function_call.name}\nArguments: {message.function_call.arguments}"
            else:
                content = message.content
            
            return ModelResponse(
                content=content,
                model=model,
                tokens_used=response.usage.total_tokens,
                cost=self.calculate_cost_for_model(
                    model,
                    response.usage.prompt_tokens,
                    response.usage.completion_tokens
                ),
                latency_seconds=latency,
                raw_response={
                    'id': response.id,
                    'function_call': message.function_call.dict() if message.function_call else None
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