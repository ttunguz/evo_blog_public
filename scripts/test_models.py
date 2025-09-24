#!/usr/bin/env python3
"""
Test script for model integrations
Verifies that all model clients work correctly
"""

import os
import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from models import ClaudeClient, OpenAIClient, GeminiClient, LocalClient


def load_api_keys():
    """Load API keys from config file or environment"""
    config_path = Path(os.getenv("CONFIG_DIR", "./config")) / "config" / "model_configs.json"
    
    if config_path.exists():
        with open(config_path, 'r') as f:
            return json.load(f)
    else:
        # Create template config file
        template = {
            "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY", "your-anthropic-key-here"),
            "openai_api_key": os.getenv("OPENAI_API_KEY", "your-openai-key-here"),
            "google_api_key": os.getenv("GOOGLE_API_KEY", "your-google-key-here"),
            "note": "Replace with your actual API keys or set as environment variables"
        }
        
        with open(config_path, 'w') as f:
            json.dump(template, f, indent=2)
        
        print(f"Created template config at: {config_path}")
        print("Please add your API keys to the config file or set them as environment variables")
        return template


def test_claude():
    """Test Claude client"""
    print("\n" + "="*50)
    print("Testing Claude Client")
    print("="*50)
    
    try:
        config = load_api_keys()
        client = ClaudeClient(
            api_key=config.get('anthropic_api_key'),
            config={'model': 'claude-3-5-sonnet-latest'}
        )
        
        prompt = "Write a one-paragraph summary about the importance of testing in software development."
        
        print("Sending prompt to Claude...")
        response = client.generate(prompt, temperature=0.5, max_tokens=150)
        
        if response.error:
            print(f"❌ Error: {response.error}")
            return False
        
        print(f"✅ Success!")
        print(f"Model: {response.model}")
        print(f"Tokens: {response.tokens_used}")
        print(f"Cost: ${response.cost:.4f}")
        print(f"Latency: {response.latency_seconds:.2f}s")
        print(f"\nContent preview: {response.content[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed: {str(e)}")
        return False


def test_openai():
    """Test OpenAI client"""
    print("\n" + "="*50)
    print("Testing OpenAI Client")
    print("="*50)
    
    try:
        config = load_api_keys()
        client = OpenAIClient(
            api_key=config.get('openai_api_key'),
            config={'model': 'gpt-4-turbo-preview'}
        )
        
        prompt = "Write a one-paragraph summary about the benefits of continuous integration."
        
        print("Sending prompt to GPT-4...")
        response = client.generate(prompt, temperature=0.5, max_tokens=150)
        
        if response.error:
            print(f"❌ Error: {response.error}")
            return False
        
        print(f"✅ Success!")
        print(f"Model: {response.model}")
        print(f"Tokens: {response.tokens_used}")
        print(f"Cost: ${response.cost:.4f}")
        print(f"Latency: {response.latency_seconds:.2f}s")
        print(f"\nContent preview: {response.content[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed: {str(e)}")
        return False


def test_gemini():
    """Test Gemini client"""
    print("\n" + "="*50)
    print("Testing Gemini Client")
    print("="*50)
    
    try:
        config = load_api_keys()
        client = GeminiClient(
            api_key=config.get('google_api_key'),
            config={'model': 'gemini-1.5-pro'}  # Using 1.5 Pro as placeholder for 2.5
        )
        
        prompt = "Write a one-paragraph summary about the advantages of microservices architecture."
        
        print("Sending prompt to Gemini...")
        response = client.generate(prompt, temperature=0.5, max_output_tokens=150)
        
        if response.error:
            print(f"❌ Error: {response.error}")
            return False
        
        print(f"✅ Success!")
        print(f"Model: {response.model}")
        print(f"Tokens: {response.tokens_used}")
        print(f"Cost: ${response.cost:.4f}")
        print(f"Latency: {response.latency_seconds:.2f}s")
        print(f"\nContent preview: {response.content[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed: {str(e)}")
        return False


