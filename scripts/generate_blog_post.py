#!/usr/bin/env python3
"""
Main Blog Post Generation Pipeline
Generates multiple variations, evaluates, and refines through 3 cycles
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from models import ClaudeClient, OpenAIClient, GeminiClient, LocalClient
from evaluator import BlogEvaluator, EvaluationScore
from data_verifier import DataVerifier
from content_retriever import ContentRetriever
from scqa_planner import SCQAPlanner, SCQAStructure
from braintrust_integration import BraintrustTracker, BraintrustEvaluator


class BlogGenerator:
    """Orchestrates the blog post generation process"""
    
    def __init__(self, output_dir: str = None):
        """Initialize the blog generator with all models"""
        
        # Set up output directory
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.output_dir = Path(f".//generations/{timestamp}")
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize models
        print("Initializing models...")
        self.models = self._initialize_models()
        
        # Initialize evaluator with Claude for AP grading
        self.evaluator = BlogEvaluator(claude_client=self.models['claude'])
        
        # Initialize data verifier
        self.data_verifier = DataVerifier()
        
        # Initialize content retriever for enhanced context
        self.content_retriever = ContentRetriever()
        
        # Initialize SCQA planner
        self.scqa_planner = SCQAPlanner(claude_client=self.models.get('claude'))
        
        # Load SCQA settings
        config_path = Path("./") / "config" / "global_settings.json"
        with open(config_path, 'r') as f:
            self.global_config = json.load(f)
        self.scqa_config = self.global_config.get('scqa_planning', {})
        
        # Initialize Braintrust tracker
        braintrust_config = self.global_config.get('braintrust', {'enabled': True})
        self.braintrust_tracker = BraintrustTracker() if braintrust_config.get('enabled', True) else None
        self.braintrust_evaluator = BraintrustEvaluator() if braintrust_config.get('enabled', True) else None
        
        # Generation statistics
        self.stats = {
            'total_generated': 0,
            'total_cost': 0,
            'best_score': 0,
            'ready_posts': 0,
            'scqa_enabled': self.scqa_config.get('enabled', True)
        }
    
    def _initialize_models(self) -> Dict:
        """Initialize all model clients"""
        models = {}
        
        # Load API keys
        config_path = Path("./") / "config" / "model_configs.json"
        with open(config_path, 'r') as f:
            api_keys = json.load(f)
        
        # Initialize each model
        try:
            models['claude'] = ClaudeClient(
                api_key=api_keys['anthropic_api_key'],
                config={'model': 'claude-sonnet-4-20250514'}
            )
            print("  ✓ Claude Sonnet 4 initialized")
        except Exception as e:
            print(f"  ✗ Claude Sonnet 4 failed: {e}")
        
        try:
            models['gpt4'] = OpenAIClient(
                api_key=api_keys['openai_api_key'],
                config={'model': 'gpt-4.1'}
            )
            print("  ✓ GPT-4.1 initialized")
        except Exception as e:
            print(f"  ✗ GPT-4.1 failed: {e}")
        
        try:
            models['gemini'] = GeminiClient(
                api_key=api_keys['google_api_key'],
                config={'model': 'gemini-2.5-pro'}
            )
            print("  ✓ Gemini 2.5 Pro initialized")
        except Exception as e:
            print(f"  ✗ Gemini 2.5 Pro failed: {e}")
        
        # Skip local model for faster generation
        # try:
        #     models['local'] = LocalClient(
        #         config={'backend': 'ollama', 'model': 'llama3.2:3b'}
        #     )
        #     print("  ✓ Local model initialized")
        # except Exception as e:
        #     print(f"  ✗ Local model failed: {e}")
        
        return models
    
    def generate_variations(self, prompt: str, cycle: int = 1) -> List[Dict]:
        """
        Generate blog post variations using different models and approaches in parallel
        
        Args:
            prompt: The input prompt or topic
            cycle: Which cycle (1, 2, or 3)
            
        Returns:
            List of generated posts with metadata
        """
        variations = []
        
        # Define variation strategies based on cycle
        if cycle == 1:
            strategies = [
                ("technical", "Write a technical deep-dive blog post about"),
                ("business", "Write a business-focused blog post about"),
                ("data-driven", "Write a data-rich analytical blog post about")
            ]
        elif cycle == 2:
            strategies = [
                ("refined", "Improve and refine this blog post idea:"),
                ("expanded", "Expand on the key insights in:"),
            ]
        else:  # cycle 3
            strategies = [
                ("polished", "Polish and perfect this blog post:"),
            ]
        
        # Create generation tasks
        generation_tasks = []
        for model_name, model_client in self.models.items():
            if not model_client:
                continue
                
            # Limit strategies: 2 for cycle 1, 1 for later cycles
            strategies_to_use = strategies[:2] if cycle == 1 else strategies[:1]
            for strategy_name, strategy_prefix in strategies_to_use:
                generation_tasks.append((
                    model_name, model_client, strategy_name, 
                    strategy_prefix, prompt, cycle
                ))
        
        print(f"  Generating {len(generation_tasks)} variations in parallel...")
        
        # Execute all generations in parallel
        with ThreadPoolExecutor(max_workers=6) as executor:
            # Submit all tasks
            future_to_task = {}
            for task in generation_tasks:
                future = executor.submit(self._generate_single_variation, *task)
                future_to_task[future] = task
            
            # Collect results as they complete
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                model_name, _, strategy_name, _, _, _ = task
                
                try:
                    variation = future.result(timeout=60)
                    if variation:
                        variations.append(variation)
                        self.stats['total_generated'] += 1
                        self.stats['total_cost'] += variation['cost']
                        print(f"    ✓ {model_name}-{strategy_name}: {variation['tokens']} tokens, ${variation['cost']:.4f}")
                    else:
                        print(f"    ✗ {model_name}-{strategy_name}: No result")
                except Exception as e:
                    print(f"    ✗ {model_name}-{strategy_name}: {str(e)[:50]}")
        
        return variations
    
    def _generate_single_variation(self, model_name: str, model_client, 
                                  strategy_name: str, strategy_prefix: str, 
                                  prompt: str, cycle: int) -> Optional[Dict]:
        """Generate a single variation (for parallel execution)"""
        
        # Build the generation prompt
        generation_prompt = self._build_generation_prompt(
            prompt, strategy_prefix, cycle
        )
        
        try:
            # Generate the blog post
            response = model_client.generate(
                generation_prompt,
                temperature=0.7 if cycle == 1 else 0.5,
                max_tokens=1500
            )
            
            if response.error:
                return None
            
            # Save the variation
            variation = {
                'model': model_name,
                'strategy': strategy_name,
                'cycle': cycle,
                'content': response.content,
                'cost': response.cost,
                'tokens': response.tokens_used,
                'latency': response.latency_seconds
            }
            
            # Save to file
            filename = f"cycle_{cycle}_{model_name}_{strategy_name}.md"
            filepath = self.output_dir / f"cycle_{cycle}" / filename
            filepath.parent.mkdir(exist_ok=True)
            
            with open(filepath, 'w') as f:
                f.write(response.content)
            
            # Log to Braintrust
            if self.braintrust_tracker:
                self.braintrust_tracker.log_generation(
                    model=model_name,
                    strategy=strategy_name,
                    cycle=cycle,
                    prompt=generation_prompt,
                    output=response.content,
                    cost=response.cost,
                    tokens=response.tokens_used,
                    latency=response.latency_seconds
                )
            
            return variation
            
        except Exception as e:
            return None
    
    def _build_generation_prompt(self, base_prompt: str, strategy_prefix: str, cycle: int) -> str:
        """Build the full generation prompt with style guidelines and enhanced context"""
        
        # Get relevant context from the unified content index
        try:
            context = self.content_retriever.get_context_for_topic(base_prompt)
            context_summary = self.content_retriever.get_context_summary(context)
            print(f"   📚 {context_summary}")
            context_str = self.content_retriever.format_context_for_prompt(context)
        except Exception as e:
            print(f"   ⚠️ Could not retrieve context: {e}")
            context_str = ""
        
        style_guide = """
