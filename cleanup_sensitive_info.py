#!/usr/bin/env python3
"""
Cleanup script to remove sensitive information from evo_blog_public
"""

import os
import re
from pathlib import Path

def replace_in_file(file_path: Path, replacements: list):
    """Replace patterns in a file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        for pattern, replacement in replacements:
            content = re.sub(pattern, replacement, content)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ Updated {file_path}")
        
    except Exception as e:
        print(f"⚠️  Error processing {file_path}: {e}")

def main():
    base_dir = Path("./_public")
    
    # Patterns to replace
    replacements = [
        # Personal paths
        (r'./', './'),
        (r'./', './'),
        (r'./content', os.getenv('BLOG_CONTENT_PATH', './content')),
        (r'./content/post', os.getenv('BLOG_CONTENT_PATH', './content/post')),
        (r'./content/blog_indexer.py', os.getenv('BLOG_INDEXER_PATH', './content/blog_indexer.py')),
        
        # API key patterns
        (r'"anthropic_api_key":\s*"[^"]*"', '"anthropic_api_key": os.getenv("ANTHROPIC_API_KEY")'),
        (r'"openai_api_key":\s*"[^"]*"', '"openai_api_key": os.getenv("OPENAI_API_KEY")'),
        (r'"google_api_key":\s*"[^"]*"', '"google_api_key": os.getenv("GOOGLE_API_KEY")'),
        
        # Path patterns
        (r'Path\.home\(\)\s*/\s*"Documents"\s*/\s*"evo_blog"', 'Path(os.getenv("CONFIG_DIR", "./config"))'),
        (r'Path\.home\(\)\s*/\s*"Documents"\s*/\s*"coding"\s*/\s*"evo_blog"', 'Path("./")'),
        (r'Path\(".//iterative_improvements"\)', 'Path(os.getenv("OUTPUT_DIR", "./iterative_improvements"))'),
        (r'Path\(f".//generations/{timestamp}"\)', 'Path(os.getenv("OUTPUT_DIR", "./generations")) / f"{timestamp}"'),
        
        # Remove personal references in examples
        (r'[DATA_PATH_PLACEHOLDER]"]*', '[DATA_PATH_PLACEHOLDER]'),
    ]
    
    # Files to process
    python_files = list(base_dir.rglob("*.py"))
    json_files = list(base_dir.rglob("*.json"))
    md_files = list(base_dir.rglob("*.md"))
    
    all_files = python_files + json_files + md_files
    
    print(f"Processing {len(all_files)} files...")
    
    for file_path in all_files:
        if '.venv' not in str(file_path) and '__pycache__' not in str(file_path):
            replace_in_file(file_path, replacements)
    
    print("\n✅ Cleanup complete!")
    print("Next steps:")
    print("1. Copy .env.example to .env and fill in your API keys")
    print("2. Update paths in .env to match your setup")
    print("3. Review the cleaned files for any remaining sensitive information")

if __name__ == "__main__":
    main()