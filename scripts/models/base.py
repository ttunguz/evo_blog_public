"""
Base class for all model clients
Defines the interface that all model implementations must follow
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import time


@dataclass
class ModelResponse:
    """Standardized response from any model"""
    content: str
    model: str
    tokens_used: int
    cost: float
    latency_seconds: float
    raw_response: Dict[str, Any]
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'content': self.content,
            'model': self.model,
            'tokens_used': self.tokens_used,
            'cost': self.cost,
            'latency_seconds': self.latency_seconds,
            'error': self.error,
            'timestamp': datetime.now().isoformat()
        }


class ModelClient(ABC):
    """Abstract base class for all model clients"""
    
    def __init__(self, api_key: str = None, config: Dict = None):
        """
        Initialize model client
        
        Args:
            api_key: API key for the service
            config: Additional configuration parameters
        """
        self.api_key = api_key
        self.config = config or {}
        self.retry_attempts = self.config.get('retry_attempts', 3)
        self.retry_delay = self.config.get('retry_delay', 2)
        
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> ModelResponse:
        """
        Generate content from the model
        
        Args:
            prompt: The input prompt
            **kwargs: Additional model-specific parameters
            
        Returns:
            ModelResponse object with generated content
        """
        pass
    
    @abstractmethod
    def calculate_cost(self, tokens_in: int, tokens_out: int) -> float:
        """
        Calculate the cost for a generation
        
        Args:
            tokens_in: Number of input tokens
            tokens_out: Number of output tokens
            
        Returns:
            Cost in USD
        """
        pass
    
    def retry_with_backoff(self, func, *args, **kwargs):
        """
        Retry a function with exponential backoff
        
        Args:
            func: Function to retry
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Function result
            
        Raises:
            Exception: If all retries fail
        """
        last_exception = None
        
        for attempt in range(self.retry_attempts):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < self.retry_attempts - 1:
                    wait_time = self.retry_delay * (2 ** attempt)
                    print(f"  Retry {attempt + 1}/{self.retry_attempts} after {wait_time}s...")
                    time.sleep(wait_time)
                    
        raise last_exception
    
    def count_tokens(self, text: str) -> int:
        """
        Estimate token count for text
        Simple approximation - override for model-specific counting
        
        Args:
            text: Input text
            
        Returns:
            Estimated token count
        """
        # Simple approximation: ~4 characters per token
        return len(text) // 4
    
    def validate_response(self, response: Any) -> bool:
        """
        Validate that the response is valid
        Override for model-specific validation
        
        Args:
            response: Raw response from the API
            
        Returns:
            True if valid, False otherwise
        """
        return response is not None
    
    def format_prompt(self, prompt: str, system_message: str = None) -> str:
        """
        Format prompt with optional system message
        Override for model-specific formatting
        
        Args:
            prompt: User prompt
            system_message: Optional system message
            
        Returns:
            Formatted prompt
        """
        if system_message:
            return f"{system_message}\n\n{prompt}"
        return prompt