Write in the exact style of Tom Tunguz with these CRITICAL requirements:

FORMATTING REQUIREMENTS (ABSOLUTELY CRITICAL):
- Approximately 500 words (acceptable range: 500-600 words)
- First sentence: Must be its own standalone paragraph
- Second sentence: Must be its own standalone paragraph and contain either a provoking statement OR a question
- NO section headers or H2/H3 tags - write as continuous flowing prose only
- All other paragraphs: Maximum 2 sentences longer than 20 words each per paragraph
- Can include additional short sentences (under 20 words) for variety
- NEVER use adverbs (words ending in -ly)
- Each paragraph should transition smoothly to the next

CONTENT STRUCTURE REQUIREMENTS:
1. Opening: First sentence (standalone) + Second sentence with provocation/question (standalone)
2. Context Setting: Establish the current stable situation or background (1 paragraph)
3. Problem Introduction: Present the disruption, challenge, or emerging issue (1 paragraph)  
4. Core Question: Implicitly raise the central question this creates (woven into content)
5. Solution/Analysis: Provide evidence-based answers and insights (2-3 paragraphs)
6. Conclusion: Must tie back to the opening hook and reinforce the solution

NARRATIVE STRUCTURE:
Structure the narrative to flow naturally from stable context → emerging problem → implicit question → data-driven solution. The post should read as a cohesive problem-solving narrative without explicit framework references.

