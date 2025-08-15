# Evolutionary Blog Post Generator

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
