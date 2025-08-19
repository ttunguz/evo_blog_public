#!/usr/bin/env python3
"""
Environment variable loader for evo_blog_public
"""

import os
from pathlib import Path

def load_env_file(env_path: str = ".env"):
    """Load environment variables from .env file"""
    env_file = Path(env_path)
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

def ensure_env_vars():
    """Ensure required environment variables are set"""
    required_vars = [
        'ANTHROPIC_API_KEY',
        'OPENAI_API_KEY', 
        'GOOGLE_API_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️  Missing required environment variables: {', '.join(missing_vars)}")
        print("Please copy .env.example to .env and fill in your API keys")
        return False
    
    return True

# Auto-load .env file when imported
load_env_file()