STYLE CHARACTERISTICS:
- Include 2-3 specific data points or statistics from real sources
- Use concrete examples from real companies
- Avoid business clichés and adverbs
- Maximum 2 colons in the entire post
- Write concisely and directly - every word counts

PARAGRAPH & SENTENCE VARIATION REQUIREMENTS:
- Mix short (1-2 sentences) and longer (3-4 sentences) paragraphs
- After two longer paragraphs, include a short one for breathing room
- Vary sentence length within paragraphs for natural rhythm
- Use single-sentence paragraphs sparingly for emphasis
- Ensure smooth transitions between different paragraph lengths

CRITICAL DATA REQUIREMENTS:
- DO NOT hallucinate or invent any statistics, percentages, or data points
- DO NOT make up company case studies or specific claims
- If you need data to support a point, indicate [NEEDS DATA: description of what data would help]
- Only use data points that you are certain about from your training
- When citing statistics, be specific about the source if known
- It's better to say "significant" or "substantial" than to invent a specific percentage
- Real examples are preferred, but only use ones you can recall accurately
"""
        
        if cycle == 1:
            return f"""{context_str}{strategy_prefix}: {base_prompt}

{style_guide}

Focus on practical insights that startup founders and VCs can apply immediately."""
        
        elif cycle == 2:
            return f"""{context_str}{strategy_prefix}

{base_prompt}

Improve by:
- Strengthening the argument with more evidence
- Making the opening more compelling
- Adding specific company examples
- Ensuring smooth transitions between ideas
{style_guide}"""
        
        else:  # cycle 3
            return f"""{context_str}{strategy_prefix}

{base_prompt}