def test_local():
    """Test local model client"""
    print("\n" + "="*50)
    print("Testing Local Model Client (Ollama)")
    print("="*50)
    
    try:
        # First check if Ollama is available
        import subprocess
        try:
            result = subprocess.run(['ollama', 'list'], capture_output=True, timeout=2)
            if result.returncode != 0:
                print("⚠️  Ollama not running. Start with 'ollama serve'")
                return False
        except:
            print("⚠️  Ollama not installed. Install from https://ollama.ai")
            return False
        
        client = LocalClient(config={
            'backend': 'ollama',
            'model': 'llama3.2:3b'  # Small model for testing
        })
        
        # Check if model exists
        models = client.list_models()
        print(f"Available models: {models}")
        
        if 'llama3.2:3b' not in str(models):
            print("Pulling llama3.2:3b for testing...")
            if not client.pull_model('llama3.2:3b'):
                print("Failed to pull model")
                return False
        
        prompt = "Write a one-paragraph summary about version control systems."
        
        print("Sending prompt to local model...")
        response = client.generate(prompt, temperature=0.5, max_tokens=150)
        
        if response.error:
            print(f"❌ Error: {response.error}")
            return False
        
        print(f"✅ Success!")
        print(f"Model: {response.model}")
        print(f"Tokens: {response.tokens_used}")
        print(f"Cost: ${response.cost:.4f} (free - local)")
        print(f"Latency: {response.latency_seconds:.2f}s")
        print(f"\nContent preview: {response.content[:200]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed: {str(e)}")
        return False


def test_all():
    """Test all model clients"""
    print("\n🚀 Testing All Model Integrations")
    print("="*60)
    
    results = {
        'Claude': False,
        'OpenAI': False,
        'Gemini': False,
        'Local': False
    }
    
    # Test each client
    results['Claude'] = test_claude()
    results['OpenAI'] = test_openai()
    results['Gemini'] = test_gemini()
    results['Local'] = test_local()
    
    # Summary
    print("\n" + "="*60)
    print("📊 Test Results Summary")
    print("="*60)
    
    for model, success in results.items():
        status = "✅ Working" if success else "❌ Failed"
        print(f"{model:10} : {status}")
    
    working_count = sum(results.values())
    print(f"\n{working_count}/{len(results)} models working")
    
    if working_count == 0:
        print("\n⚠️  No models working. Please check:")
        print("1. API keys in config/model_configs.json")
        print("2. Internet connection")
        print("3. Ollama installation for local models")
    elif working_count < len(results):
        print("\n⚠️  Some models not working. Check API keys for failed models.")
    else:
        print("\n🎉 All models working successfully!")


def quick_test(model_name: str):
    """Quick test of a specific model"""
    
    prompt = "Write one sentence about artificial intelligence."
    
    if model_name.lower() == 'claude':
        config = load_api_keys()
        client = ClaudeClient(api_key=config.get('anthropic_api_key'))
    elif model_name.lower() == 'openai' or model_name.lower() == 'gpt':
        config = load_api_keys()
        client = OpenAIClient(api_key=config.get('openai_api_key'))
    elif model_name.lower() == 'gemini':
        config = load_api_keys()
        client = GeminiClient(api_key=config.get('google_api_key'))
    elif model_name.lower() == 'local':
        client = LocalClient(config={'backend': 'ollama'})
    else:
        print(f"Unknown model: {model_name}")
        print("Options: claude, openai, gemini, local")
        return
    
    print(f"\nTesting {model_name}...")
    response = client.generate(prompt, max_tokens=50)
    
    if response.error:
        print(f"Error: {response.error}")
    else:
        print(f"Response: {response.content}")
        print(f"Cost: ${response.cost:.4f}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test model integrations")
    parser.add_argument('--model', help="Test specific model (claude/openai/gemini/local)")
    parser.add_argument('--quick', action='store_true', help="Run quick test")
    
    args = parser.parse_args()
    
    if args.model:
        quick_test(args.model)
    else:
        test_all()