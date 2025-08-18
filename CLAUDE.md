# Evolutionary Blog Post Generator

An AI-powered system that generates high-quality blog posts using multiple language models in parallel, with evaluation and refinement cycles to achieve optimal results.

## Overview

This tool uses an evolutionary approach to blog post generation:

1. **Parallel Generation**: Multiple AI models (Claude, GPT-4, Gemini) generate different variations simultaneously
2. **AP-Grade Evaluation**: Posts are scored using AP English grading criteria  
3. **Iterative Refinement**: Best posts are refined through multiple cycles
4. **Data Verification**: Claims are fact-checked and marked for verification

## Architecture

```
User Prompt → Multiple Models → Evaluation → Refinement → Final Post
    ↓              ↓               ↓            ↓           ↓
  Topic      Claude/GPT/Gemini   AP Grading   Improvement  Publishing
```

The system generates blog posts that consistently score 85-95/100 with proper Tom Tunguz style characteristics.

## Quick Start

### 1. Setup Environment

```bash
# Create virtual environment with uv
uv venv

# Install dependencies
uv pip install -r requirements.txt
```

### 2. Configure API Keys

Create `config/model_configs.json`:
```json
{
  "anthropic_api_key": "your-claude-key",
  "openai_api_key": "your-gpt4-key", 
  "google_api_key": "your-gemini-key"
}
```

### 3. Setup Braintrust (Optional)

For advanced evaluation tracking and experiment logging:

```bash
# Set Braintrust API key
export BRAINTRUST_API_KEY="your-braintrust-key"

# Test the integration
python test_braintrust.py

# Run setup helper
python scripts/eval_braintrust.py --setup
```

### 4. Generate a Blog Post

```bash
# Basic generation
python scripts/generate_blog_post.py "Your topic here"

# With custom title and cycles
python scripts/generate_blog_post.py "Your topic" --title "Post Title" --cycles 3
```

## Usage Examples

### Business Analysis Post
```bash
python scripts/generate_blog_post.py "How AI agents are transforming enterprise software procurement, reducing decision time from months to weeks"
```

### Technical Deep Dive
```bash
python scripts/generate_blog_post.py "The architecture patterns enabling real-time AI inference at scale" --title "Real-time AI at Scale"
```

### Market Analysis
```bash
python scripts/generate_blog_post.py "Why SaaS startups are shifting from freemium to product-led trials in 2025" --cycles 3
```

## Output Structure

Each generation creates a timestamped directory with:

```
generations/20250813_152433/
├── cycle_1/                    # First round outputs
│   ├── cycle_1_claude_business.md
│   ├── cycle_1_gpt4_technical.md
│   └── cycle_1_gemini_business.md
├── cycle_2/                    # Refined outputs
│   ├── cycle_2_claude_refined.md
│   └── cycle_2_gpt4_refined.md
├── best_post.md               # Highest scoring post
├── statistics.json            # Generation metrics
├── cycle_1_evaluations.json   # Detailed scores
└── fact_check_report.md       # Data verification
```

## Understanding Scores

**Evaluation Criteria:**
- **Content Quality** (40%): Insight depth, argument strength
- **Writing Style** (30%): Tom Tunguz voice, clarity, flow
- **Structure** (20%): Hook, transitions, conclusion
- **Data Usage** (10%): Specific examples, statistics

**Grade Scale:**
- A (90-100): Ready to publish
- B+ (85-89): Minor edits needed
- B (80-84): Needs improvement
- Below 80: Significant revision required

## Style Guidelines

Posts are optimized for Tom Tunguz's style:

- **Length**: Exactly 500 words maximum
- **Structure**: Short paragraphs (2-4 sentences)
- **Content**: 2-3 specific data points, real company examples
- **Tone**: Direct, practical insights for founders/VCs
- **Format**: No H2 headers, compelling hook, forward-looking conclusion

## Braintrust Integration

### Experiment Tracking

The system automatically logs all generations and evaluations to Braintrust when `BRAINTRUST_API_KEY` is set:

- **Generation Logging**: Every model output with cost, tokens, latency
- **Evaluation Tracking**: AP scores, grades, and detailed feedback
- **Comparative Analysis**: Battle evaluations between post variations
- **Experiment URLs**: Direct links to view results in Braintrust dashboard

### Evaluation Scripts

```bash
# Run standalone evaluations
python scripts/eval_braintrust.py --generations-dir generations/20250815_085043

# Compare multiple posts
python scripts/eval_braintrust.py --generations-dir generations/latest --compare

# Style compliance check
python scripts/eval_braintrust.py --generations-dir generations/latest --style

# Test evaluation framework
python scripts/eval_braintrust.py --test
```

### Configuration

Braintrust settings in `config/global_settings.json`:

```json
{
  "braintrust": {
    "enabled": true,
    "project_name": "evo-blog-generator",
    "log_generations": true,
    "log_evaluations": true,
    "log_comparisons": true,
    "run_factuality_checks": true,
    "auto_battle_evaluation": true
  }
}
```

To disable Braintrust tracking, set `"enabled": false` or unset `BRAINTRUST_API_KEY`.

## Advanced Features

### Custom Evaluation Weights

Edit `config/evaluation_weights.json` to adjust scoring:

```json
{
  "content_quality": 0.4,
  "writing_style": 0.3,
  "structure": 0.2,
  "data_usage": 0.1
}
```

### Search Generated Content

```bash
# Find high-scoring posts
./search.sh "score.*9[0-9]"

# Search by topic
./search.sh "AI agents"

# List all sessions
./list_sessions.sh
```

### Fact Checking

The system automatically:
- Identifies claims needing verification
- Marks suspicious statistics
- Generates fact-check reports
- Suggests [NEEDS DATA] placeholders

## Troubleshooting

### Common Issues

**API Key Errors**: Verify `config/model_configs.json` exists with valid keys

**Module Not Found**: Ensure virtual environment is activated:
```bash
source evo_blog_env/bin/activate
```

**Low Scores**: Check that posts stay under 500 words and include specific data

**No Output**: Verify at least one model initializes successfully

### Performance Tips

- Use 2 cycles for faster generation (default)
- 3 cycles for highest quality
- Skip local models for speed
- Run with single model for testing

## API Costs

Typical costs per blog post:
- **2 cycles**: $0.05-0.15
- **3 cycles**: $0.10-0.25

Cost breakdown by model:
- Claude Sonnet 4: ~$0.04 per post
- GPT-4.1: ~$0.06 per post  
- Gemini 2.5 Pro: ~$0.02 per post

## Best Practices

1. **Specific Topics**: Use concrete, focused prompts
2. **Data Ready**: Have supporting statistics available
3. **Review Scores**: Aim for 85+ before publishing
4. **Fact Check**: Verify all claims in fact_check_report.md
5. **Iterate**: Use refinement cycles for important posts

## Integration

### Hugo Blog Integration

```bash
# Copy best post to Hugo
cp generations/latest/best_post.md ~/blog/content/posts/

# Auto-format for Hugo
python scripts/format_for_hugo.py generations/latest/best_post.md
```

### Automated Workflows

The system integrates with:
- Content calendars
- Social media scheduling  
- Email newsletters
- SEO optimization tools

## Contributing

Key files to understand:
- `scripts/generate_blog_post.py`: Main orchestrator
- `scripts/evaluator.py`: AP grading system
- `scripts/models/`: AI client implementations
- `config/`: Style and evaluation settings

For custom models, implement the `BaseModel` interface in `scripts/models/base.py`.

---

*The Evolutionary Blog Post Generator consistently produces publication-ready content that matches Tom Tunguz's distinctive style and insights.*