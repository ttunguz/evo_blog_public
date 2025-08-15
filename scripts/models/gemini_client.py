"""
Google Gemini model client implementation
"""

import os
import time
from typing import Dict, Any, Optional
import google.generativeai as genai
from .base import ModelClient, ModelResponse


class GeminiClient(ModelClient):
    """Client for Google's Gemini models"""
    
    # Pricing per 1K tokens (as of 2024)
    # Note: Gemini pricing varies by input size
    PRICING = {
        'gemini-2.0-flash-exp': {
            'input': 0.0,     # Free during experimental phase
            'output': 0.0     # Free during experimental phase
        },
        'gemini-1.5-pro': {
            'input_under_128k': 0.00125,  # $1.25 per 1M tokens
            'input_over_128k': 0.0025,    # $2.50 per 1M tokens
            'output_under_128k': 0.005,   # $5.00 per 1M tokens
            'output_over_128k': 0.01,     # $10.00 per 1M tokens
        },
        'gemini-1.5-flash': {
            'input_under_128k': 0.000075, # $0.075 per 1M tokens
            'input_over_128k': 0.00015,   # $0.15 per 1M tokens
            'output_under_128k': 0.0003,  # $0.30 per 1M tokens
            'output_over_128k': 0.0006,   # $0.60 per 1M tokens
        },
        'gemini-2.5-pro': {  # Gemini 2.5 Pro pricing
            'input': 0.002,    # $2 per 1M tokens (estimated)
            'output': 0.008    # $8 per 1M tokens (estimated)
        }
    }
    
    # Safety settings for content generation
    SAFETY_SETTINGS = [
        {
            "category": "HARM_CATEGORY_HARASSMENT",
            "threshold": "BLOCK_NONE"
        },
        {
            "category": "HARM_CATEGORY_HATE_SPEECH",
            "threshold": "BLOCK_NONE"
        },
        {
            "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
            "threshold": "BLOCK_NONE"
        },
        {
            "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
            "threshold": "BLOCK_NONE"
        }
    ]
    
    def __init__(self, api_key: str = None, config: Dict = None):
        """
        Initialize Gemini client
        
        Args:
            api_key: Google API key (or from environment)
            config: Additional configuration
        """
        config = config or {}
        super().__init__(api_key, config)
        
        # Get API key from parameter or environment
        self.api_key = api_key or os.getenv('GOOGLE_API_KEY')
        if not self.api_key:
            raise ValueError("Google API key required")
        
        # Configure the SDK
        genai.configure(api_key=self.api_key)
        
        # Default model - Use Gemini 2.5 Pro as default
        self.default_model = config.get('model', 'gemini-2.5-pro')
        self.max_tokens = config.get('max_output_tokens', 2000)
        self.temperature = config.get('temperature', 0.7)
        
        # Initialize model
        self.model = None
        self._initialize_model(self.default_model)
    
    def _initialize_model(self, model_name: str):
        """
        Initialize or switch to a different Gemini model
        
        Args:
            model_name: Name of the model to use
        """
        generation_config = genai.GenerationConfig(
            temperature=self.temperature,
            top_p=self.config.get('top_p', 0.95),
            top_k=self.config.get('top_k', 40),
            max_output_tokens=self.max_tokens,
        )
        
        # Map our naming to Google's naming
        actual_model = model_name  # Use the model name directly now that 2.5 Pro is available
        
        self.model = genai.GenerativeModel(
            model_name=actual_model,
            generation_config=generation_config,
            safety_settings=self.SAFETY_SETTINGS
        )
    
    def generate(self, prompt: str, **kwargs) -> ModelResponse:
        """
        Generate content using Gemini
        
        Args:
            prompt: The input prompt
            **kwargs: Additional parameters (model, temperature, max_tokens, etc.)
            
        Returns:
            ModelResponse with generated content
        """
        model_name = kwargs.get('model', self.default_model)
        temperature = kwargs.get('temperature', self.temperature)
        max_tokens = kwargs.get('max_output_tokens', self.max_tokens)
        system_message = kwargs.get('system_message', None)
        
        # Update model if different
        if model_name != self.default_model:
            self._initialize_model(model_name)
        
        # Update generation config if parameters changed
        if temperature != self.temperature or max_tokens != self.max_tokens:
            # Re-initialize with new config
            self.temperature = temperature
            self.max_tokens = max_tokens
            self._initialize_model(model_name)
        
        # Combine system message with prompt if provided
        if system_message:
            full_prompt = f"{system_message}\n\n{prompt}"
        else:
            full_prompt = prompt
        
        # Track timing
        start_time = time.time()
        
        try:
            # Make API call with retry
            response = self.retry_with_backoff(
                self._call_api,
                full_prompt
            )
            
            # Calculate metrics
            latency = time.time() - start_time
            
            # Extract content
            content = response.text
            
            # Estimate tokens (Gemini doesn't always provide token counts)
            input_tokens = self.count_tokens(full_prompt)
            output_tokens = self.count_tokens(content)
            total_tokens = input_tokens + output_tokens
            
            # Calculate cost
            cost = self.calculate_cost_for_model(
                model_name, input_tokens, output_tokens
            )
            
            return ModelResponse(
                content=content,
                model=model_name,
                tokens_used=total_tokens,
                cost=cost,
                latency_seconds=latency,
                raw_response={
                    'model': model_name,
                    'finish_reason': response.candidates[0].finish_reason.name if response.candidates else 'UNKNOWN',
                    'safety_ratings': [
                        {
                            'category': rating.category.name,
                            'probability': rating.probability.name
                        }
                        for rating in response.candidates[0].safety_ratings
                    ] if response.candidates else []
                }
            )
            
        except Exception as e:
            return ModelResponse(
                content="",
                model=model_name,
                tokens_used=0,
                cost=0,
                latency_seconds=time.time() - start_time,
                raw_response={},
                error=str(e)
            )
    
    def _call_api(self, prompt: str) -> Any:
        """
        Make the actual API call to Gemini
        
        Args:
            prompt: The input prompt
            
        Returns:
            API response
        """
        return self.model.generate_content(prompt)
    
    def calculate_cost(self, tokens_in: int, tokens_out: int) -> float:
        """
        Calculate cost for Gemini generation
        
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
        Calculate cost for specific Gemini model
        
        Args:
            model: Model name
            tokens_in: Number of input tokens
            tokens_out: Number of output tokens
            
        Returns:
            Cost in USD
        """
        if model not in self.PRICING:
            # Default to 1.5 Pro pricing if model not found
            model = 'gemini-1.5-pro'
        
        pricing = self.PRICING[model]
        
        # Handle different pricing structures
        if model in ['gemini-1.5-pro', 'gemini-1.5-flash']:
            # These models have tiered pricing based on context length
            if tokens_in < 128000:
                input_rate = pricing['input_under_128k']
                output_rate = pricing['output_under_128k']
            else:
                input_rate = pricing['input_over_128k']
                output_rate = pricing['output_over_128k']
        else:
            # Simple pricing structure
            input_rate = pricing.get('input', 0)
            output_rate = pricing.get('output', 0)
        
        # Convert to cost (pricing is per 1K tokens)
        input_cost = (tokens_in / 1000) * input_rate
        output_cost = (tokens_out / 1000) * output_rate
        
        return round(input_cost + output_cost, 6)
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens for Gemini
        Uses the model's count_tokens method for accuracy
        
        Args:
            text: Input text
            
        Returns:
            Token count
        """
        try:
            # Use Gemini's built-in token counter
            return self.model.count_tokens(text).total_tokens
        except:
            # Fallback to approximation
            # Gemini uses similar tokenization to ~4 characters per token
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
        model_name = kwargs.get('model', self.default_model)
        system_message = kwargs.get('system_message', None)
        
        # Update model if different
        if model_name != self.default_model:
            self._initialize_model(model_name)
        
        # Combine system message with prompt if provided
        if system_message:
            full_prompt = f"{system_message}\n\n{prompt}"
        else:
            full_prompt = prompt
        
        # Generate with streaming
        response = self.model.generate_content(full_prompt, stream=True)
        
        for chunk in response:
            if chunk.text:
                yield chunk.text
    
    def generate_with_images(self, prompt: str, images: list, **kwargs) -> ModelResponse:
        """
        Generate content with image inputs (multimodal)
        
        Args:
            prompt: The text prompt
            images: List of image paths or PIL images
            **kwargs: Additional parameters
            
        Returns:
            ModelResponse with generated content
        """
        from PIL import Image
        
        # Prepare inputs
        inputs = [prompt]
        
        for image in images:
            if isinstance(image, str):
                # Load image from path
                img = Image.open(image)
            else:
                img = image
            inputs.append(img)
        
        start_time = time.time()
        
        try:
            response = self.model.generate_content(inputs)
            
            content = response.text
            latency = time.time() - start_time
            
            # Estimate tokens
            total_tokens = self.count_tokens(prompt) + self.count_tokens(content)
            
            return ModelResponse(
                content=content,
                model=self.default_model,
                tokens_used=total_tokens,
                cost=0,  # Cost calculation for multimodal is complex
                latency_seconds=latency,
                raw_response={
                    'model': self.default_model,
                    'multimodal': True,
                    'image_count': len(images)
                }
            )
            
        except Exception as e:
            return ModelResponse(
                content="",
                model=self.default_model,
                tokens_used=0,
                cost=0,
                latency_seconds=time.time() - start_time,
                raw_response={},
                error=str(e)
            )