Final polish:
- Perfect the opening hook
- Ensure every paragraph flows smoothly
- Verify all data points are specific and impactful
- Strengthen the conclusion
{style_guide}"""
    
    def evaluate_variations(self, variations: List[Dict], title: str = "") -> List[Dict]:
        """Evaluate all variations and rank them"""
        
        print("\nEvaluating variations...")
        evaluated = []
        
        for var in variations:
            print(f"  Evaluating {var['model']} - {var['strategy']}...")
            
            # Evaluate the post
            evaluation = self.evaluator.evaluate(var['content'], title)
            
            # Add evaluation to variation
            var['evaluation'] = evaluation
            var['score'] = evaluation.overall_score
            var['grade'] = evaluation.overall_grade
            var['ready'] = evaluation.ready_to_ship
            
            # Log evaluation to Braintrust
            if self.braintrust_tracker:
                self.braintrust_tracker.log_evaluation(
                    model=var['model'],
                    strategy=var['strategy'],
                    cycle=var['cycle'],
                    content=var['content'],
                    evaluation=evaluation,
                    input_prompt=""  # We'll add this in a future update
                )
            
            evaluated.append(var)
            
            if evaluation.ready_to_ship:
                self.stats['ready_posts'] += 1
            
            if evaluation.overall_score > self.stats['best_score']:
                self.stats['best_score'] = evaluation.overall_score
            
            print(f"    Score: {evaluation.overall_score:.1f} | Grade: {evaluation.overall_grade} | Ready: {'✓' if evaluation.ready_to_ship else '✗'}")
        
        # Sort by score
        evaluated.sort(key=lambda x: x['score'], reverse=True)
        
        # Save evaluation results
        results_file = self.output_dir / f"cycle_{variations[0]['cycle']}_evaluations.json"
        with open(results_file, 'w') as f:
            json.dump([{
                'model': v['model'],
                'strategy': v['strategy'],
                'score': v['score'],
                'grade': v['grade'],
                'ready': v['ready'],
                'feedback': v['evaluation'].feedback
            } for v in evaluated], f, indent=2)
        
        return evaluated
    
    def refine_for_next_cycle(self, top_variations: List[Dict]) -> str:
        """Create a refined prompt for the next cycle based on top variations"""
        
        # Extract best elements from top variations
        best_elements = []
        
        for var in top_variations[:3]:
            eval_feedback = var['evaluation'].feedback
            if "Strengths:" in eval_feedback.get('ap_evaluation', ''):
                strengths = eval_feedback['ap_evaluation'].split('Strengths:')[1].split('|')[0]
                best_elements.append(f"From {var['model']}: {strengths}")
        
        # Build refinement prompt
        refinement = f"""
Based on evaluation, combine the best elements:
{chr(10).join(best_elements)}

Original content to improve:
{top_variations[0]['content'][:1000]}...

