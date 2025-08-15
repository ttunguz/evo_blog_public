"""
Local model client implementation (Ollama/MLX)
Supports both Ollama and MLX backends for local model inference
"""

import os
import time
import json
import subprocess
from typing import Dict, Any, Optional
from .base import ModelClient, ModelResponse


class LocalClient(ModelClient):
    """Client for local models via Ollama or MLX"""
    
    def __init__(self, api_key: str = None, config: Dict = None):
        """
        Initialize local model client
        
        Args:
            api_key: Not used for local models
            config: Configuration including backend type and model
        """
        config = config or {}
        super().__init__(api_key, config)
        
        # Determine backend
        self.backend = config.get('backend', 'ollama')  # 'ollama' or 'mlx'
        
        # Default model
        if self.backend == 'ollama':
            self.default_model = config.get('model', 'qwen2.5:32b')
        else:  # mlx
            self.default_model = config.get('model', 'mlx-community/Qwen2.5-32B-Instruct-4bit')
        
        self.max_tokens = config.get('max_tokens', 2000)
        self.temperature = config.get('temperature', 0.8)
        
        # Check if backend is available
        self._check_backend()
    
    def _check_backend(self):
        """Check if the backend is available and running"""
        if self.backend == 'ollama':
            try:
                # Check if Ollama is running
                result = subprocess.run(
                    ['ollama', 'list'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode != 0:
                    print("Warning: Ollama not running. Start with 'ollama serve'")
            except (subprocess.SubprocessError, FileNotFoundError):
                print("Warning: Ollama not found. Install from https://ollama.ai")
        
        elif self.backend == 'mlx':
            try:
                import mlx
                import mlx_lm
            except ImportError:
                print("Warning: MLX not installed. Install with 'pip install mlx mlx-lm'")
    
    def generate(self, prompt: str, **kwargs) -> ModelResponse:
        """
        Generate content using local model
        
        Args:
            prompt: The input prompt
            **kwargs: Additional parameters
            
        Returns:
            ModelResponse with generated content
        """
        if self.backend == 'ollama':
            return self._generate_ollama(prompt, **kwargs)
        else:
            return self._generate_mlx(prompt, **kwargs)
    
    def _generate_ollama(self, prompt: str, **kwargs) -> ModelResponse:
        """
        Generate using Ollama backend
        
        Args:
            prompt: The input prompt
            **kwargs: Additional parameters
            
        Returns:
            ModelResponse with generated content
        """
        model = kwargs.get('model', self.default_model)
        temperature = kwargs.get('temperature', self.temperature)
        max_tokens = kwargs.get('max_tokens', self.max_tokens)
        system_message = kwargs.get('system_message', None)
        
        # Build full prompt
        if system_message:
            full_prompt = f"{system_message}\n\n{prompt}"
        else:
            full_prompt = prompt
        
        start_time = time.time()
        
        try:
            # Use Ollama API via curl (more reliable than Python client)
            import requests
            
            url = "http://localhost:11434/api/generate"
            
            payload = {
                "model": model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                    "top_p": kwargs.get('top_p', 0.95),
                    "top_k": kwargs.get('top_k', 40)
                }
            }
            
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            
            result = response.json()
            
            latency = time.time() - start_time
            
            # Extract metrics
            content = result.get('response', '')
            total_duration = result.get('total_duration', 0) / 1e9  # Convert ns to seconds
            prompt_eval_count = result.get('prompt_eval_count', 0)
            eval_count = result.get('eval_count', 0)
            total_tokens = prompt_eval_count + eval_count
            
            return ModelResponse(
                content=content,
                model=model,
                tokens_used=total_tokens,
                cost=0,  # Local models have no API cost
                latency_seconds=latency,
                raw_response={
                    'model': model,
                    'created_at': result.get('created_at', ''),
                    'total_duration_ns': result.get('total_duration', 0),
                    'load_duration_ns': result.get('load_duration', 0),
                    'prompt_eval_count': prompt_eval_count,
                    'eval_count': eval_count,
                    'eval_duration_ns': result.get('eval_duration', 0)
                }
            )
            
        except Exception as e:
            # Fallback to command line if API fails
            try:
                result = subprocess.run(
                    ['ollama', 'run', model, full_prompt],
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                if result.returncode == 0:
                    content = result.stdout.strip()
                    latency = time.time() - start_time
                    
                    return ModelResponse(
                        content=content,
                        model=model,
                        tokens_used=len(full_prompt.split()) + len(content.split()),
                        cost=0,
                        latency_seconds=latency,
                        raw_response={'method': 'cli'}
                    )
                else:
                    raise Exception(f"Ollama error: {result.stderr}")
                    
            except Exception as cli_error:
                return ModelResponse(
                    content="",
                    model=model,
                    tokens_used=0,
                    cost=0,
                    latency_seconds=time.time() - start_time,
                    raw_response={},
                    error=f"API error: {str(e)}, CLI error: {str(cli_error)}"
                )
    
    def _generate_mlx(self, prompt: str, **kwargs) -> ModelResponse:
        """
        Generate using MLX backend
        
        Args:
            prompt: The input prompt
            **kwargs: Additional parameters
            
        Returns:
            ModelResponse with generated content
        """
        try:
            import mlx_lm
            
            model = kwargs.get('model', self.default_model)
            temperature = kwargs.get('temperature', self.temperature)
            max_tokens = kwargs.get('max_tokens', self.max_tokens)
            system_message = kwargs.get('system_message', None)
            
            # Build full prompt with proper formatting for Qwen
            if system_message:
                messages = [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ]
            else:
                messages = [{"role": "user", "content": prompt}]
            
            start_time = time.time()
            
            # Load model and tokenizer
            model_obj, tokenizer = mlx_lm.load(model)
            
            # Format prompt for model
            formatted_prompt = tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
            
            # Generate
            response = mlx_lm.generate(
                model_obj,
                tokenizer,
                prompt=formatted_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=kwargs.get('top_p', 0.95)
            )
            
            latency = time.time() - start_time
            
            # Extract content
            content = response.strip()
            
            # Estimate tokens
            input_tokens = len(tokenizer.encode(formatted_prompt))
            output_tokens = len(tokenizer.encode(content))
            total_tokens = input_tokens + output_tokens
            
            return ModelResponse(
                content=content,
                model=model,
                tokens_used=total_tokens,
                cost=0,
                latency_seconds=latency,
                raw_response={
                    'model': model,
                    'backend': 'mlx',
                    'input_tokens': input_tokens,
                    'output_tokens': output_tokens
                }
            )
            
        except Exception as e:
            return ModelResponse(
                content="",
                model=kwargs.get('model', self.default_model),
                tokens_used=0,
                cost=0,
                latency_seconds=time.time() - start_time,
                raw_response={},
                error=str(e)
            )
    
    def calculate_cost(self, tokens_in: int, tokens_out: int) -> float:
        """
        Calculate cost for local generation (always 0)
        
        Args:
            tokens_in: Number of input tokens
            tokens_out: Number of output tokens
            
        Returns:
            0 (local models have no API cost)
        """
        return 0.0
    
    def count_tokens(self, text: str) -> int:
        """
        Estimate token count for local models
        
        Args:
            text: Input text
            
        Returns:
            Estimated token count
        """
        # Simple word-based approximation
        # Most models use ~1.3 tokens per word on average
        words = len(text.split())
        return int(words * 1.3)
    
    def stream_generate(self, prompt: str, **kwargs):
        """
        Generate content with streaming
        
        Args:
            prompt: The input prompt
            **kwargs: Additional parameters
            
        Yields:
            Chunks of generated text
        """
        if self.backend == 'ollama':
            yield from self._stream_ollama(prompt, **kwargs)
        else:
            # MLX doesn't have built-in streaming in the same way
            # Return the full response as a single chunk
            response = self._generate_mlx(prompt, **kwargs)
            yield response.content
    
    def _stream_ollama(self, prompt: str, **kwargs):
        """
        Stream generation using Ollama
        
        Args:
            prompt: The input prompt
            **kwargs: Additional parameters
            
        Yields:
            Chunks of generated text
        """
        import requests
        
        model = kwargs.get('model', self.default_model)
        temperature = kwargs.get('temperature', self.temperature)
        max_tokens = kwargs.get('max_tokens', self.max_tokens)
        system_message = kwargs.get('system_message', None)
        
        # Build full prompt
        if system_message:
            full_prompt = f"{system_message}\n\n{prompt}"
        else:
            full_prompt = prompt
        
        url = "http://localhost:11434/api/generate"
        
        payload = {
            "model": model,
            "prompt": full_prompt,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        try:
            response = requests.post(url, json=payload, stream=True)
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    if 'response' in data:
                        yield data['response']
                    if data.get('done', False):
                        break
                        
        except Exception as e:
            yield f"Error: {str(e)}"
    
    def list_models(self) -> list:
        """
        List available local models
        
        Returns:
            List of available model names
        """
        if self.backend == 'ollama':
            try:
                result = subprocess.run(
                    ['ollama', 'list'],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')[1:]  # Skip header
                    models = []
                    for line in lines:
                        if line:
                            model_name = line.split()[0]
                            models.append(model_name)
                    return models
                    
            except:
                pass
        
        return [self.default_model]
    
    def pull_model(self, model_name: str) -> bool:
        """
        Pull/download a model for local use
        
        Args:
            model_name: Name of the model to pull
            
        Returns:
            True if successful, False otherwise
        """
        if self.backend == 'ollama':
            try:
                print(f"Pulling model {model_name}...")
                result = subprocess.run(
                    ['ollama', 'pull', model_name],
                    capture_output=True,
                    text=True
                )
                return result.returncode == 0
            except:
                return False
        
        return False