#!/usr/bin/env python3
"""
Setup script for the Evolutionary Blog Post Generator
Creates necessary directories and initializes configuration
"""

import os
import json
import shutil
from datetime import datetime
from pathlib import Path

def setup_directories():
    """Create the complete directory structure"""
    base_dir = Path(os.getenv("CONFIG_DIR", "./config"))
    
    # Main directories
    directories = [
        "config",
        "config/style_reference",
        "templates",
        "generations",
        "scripts",
        "evaluation",
        "utils"
    ]
    
    for dir_path in directories:
        full_path = base_dir / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"✓ Created: {full_path}")
    
    return base_dir

def create_gitignore(base_dir):
    """Create .gitignore file"""
    gitignore_content = """# API Keys and Secrets
config/model_configs.json
.env
*.key

# Generated content
generations/*/raw_outputs/
generations/*/scores/

# Cache
__pycache__/
*.pyc
.cache/

# MacOS
.DS_Store

# Editor
.vscode/
.idea/
*.swp
"""
    
    gitignore_path = base_dir / ".gitignore"
    gitignore_path.write_text(gitignore_content)
    print(f"✓ Created .gitignore")

def create_readme(base_dir):
    """Create README with usage instructions"""
    readme_content = """# Evolutionary Blog Post Generator

## Overview
Advanced blog post generation system using multiple AI models with iterative refinement.

## Quick Start

### 1. Generate a blog post
```bash
python generate_blog.py --topic "Your Topic" --source notes.md
```

### 2. Review generations
```bash
python review_posts.py --session 2025-08-13_your_topic
```

### 3. Export final post
```bash
python export_post.py --session 2025-08-13_your_topic --format markdown
```

## File Structure
- `config/` - Configuration and settings
- `templates/` - Blog post templates
- `generations/` - All generated content
- `scripts/` - Main execution scripts
- `evaluation/` - Scoring and evaluation tools
- `utils/` - Helper utilities

## Models Used
- Claude 3.5 Sonnet
- GPT-4
- Gemini 2.5 Pro
- Local Qwen 2.5

## Configuration
Edit `config/global_settings.json` to customize:
- Writing style preferences
- Model parameters
- Evaluation weights
"""
    
    readme_path = base_dir / "README.md"
    readme_path.write_text(readme_content)
    print(f"✓ Created README.md")

def create_example_session(base_dir):
    """Create an example generation session structure"""
    example_date = datetime.now().strftime("%Y-%m-%d")
    example_session = base_dir / "generations" / f"{example_date}_example_topic"
    
    # Create session directories
    session_dirs = [
        "",
        "cycle_1",
        "cycle_1/prompts",
        "cycle_1/raw_outputs",
        "cycle_1/scores",
        "cycle_2",
        "cycle_2/prompts", 
        "cycle_2/refined_outputs",
        "cycle_2/change_tracking",
        "cycle_2/scores",
        "cycle_3",
        "cycle_3/final_candidates",
        "cycle_3/micro_edits",
        "cycle_3/scores",
        "final",
        "final/alternatives"
    ]
    
    for dir_name in session_dirs:
        dir_path = example_session / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
    
    # Create example metadata
    metadata = {
        "session_id": f"{example_date}_example",
        "topic": "Example Topic",
        "created_at": datetime.now().isoformat(),
        "status": "example",
        "note": "This is an example session structure"
    }
    
    metadata_path = example_session / "metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2))
    
    print(f"✓ Created example session: {example_session}")

def create_usage_scripts(base_dir):
    """Create helpful usage scripts"""
    
    # Quick search script using ripgrep
    search_script = """#!/bin/bash
# Search through all blog generations using ripgrep

if [ $# -eq 0 ]; then
    echo "Usage: ./search.sh <search_term>"
    exit 1
fi

echo "Searching for: $1"
echo "=================="

# Search in all markdown files
rg "$1" --type md generations/

# Search in metadata
echo -e "\\nMetadata matches:"
rg "$1" --type json generations/*/metadata.json
"""
    
    search_path = base_dir / "search.sh"
    search_path.write_text(search_script)
    os.chmod(search_path, 0o755)
    print(f"✓ Created search.sh (using ripgrep)")
    
    # List sessions script
    list_script = """#!/bin/bash
# List all generation sessions

echo "Blog Generation Sessions"
echo "========================"

for session in generations/*/; do
    if [ -f "$session/metadata.json" ]; then
        echo ""
        echo "📁 $(basename $session)"
        # Use ripgrep to extract key fields
        rg '"topic":|"created_at":|"final_selection":' "$session/metadata.json" | sed 's/^/  /'
    fi
done
"""
    
    list_path = base_dir / "list_sessions.sh"
    list_path.write_text(list_script)
    os.chmod(list_path, 0o755)
    print(f"✓ Created list_sessions.sh")

def create_requirements(base_dir):
    """Create requirements.txt"""
    requirements = """# AI Model APIs
anthropic>=0.18.0
openai>=1.0.0
google-generativeai>=0.3.0

# Text Processing
beautifulsoup4>=4.12.0
markdown>=3.4.0
textstat>=0.7.3
nltk>=3.8.0

# Analysis
scikit-learn>=1.3.0
numpy>=1.24.0
pandas>=2.0.0

# Utilities
python-dotenv>=1.0.0
rich>=13.0.0
click>=8.1.0
pyyaml>=6.0

# Local Model Support
ollama>=0.1.0
"""
    
    req_path = base_dir / "requirements.txt"
    req_path.write_text(requirements)
    print(f"✓ Created requirements.txt")

def main():
    """Run complete setup"""
    print("🚀 Setting up Evolutionary Blog Post Generator")
    print("=" * 50)
    
    # Create directories
    base_dir = setup_directories()
    
    # Create configuration files
    create_gitignore(base_dir)
    create_readme(base_dir)
    create_requirements(base_dir)
    
    # Create example structure
    create_example_session(base_dir)
    
    # Create utility scripts
    create_usage_scripts(base_dir)
    
    print("\n" + "=" * 50)
    print("✅ Setup complete!")
    print(f"📁 Location: {base_dir}")
    print("\nNext steps:")
    print("1. cd ~/Documents/evo_blog")
    print("2. pip3 install -r requirements.txt")
    print("3. Add your API keys to config/model_configs.json")
    print("4. Copy reference blog posts to config/style_reference/")
    print("\n💡 Use ./search.sh to search with ripgrep")
    print("💡 Use ./list_sessions.sh to see all generations")

if __name__ == "__main__":
    main()