Key improvements needed:
{chr(10).join(self.evaluator.generate_improvement_suggestions(top_variations[0]['evaluation']))}
"""
        
        return refinement
    
    def generate_blog_post(self, topic: str, title: str = "", max_cycles: int = 3, enable_scqa: bool = None) -> Dict:
        """
        Main pipeline to generate and refine blog posts
        
        Args:
            topic: The topic or prompt for the blog post
            title: Optional title for context
            max_cycles: Number of refinement cycles (default: 3)
            enable_scqa: Override SCQA planning (None uses config default)
            
        Returns:
            The best blog post with metadata
        """
        
        print(f"\n{'='*60}")
        print(f"Generating Blog Post: {title or topic[:50]}")
        print(f"{'='*60}")
        
        # Start Braintrust experiment
        experiment_id = None
        start_time = time.time()
        if self.braintrust_tracker:
            experiment_metadata = {
                "max_cycles": max_cycles,
                "enable_scqa": enable_scqa,
                "models_available": list(self.models.keys())
            }
            experiment_id = self.braintrust_tracker.start_experiment(topic, title, experiment_metadata)
        
        # Determine if SCQA should be enabled
        use_scqa = enable_scqa if enable_scqa is not None else self.scqa_config.get('enabled', True)
        
        # SCQA Planning Phase
        scqa_structure = None
        if use_scqa:
            print("\n🎯 SCQA Planning Phase")
            try:
                scqa_structure = self.scqa_planner.plan_structure(topic, title)
                
                # Validate SCQA structure
                if self.scqa_config.get('validation_enabled', True):
                    is_valid, issues = self.scqa_planner.validate_scqa_structure(scqa_structure)
                    if not is_valid:
                        print(f"⚠️  SCQA validation issues: {', '.join(issues)}")
                        if scqa_structure.confidence_score < self.scqa_config.get('confidence_threshold', 60):
                            print("🔄 Using fallback structure due to low confidence")
                
                # Show SCQA summary
                print(self.scqa_planner.get_scqa_summary(scqa_structure))
                
                # Create enhanced prompt
                current_prompt = self.scqa_planner.create_enhanced_prompt(scqa_structure, topic)
                
            except Exception as e:
                print(f"⚠️  SCQA planning failed: {e}")
                if self.scqa_config.get('fallback_enabled', True):
                    print("🔄 Falling back to direct topic generation")
                    current_prompt = topic
                else:
                    raise e
        else:
            print("📝 Direct topic generation (SCQA disabled)")
            current_prompt = topic
        
        # Save initial prompt and SCQA structure
        with open(self.output_dir / "initial_prompt.txt", 'w') as f:
            f.write(f"Topic: {topic}\nTitle: {title}\nSCQA Enabled: {use_scqa}\n")
            if scqa_structure:
                f.write(f"\nSCQA Structure:\n{self.scqa_planner.get_scqa_summary(scqa_structure)}")
                f.write(f"\nEnhanced Prompt:\n{current_prompt}")
        
        all_variations = []
        
        for cycle in range(1, max_cycles + 1):
            print(f"\n--- Cycle {cycle} ---")
            
            # Generate variations
            variations = self.generate_variations(current_prompt, cycle)
            
            if not variations:
                print("No variations generated, stopping.")
                break
            
            # Evaluate variations
            evaluated = self.evaluate_variations(variations, title)
            all_variations.extend(evaluated)
            
            # Check if we have a ready post
            ready_posts = [v for v in evaluated if v['ready']]
            if ready_posts and cycle >= 2:
                print(f"\n✓ Found {len(ready_posts)} ready posts, stopping early.")
                break
            
            # Prepare for next cycle
            if cycle < max_cycles:
                current_prompt = self.refine_for_next_cycle(evaluated)
        
        # Select the best post
        all_variations.sort(key=lambda x: x['score'], reverse=True)
        best_post = all_variations[0] if all_variations else None
        
        if best_post:
            # Check for data verification needs
            print("\nChecking for claims that need verification...")
            enhanced_content, claims = self.data_verifier.enhance_blog_post(
                best_post['content'], 
                auto_search=False  # Don't auto-search for now
            )
            
            # Generate fact check report
            if claims:
                fact_check_report = self.data_verifier.generate_fact_check_report(claims)
                with open(self.output_dir / "fact_check_report.md", 'w') as f:
                    f.write(fact_check_report)
                print(f"  Found {len(claims)} claims - see fact_check_report.md")
            
            # Save the best post (enhanced version)
            best_post['content'] = enhanced_content
            with open(self.output_dir / "best_post.md", 'w') as f:
                f.write(best_post['content'])
            
            # Grammar and style check
            print("\nRunning grammar and style check...")
            grammar_checked_content = self._grammar_and_style_check(enhanced_content)
            
            # Copy to h48 blog content folder
            self._copy_to_blog_folder(grammar_checked_content, title)
            
            # Update blog index
            self._update_blog_index()
            
            # Save statistics
            with open(self.output_dir / "statistics.json", 'w') as f:
                json.dump({
                    'best_score': best_post['score'],
                    'best_grade': best_post['grade'],
                    'best_model': best_post['model'],
                    'best_strategy': best_post['strategy'],
                    'total_generated': self.stats['total_generated'],
                    'total_cost': self.stats['total_cost'],
                    'ready_posts': self.stats['ready_posts'],
                    'all_scores': [v['score'] for v in all_variations]
                }, f, indent=2)
            
            print(f"\n{'='*60}")
            print("Generation Complete!")
            print(f"{'='*60}")
            print(f"Best Post: {best_post['grade']} ({best_post['score']:.1f}/100)")
            print(f"Model: {best_post['model']} | Strategy: {best_post['strategy']}")
            print(f"Ready to Ship: {'✅ Yes' if best_post['ready'] else '❌ No'}")
            print(f"Total Cost: ${self.stats['total_cost']:.2f}")
            print(f"Output: {self.output_dir}")
            
            # Log best post selection and finish Braintrust experiment
            if self.braintrust_tracker:
                self.braintrust_tracker.log_best_post_selection(
                    best_post=best_post,
                    all_variations=all_variations
                )
                
                # Prepare final stats
                end_time = time.time()
                final_stats = {
                    **self.stats,
                    "duration_seconds": end_time - start_time,
                    "experiment_id": experiment_id,
                    "final_best_score": best_post['score'],
                    "final_ready": best_post['ready']
                }
                
                experiment_url = self.braintrust_tracker.finish_experiment(final_stats)
                if experiment_url and experiment_url not in ["disabled", "error"]:
                    print(f"📊 Braintrust Experiment: {experiment_url}")
            
            return best_post
        
        else:
            print("\n❌ No posts generated successfully.")
            return None
    
    def _copy_to_blog_folder(self, content: str, title: str):
        """Copy the final blog post to the h48/content/post folder with proper front matter"""
        import re
        from datetime import datetime
        
        # Create filename from title
        if title:
            filename = re.sub(r'[^\w\s-]', '', title.lower())
            filename = re.sub(r'[-\s]+', '-', filename)
            filename = f"{filename}.md"
        else:
            # Fallback to timestamp-based name
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"blog-post-{timestamp}.md"
        
        # Generate today's date for front matter
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Determine categories based on content analysis
        categories = self._analyze_categories(content)
        categories_str = f"[{', '.join(categories)}]"
        
        # Extract first line as potential title if no title provided
        if not title:
            lines = content.strip().split('\n')
            if lines:
                title = lines[0].strip().rstrip('.')
        
        # Build front matter
        front_matter = f"""---
