#!/usr/bin/env python3
"""
Braintrust Evaluation Script for Blog Posts
Runs systematic evaluations using Braintrust framework
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

import braintrust
from autoevals import Factuality, Levenshtein, Battle
from braintrust_integration import BraintrustTracker, setup_braintrust_for_blog_generator


def load_blog_posts_for_evaluation(generations_dir: str) -> List[Dict]:
    """Load blog posts from a generations directory for evaluation"""
    
    generations_path = Path(generations_dir)
    if not generations_path.exists():
        raise ValueError(f"Generations directory not found: {generations_dir}")
    
    posts = []
    
    # Look for best_post.md files
    best_post_file = generations_path / "best_post.md"
    if best_post_file.exists():
        with open(best_post_file, 'r') as f:
            content = f.read()
        
        # Try to load metadata
        metadata_file = generations_path / "statistics.json"
        metadata = {}
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
        
        posts.append({
            "id": "best_post",
            "content": content,
            "metadata": metadata,
            "source": str(best_post_file)
        })
    
    # Also load individual cycle posts for comparison
    for cycle_dir in generations_path.glob("cycle_*"):
        if cycle_dir.is_dir():
            for post_file in cycle_dir.glob("*.md"):
                with open(post_file, 'r') as f:
                    content = f.read()
                
                # Parse filename for metadata
                filename_parts = post_file.stem.split('_')
                cycle_num = filename_parts[1] if len(filename_parts) > 1 else "unknown"
                model = filename_parts[2] if len(filename_parts) > 2 else "unknown"
                strategy = filename_parts[3] if len(filename_parts) > 3 else "unknown"
                
                posts.append({
                    "id": post_file.stem,
                    "content": content,
                    "metadata": {
                        "cycle": cycle_num,
                        "model": model,
                        "strategy": strategy
                    },
                    "source": str(post_file)
                })
    
    return posts


def create_evaluation_dataset() -> List[Dict]:
    """Create a dataset of blog post evaluation scenarios"""
    
    return [
        {
            "input": "Evaluate blog post quality",
            "expected": "High-quality blog post with clear structure, engaging content, and factual accuracy",
            "criteria": ["factuality", "readability", "engagement", "structure"]
        },
        {
            "input": "Check Tom Tunguz style compliance",
            "expected": "Matches Tom Tunguz writing style: analytical, data-driven, 500-750 words",
            "criteria": ["style_match", "word_count", "data_usage", "tone"]
        },
        {
            "input": "Verify data accuracy",
            "expected": "All statistics and claims are accurate and properly sourced",
            "criteria": ["factuality", "source_citations", "data_accuracy"]
        }
    ]


def run_blog_post_evaluation():
    """Main evaluation function using Braintrust"""
    
    # Setup data
    posts_data = [
        {
            "input": "How AI agents are transforming customer support",
            "expected": "High-quality blog post about AI agents in customer support",
            "metadata": {"topic": "AI agents", "industry": "customer support"}
        },
        {
            "input": "The future of SaaS pricing models in 2025",
            "expected": "Analytical blog post about SaaS pricing trends",
            "metadata": {"topic": "SaaS", "year": "2025"}
        }
    ]
    
    # Task function - simulate blog post generation
    def task(input_data):
        """Simulate the blog generation task"""
        # This would normally call your blog generator
        # For testing, return a sample response
        if isinstance(input_data, dict):
            return f"Generated blog post about: {input_data['input']}"
        else:
            return f"Generated blog post about: {input_data}"
    
    # Scoring functions
    scores = [
        Factuality(),  # Check factual accuracy
        Levenshtein()  # Basic text similarity
    ]
    
    # Run evaluation
    result = braintrust.Eval(
        name="blog_post_quality_eval",
        data=posts_data,
        task=task,
        scores=scores,
        metadata={
            "evaluation_type": "blog_quality",
            "framework": "evolutionary_blog_generator",
            "timestamp": datetime.now().isoformat()
        }
    )
    
    print(f"✅ Evaluation completed: {result}")
    return result


def run_comparative_evaluation(posts: List[Dict]):
    """Run comparative evaluation between multiple blog posts"""
    
    if len(posts) < 2:
        print("❌ Need at least 2 posts for comparative evaluation")
        return None
    
    def compare_posts(input_data):
        """Compare two posts and return the better one"""
        post1 = input_data["post1"]
        post2 = input_data["post2"]
        
        # Use Battle evaluator for comparison
        battle = Battle()
        result = battle(output=post1, expected=post2)
        return {
            "winner": "post1" if result.score > 0.5 else "post2",
            "confidence": abs(result.score - 0.5) * 2,
            "reasoning": result.metadata if hasattr(result, 'metadata') else "No reasoning available"
        }
    
    # Create comparison data
    comparison_data = []
    for i in range(len(posts) - 1):
        comparison_data.append({
            "post1": posts[i]["content"],
            "post2": posts[i + 1]["content"],
            "post1_id": posts[i]["id"],
            "post2_id": posts[i + 1]["id"]
        })
    
    # Run evaluation
    result = braintrust.Eval(
        name="blog_post_comparison_eval",
        data=comparison_data,
        task=compare_posts,
        scores=[],  # Battle already provides scoring
        metadata={
            "evaluation_type": "comparative",
            "posts_count": len(posts),
            "timestamp": datetime.now().isoformat()
        }
    )
    
    print(f"✅ Comparative evaluation completed")
    return result


def run_style_compliance_evaluation(posts: List[Dict]):
    """Evaluate Tom Tunguz style compliance"""
    
    def evaluate_style(input_data):
        """Evaluate style compliance"""
        content = input_data["content"]
        
        # Basic style checks
        word_count = len(content.split())
        paragraph_count = len([p for p in content.split('\n\n') if p.strip()])
        
        # Style compliance score
        score = 1.0
        
        # Check word count (500-750 target)
        if word_count < 500 or word_count > 900:
            score -= 0.3
        
        # Check paragraph structure (prefer shorter paragraphs)
        avg_words_per_paragraph = word_count / max(paragraph_count, 1)
        if avg_words_per_paragraph > 100:  # Too long paragraphs
            score -= 0.2
        
        # Check for data points (look for numbers/percentages)
        import re
        data_points = len(re.findall(r'\d+%|\$\d+|\d+\.\d+', content))
        if data_points < 2:
            score -= 0.3
        
        return {
            "style_score": max(0, score),
            "word_count": word_count,
            "paragraph_count": paragraph_count,
            "data_points": data_points,
            "compliant": score > 0.7
        }
    
    # Prepare evaluation data
    style_data = [{"content": post["content"], "id": post["id"]} for post in posts]
    
    # Run evaluation
    result = braintrust.Eval(
        name="tom_tunguz_style_compliance",
        data=style_data,
        task=evaluate_style,
        scores=[
            lambda output, expected: output["style_score"],
            lambda output, expected: 1.0 if output["compliant"] else 0.0
        ],
        metadata={
            "evaluation_type": "style_compliance",
            "author": "Tom Tunguz",
            "timestamp": datetime.now().isoformat()
        }
    )
    
    print(f"✅ Style compliance evaluation completed")
    return result


def main():
    parser = argparse.ArgumentParser(description="Run Braintrust evaluations on blog posts")
    parser.add_argument("--generations-dir", help="Path to generations directory to evaluate")
    parser.add_argument("--setup", action="store_true", help="Setup Braintrust configuration")
    parser.add_argument("--test", action="store_true", help="Run test evaluation")
    parser.add_argument("--compare", action="store_true", help="Run comparative evaluation")
    parser.add_argument("--style", action="store_true", help="Run style compliance evaluation")
    parser.add_argument("--api-key", help="Braintrust API key")
    
    args = parser.parse_args()
    
    # Setup mode
    if args.setup:
        print("🔧 Setting up Braintrust for blog generator...")
        success = setup_braintrust_for_blog_generator(args.api_key)
        if success:
            print("✅ Braintrust setup completed successfully")
        else:
            print("❌ Braintrust setup failed")
        return
    
    # Check if Braintrust is configured
    if not os.getenv('BRAINTRUST_API_KEY') and not args.api_key:
        print("❌ BRAINTRUST_API_KEY not set. Use --setup or set environment variable.")
        return
    
    if args.api_key:
        os.environ['BRAINTRUST_API_KEY'] = args.api_key
    
    # Test mode
    if args.test:
        print("🧪 Running test evaluation...")
        result = run_blog_post_evaluation()
        return
    
    # Load posts for evaluation
    if args.generations_dir:
        print(f"📂 Loading posts from {args.generations_dir}...")
        try:
            posts = load_blog_posts_for_evaluation(args.generations_dir)
            print(f"✅ Loaded {len(posts)} posts for evaluation")
            
            if args.compare and len(posts) >= 2:
                print("🔄 Running comparative evaluation...")
                run_comparative_evaluation(posts)
            
            if args.style:
                print("📝 Running style compliance evaluation...")
                run_style_compliance_evaluation(posts)
            
            if not args.compare and not args.style:
                print("📊 Running all evaluations...")
                if len(posts) >= 2:
                    run_comparative_evaluation(posts)
                run_style_compliance_evaluation(posts)
            
        except Exception as e:
            print(f"❌ Error loading posts: {e}")
    else:
        print("❌ Please specify --generations-dir or use --test for testing")
        parser.print_help()


if __name__ == "__main__":
    main()