layout: post
draft: false
title: "{title}"
categories: {categories_str}
date: "{today}"
---

{content}"""
        
        # Define target path
        h48_content_path = Path("./content/post")
        target_file = h48_content_path / filename
        
        try:
            # Ensure the target directory exists
            h48_content_path.mkdir(parents=True, exist_ok=True)
            
            # Write the content with front matter to the target file
            with open(target_file, 'w', encoding='utf-8') as f:
                f.write(front_matter)
            
            print(f"✅ Blog post copied to: {target_file}")
            
        except Exception as e:
            print(f"⚠️  Warning: Could not copy to h48 folder: {e}")
    
    def _analyze_categories(self, content: str) -> list:
        """Analyze content to suggest appropriate categories"""
        content_lower = content.lower()
        categories = []
        
        # AI-related keywords
        ai_keywords = ['ai', 'artificial intelligence', 'machine learning', 'llm', 'gpt', 'claude', 'automation', 'agent']
        if any(keyword in content_lower for keyword in ai_keywords):
            categories.append('AI')
        
        # SaaS/Business keywords
        saas_keywords = ['saas', 'software', 'startup', 'revenue', 'business', 'growth', 'sales', 'marketing']
        if any(keyword in content_lower for keyword in saas_keywords):
            categories.append('SaaS')
        
        # Data/Analytics keywords
        data_keywords = ['data', 'analytics', 'pipeline', 'etl', 'database', 'warehouse', 'visualization']
        if any(keyword in content_lower for keyword in data_keywords):
            categories.append('data')
        
        # Management/Leadership keywords
        mgmt_keywords = ['management', 'leadership', 'team', 'hiring', 'culture', 'manager', 'ceo']
        if any(keyword in content_lower for keyword in mgmt_keywords):
            categories.append('management')
        
        # Technology keywords
        tech_keywords = ['engineering', 'developer', 'programming', 'code', 'technical', 'infrastructure']
        if any(keyword in content_lower for keyword in tech_keywords):
            categories.append('technology')
        
        # Default to 'trend' if no specific categories found
        if not categories:
            categories.append('trend')
        
        return categories[:3]  # Limit to 3 categories
    
    def _grammar_and_style_check(self, content: str) -> str:
        """Use Claude to check grammar, spelling, and paragraph variation."""
        try:
            from models import ClaudeClient
            claude = ClaudeClient()
            
            prompt = f"""Please proofread this blog post for:

1. GRAMMAR & SPELLING:
   - Fix any grammar errors
   - Correct spelling mistakes
   - Remove duplicate punctuation (like double periods)
   - Ensure proper punctuation

2. PARAGRAPH VARIATION:
   - Mix short (1-2 sentences) and longer (3-4 sentences) paragraphs
   - After two longer paragraphs, include a short one for breathing room
   - Vary sentence length within paragraphs for natural rhythm
   - Ensure smooth transitions between different paragraph lengths

3. STYLE CONSISTENCY:
   - Keep the tone and voice consistent
   - Maintain the original meaning and key points
   - Preserve all specific examples and data points

Return ONLY the corrected text with no explanations or comments.

Text to proofread:

{content}"""

            response = claude.generate(prompt, max_tokens=2000)
            if response and response.strip():
                print("✅ Grammar and style check completed")
                return response.strip()
            else:
                print("⚠️  Grammar check failed, using original content")
                return content
                
        except Exception as e:
            print(f"⚠️  Grammar check error: {e}")
            return content
    
    def _update_blog_index(self):
        """Update the blog post LanceDB index."""
        try:
            import subprocess
            import sys
            
            # Path to the blog indexer
            indexer_path = "./content/blog_indexer.py"
            
            # Run the indexer update
            result = subprocess.run(
                [sys.executable, indexer_path, "--update"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                print("✅ Blog index updated successfully")
            else:
                print(f"⚠️  Blog index update failed: {result.stderr}")
                
        except Exception as e:
            print(f"⚠️  Blog index update error: {e}")


def main():
    parser = argparse.ArgumentParser(description="Generate blog posts using multiple AI models")
    parser.add_argument("topic", help="The topic or prompt for the blog post")
    parser.add_argument("--title", help="Optional title for the blog post", default="")
    parser.add_argument("--cycles", type=int, default=2, help="Number of refinement cycles (1-3)")
    parser.add_argument("--output", help="Output directory for generated posts")
    
    # SCQA options
    scqa_group = parser.add_mutually_exclusive_group()
    scqa_group.add_argument("--enable-scqa", action="store_true", help="Enable SCQA planning (default)")
    scqa_group.add_argument("--no-scqa", action="store_true", help="Disable SCQA planning")
    scqa_group.add_argument("--scqa-only", action="store_true", help="Only generate SCQA structure, don't create blog post")
    
    args = parser.parse_args()
    
    # Determine SCQA setting
    enable_scqa = None
    if args.no_scqa:
        enable_scqa = False
    elif args.enable_scqa:
        enable_scqa = True
    # If neither flag, use config default (None)
    
    # Handle SCQA-only mode
    if args.scqa_only:
        print("🎯 SCQA Structure Analysis Only")
        print("="*50)
        
        # Just run SCQA planning
        from scqa_planner import SCQAPlanner
        from models import ClaudeClient
        
        # Initialize Claude for SCQA planning
        config_path = Path("./") / "config" / "model_configs.json"
        with open(config_path, 'r') as f:
            api_keys = json.load(f)
        
        claude_client = ClaudeClient(
            api_key=api_keys['anthropic_api_key'],
            config={'model': 'claude-opus-4-1-20250805'}
        )
        
        planner = SCQAPlanner(claude_client=claude_client)
        structure = planner.plan_structure(args.topic, args.title)
        
        print(planner.get_scqa_summary(structure))
        
        is_valid, issues = planner.validate_scqa_structure(structure)
        print(f"\nValidation: {'✅ Valid' if is_valid else '❌ Issues found'}")
        if issues:
            for issue in issues:
                print(f"  - {issue}")
        
        print(f"\nEnhanced Prompt Preview:")
        print("-" * 30)
        enhanced_prompt = planner.create_enhanced_prompt(structure, args.topic)
        print(enhanced_prompt[:500] + "..." if len(enhanced_prompt) > 500 else enhanced_prompt)
        return
    
    # Initialize generator
    generator = BlogGenerator(output_dir=args.output)
    
    # Generate blog post
    result = generator.generate_blog_post(
        topic=args.topic,
        title=args.title,
        max_cycles=min(args.cycles, 3),
        enable_scqa=enable_scqa
    )
    
    if result and result['ready']:
        print(f"\n✨ Your blog post is ready to publish!")
        print(f"Find it at: {generator.output_dir / 'best_post.md'}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main()
    else:
        # Test with a sample topic
        print("Testing with sample topic...")
        generator = BlogGenerator()
        result = generator.generate_blog_post(
            topic="How AI agents are changing the way startups approach customer support, based on recent Klarna results showing 66% cost reduction",
            title="The AI Agent Revolution in Customer Support",
            max_cycles=2
        )