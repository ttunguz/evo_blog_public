#!/usr/bin/env python3
"""
Iterative Improver - Main Orchestrator
Runs the complete iterative prompt improvement system through multiple cycles
"""

import os
import sys
import json
import time
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from post_analyzer import PostAnalyzer, StyleAnalysis
from prompt_generator import PromptGenerator, PromptVariation
from comparative_evaluator import ComparativeEvaluator, ComparisonScore
from feedback_manager import FeedbackManager, FeedbackSummary
from braintrust_integration import BraintrustTracker

# Import blog generator
from generate_blog_post import BlogGenerator


class IterativeImprover:
    """Main orchestrator for iterative prompt improvement"""
    
    def __init__(self, max_iterations: int = 20, use_llm_judge: bool = False):
        self.max_iterations = max_iterations
        self.use_llm_judge = use_llm_judge
        self.output_dir = Path(".//iterative_improvements")
        self.output_dir.mkdir(exist_ok=True)
        
        # Create iteration tracking directory
        self.run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_dir = self.output_dir / f"run_{self.run_id}"
        self.run_dir.mkdir(exist_ok=True)
        
        # Initialize components
        self.braintrust_tracker = BraintrustTracker("iterative-improvement")
        self.post_analyzer = PostAnalyzer(self.braintrust_tracker)
        self.prompt_generator = PromptGenerator(self.braintrust_tracker)
        self.comparative_evaluator = ComparativeEvaluator(self.braintrust_tracker, use_llm_judge=use_llm_judge)
        self.feedback_manager = FeedbackManager(self.braintrust_tracker)
        
        # Initialize blog generator for AI post generation
        try:
            self.blog_generator = BlogGenerator()
        except FileNotFoundError:
            # Handle missing config gracefully
            print("⚠️  Warning: Could not initialize blog generator. Using simplified generation.")
            self.blog_generator = None
        
        # Tracking variables
        self.iteration_results: List[Dict] = []
        self.best_overall_score = 0.0
        self.best_prompt = ""
        self.convergence_threshold = 0.02  # Stop if improvement < 2%
        self.stagnation_count = 0
        self.max_stagnation = 3
    
    def run_complete_cycle(self, num_iterations: int = 20) -> Dict:
        """Run the complete iterative improvement cycle"""
        
        print(f"🚀 Starting Iterative Prompt Improvement")
        print(f"{'='*60}")
        print(f"Run ID: {self.run_id}")
        print(f"Target Iterations: {num_iterations}")
        print(f"Output Directory: {self.run_dir}")
        print(f"{'='*60}")
        
        # Start Braintrust experiment tracking
        experiment_id = self.braintrust_tracker.start_experiment(
            topic="iterative_prompt_improvement",
            title=f"20-Iteration Prompt Optimization Run",
            metadata={
                "run_id": self.run_id,
                "max_iterations": num_iterations,
                "convergence_threshold": self.convergence_threshold
            }
        )
        
        start_time = time.time()
        
        try:
            # Phase 1: Analyze published posts (once at the beginning)
            print(f"\n📊 Phase 1: Analyzing Published Posts")
            style_analysis = self.post_analyzer.analyze_posts(20)
            published_posts = self.post_analyzer.posts
            
            # Run iterations
            for iteration in range(1, num_iterations + 1):
                print(f"\n{'='*60}")
                print(f"🔄 ITERATION {iteration}/{num_iterations}")
                print(f"{'='*60}")
                
                iteration_start = time.time()
                
                try:
                    # Run single iteration
                    iteration_result = self._run_single_iteration(
                        iteration, style_analysis, published_posts
                    )
                    
                    self.iteration_results.append(iteration_result)
                    
                    # Check for improvement and convergence
                    should_continue = self._check_convergence(iteration_result, iteration)
                    
                    iteration_time = time.time() - iteration_start
                    print(f"⏱️  Iteration {iteration} completed in {iteration_time:.1f}s")
                    
                    if not should_continue:
                        print(f"\n🎯 Convergence achieved after {iteration} iterations")
                        break
                        
                except Exception as e:
                    print(f"❌ Error in iteration {iteration}: {e}")
                    continue
            
            # Generate final summary
            final_results = self._generate_final_summary()
            
            # Save complete results
            self._save_complete_results(final_results)
            
            total_time = time.time() - start_time
            print(f"\n{'='*60}")
            print(f"🎉 ITERATIVE IMPROVEMENT COMPLETE")
            print(f"{'='*60}")
            print(f"Total Time: {total_time:.1f}s")
            print(f"Iterations Completed: {len(self.iteration_results)}")
            print(f"Best Overall Score: {self.best_overall_score:.1%}")
            print(f"Final Improvement: {final_results['total_improvement']:+.1%}")
            print(f"Results saved to: {self.run_dir}")
            
            return final_results
            
        finally:
            # Finish Braintrust experiment
            if self.braintrust_tracker:
                final_stats = {
                    "iterations_completed": len(self.iteration_results),
                    "best_score": self.best_overall_score,
                    "total_improvement": final_results.get('total_improvement', 0.0) if 'final_results' in locals() else 0.0,
                    "run_id": self.run_id
                }
                self.braintrust_tracker.finish_experiment(final_stats)
    
    def _run_single_iteration(self, iteration: int, style_analysis: StyleAnalysis, 
                            published_posts: List) -> Dict:
        """Run a single iteration of the improvement cycle"""
        
        print(f"\n📋 Iteration {iteration} Steps:")
        
        # Step 1: Generate prompt variations (or use previous feedback)
        print(f"   1️⃣ Generating prompt variations...")
        
        if iteration == 1:
            # First iteration: generate based on style analysis
            prompt_variations = self.prompt_generator.generate_iterative_improvements(
                style_analysis, iteration=iteration
            )
        else:
            # Later iterations: use feedback from previous iteration
            previous_result = self.iteration_results[-1]
            # Extract performance feedback for prompt generator
            performance_feedback = {
                "overall_similarity": previous_result["best_score_this_iteration"],
                "content_depth": 0.5,  # Simplified for demo
                "style_similarity": 0.6,
                "structural_match": 0.55
            }
            prompt_variations = self.prompt_generator.generate_iterative_improvements(
                style_analysis, {"performance_scores": performance_feedback}, iteration
            )
        
        print(f"      Generated {len(prompt_variations)} variations")
        
        # Step 2: Generate AI posts using prompt variations
        print(f"   2️⃣ Generating AI posts...")
        ai_posts = self._generate_ai_posts_from_prompts(prompt_variations, published_posts)
        print(f"      Generated {len(ai_posts)} AI posts")
        
        # Step 3: Compare AI posts with published posts
        print(f"   3️⃣ Running comparative evaluation...")
        comparison_results = self._compare_with_published_posts(ai_posts, published_posts)
        print(f"      Completed {len(comparison_results)} comparisons")
        
        # Step 4: Generate feedback and optimization recommendations
        print(f"   4️⃣ Analyzing feedback...")
        feedback_summary = self.feedback_manager.generate_feedback_summary(
            comparison_results, prompt_variations, iteration
        )
        
        # Step 5: Update best performing prompt
        best_score = max(c.overall_similarity for c in comparison_results) if comparison_results else 0.0
        if best_score > self.best_overall_score:
            self.best_overall_score = best_score
            best_idx = max(range(len(comparison_results)), 
                          key=lambda i: comparison_results[i].overall_similarity)
            self.best_prompt = prompt_variations[best_idx].prompt_text
        
        # Compile iteration results
        iteration_result = {
            "iteration": iteration,
            "timestamp": datetime.now().isoformat(),
            "prompt_variations": [
                {
                    "name": pv.name,
                    "version": pv.version,
                    "expected_improvement": pv.expected_score_improvement
                } for pv in prompt_variations
            ],
            "comparison_results": [
                {
                    "overall_similarity": cr.overall_similarity,
                    "structural_match": cr.structural_match,
                    "style_similarity": cr.style_similarity,
                    "content_depth": cr.content_depth,
                    "improvement_areas": cr.improvement_areas
                } for cr in comparison_results
            ],
            "best_score_this_iteration": best_score,
            "best_overall_score": self.best_overall_score,
            "feedback_summary": {
                "overall_improvement": feedback_summary.overall_improvement,
                "confidence_score": feedback_summary.confidence_score,
                "worst_areas": feedback_summary.worst_performing_areas
            }
        }
        
        # Save iteration results
        self._save_iteration_results(iteration, iteration_result)
        
        return iteration_result
    
    def _generate_ai_posts_from_prompts(self, prompt_variations: List[PromptVariation], 
                                      published_posts: List) -> List[Tuple[str, str]]:
        """Generate AI posts using different prompt variations"""
        
        ai_posts = []
        
        # If blog generator is not available, use simulated posts
        if not self.blog_generator:
            return self._generate_simulated_posts(prompt_variations)
        
        # Select topics from published posts for generation
        topics = [
            "How AI agents are transforming B2B sales efficiency",
            "The rise of micro-SaaS businesses in specialized markets", 
            "Why data teams are becoming revenue drivers",
            "The future of SaaS pricing models in 2025",
            "How vertical AI tools are disrupting traditional software"
        ]
        
        # Use top 3 prompt variations for efficiency
        top_variations = sorted(prompt_variations, key=lambda pv: pv.expected_score_improvement, reverse=True)[:3]
        
        for i, variation in enumerate(top_variations):
            topic = topics[i % len(topics)]
            
            try:
                print(f"      🤖 Generating with {variation.name} prompt...")
                
                # Create modified generator with new prompt
                try:
                    modified_generator = BlogGenerator()
                    
                    # Override the prompt building method (simplified approach)
                    def build_custom_prompt(base_prompt, strategy_prefix, cycle):
                        return f"{variation.prompt_text}\n\nTopic: {base_prompt}"
                    
                    modified_generator._build_generation_prompt = build_custom_prompt
                    
                    # Generate blog post
                    result = modified_generator.generate_blog_post(
                        topic=topic,
                        title=f"Generated for {variation.name}",
                        max_cycles=1  # Quick generation for iteration
                    )
                    
                    if result and result.get('content'):
                        ai_posts.append((result['content'], variation.name))
                        print(f"         ✅ Generated {len(result['content'].split())} words")
                    else:
                        print(f"         ❌ Generation failed")
                        
                except Exception as gen_error:
                    print(f"         ❌ Generation error: {gen_error}")
                    # Fall back to simulated content
                    simulated_content = self._create_simulated_post(topic, variation.name)
                    ai_posts.append((simulated_content, variation.name))
                    print(f"         📝 Using simulated content ({len(simulated_content.split())} words)")
                    
            except Exception as e:
                print(f"         ❌ Error generating with {variation.name}: {e}")
                continue
        
        return ai_posts
    
    def _generate_simulated_posts(self, prompt_variations: List[PromptVariation]) -> List[Tuple[str, str]]:
        """Generate simulated AI posts for testing"""
        
        simulated_posts = []
        
        base_topics = [
            "AI agents transforming B2B sales",
            "Micro-SaaS market emergence", 
            "Data teams driving revenue"
        ]
        
        for i, variation in enumerate(prompt_variations[:3]):
            topic = base_topics[i % len(base_topics)]
            content = self._create_simulated_post(topic, variation.name)
            simulated_posts.append((content, variation.name))
            print(f"      📝 Simulated post for {variation.name}: {len(content.split())} words")
        
        return simulated_posts
    
    def _create_simulated_post(self, topic: str, variation_name: str) -> str:
        """Create a simulated blog post for testing"""
        
        import random
        
        # Add variation to prevent stagnation
        openings = [
            f"The landscape of {topic.lower()} is shifting rapidly.",
            f"A quiet revolution is transforming {topic.lower()}.",
            f"The future of {topic.lower()} arrived ahead of schedule.",
            f"Traditional assumptions about {topic.lower()} no longer hold."
        ]
        
        questions = [
            "What happens when technology fundamentally changes how businesses operate?",
            "How do market leaders stay ahead of this transformation?",
            "What does this mean for competitive dynamics?",
            "Why are the smartest companies moving so quickly?"
        ]
        
        data_points = [
            "10x improvements", "66% cost reduction", "3x faster implementation", 
            "150x cost advantage", "90% efficiency gains", "5x return on investment"
        ]
        
        # Vary content based on variation name
        data_point = random.choice(data_points)
        opening = random.choice(openings)
        question = random.choice(questions)
        
        # Add slight variation based on iteration
        variation_factor = hash(variation_name) % 5
        
        return f"""{opening}

{question}

Companies across industries are discovering that {topic.lower()} represents more than incremental improvement. Early adopters are seeing dramatic results that suggest a fundamental shift in competitive dynamics.

Three factors drive this transformation. First, the technology has matured to enterprise readiness. Second, the cost-benefit equation has reached a tipping point. Third, competitive pressure forces rapid adoption.

The math is compelling for forward-thinking organizations. Traditional approaches cost significantly more while delivering inferior results. This technology offers {data_point} while reducing operational overhead.

However, successful implementation requires strategic thinking beyond simple technology adoption. The most effective organizations combine technological capability with process optimization and cultural change.

The companies that master this transformation will build sustainable competitive advantages in their respective markets.

--- Generated by {variation_name} variation (iteration factor: {variation_factor}) ---"""
    
    def _compare_with_published_posts(self, ai_posts: List[Tuple[str, str]], 
                                    published_posts: List) -> List[ComparisonScore]:
        """Compare AI posts with published posts"""
        
        comparison_results = []
        
        for i, (ai_content, prompt_name) in enumerate(ai_posts):
            # Use corresponding published post (round-robin)
            published_post = published_posts[i % len(published_posts)]
            
            # Extract topic
            topic = published_post.topic_tags[0] if published_post.topic_tags else "general"
            
            # Run comparison
            comparison = self.comparative_evaluator.comprehensive_comparison(
                ai_content, published_post, topic, prompt_name
            )
            
            comparison_results.append(comparison)
        
        return comparison_results
    
    def _check_convergence(self, iteration_result: Dict, iteration: int) -> bool:
        """Check if the system has converged or should continue"""
        
        current_best = iteration_result["best_score_this_iteration"]
        
        # Check for improvement
        if len(self.iteration_results) > 1:
            previous_best = self.iteration_results[-2]["best_score_this_iteration"]
            improvement = current_best - previous_best
            
            if improvement < self.convergence_threshold:
                self.stagnation_count += 1
                print(f"   📊 Low improvement: {improvement:+.1%} (stagnation: {self.stagnation_count})")
            else:
                self.stagnation_count = 0
                print(f"   📈 Good improvement: {improvement:+.1%}")
            
            # Stop if stagnating too long
            if self.stagnation_count >= self.max_stagnation:
                print(f"   ⚠️  Stopping due to stagnation ({self.stagnation_count} iterations)")
                return False
        
        # Stop if very high score achieved
        if current_best > 0.95:
            print(f"   🎯 Excellent score achieved: {current_best:.1%}")
            return False
        
        # Continue if under max iterations
        return iteration < self.max_iterations
    
    def _generate_final_summary(self) -> Dict:
        """Generate final summary of all iterations"""
        
        if not self.iteration_results:
            return {"error": "No iterations completed"}
        
        # Calculate total improvement
        first_score = self.iteration_results[0]["best_score_this_iteration"]
        final_score = self.iteration_results[-1]["best_score_this_iteration"]
        total_improvement = final_score - first_score
        
        # Find best iteration
        best_iteration = max(self.iteration_results, key=lambda r: r["best_score_this_iteration"])
        
        # Calculate average improvement per iteration
        improvements = []
        for i in range(1, len(self.iteration_results)):
            current = self.iteration_results[i]["best_score_this_iteration"]
            previous = self.iteration_results[i-1]["best_score_this_iteration"]
            improvements.append(current - previous)
        
        avg_improvement = sum(improvements) / len(improvements) if improvements else 0.0
        
        # Identify most effective optimization areas
        all_areas = []
        for result in self.iteration_results:
            for comparison in result["comparison_results"]:
                all_areas.extend(comparison["improvement_areas"])
        
        from collections import Counter
        common_areas = Counter(all_areas).most_common(5)
        
        final_summary = {
            "run_id": self.run_id,
            "total_iterations": len(self.iteration_results),
            "first_score": first_score,
            "final_score": final_score,
            "total_improvement": total_improvement,
            "avg_improvement_per_iteration": avg_improvement,
            "best_iteration": best_iteration["iteration"],
            "best_score": best_iteration["best_score_this_iteration"],
            "convergence_achieved": self.stagnation_count >= self.max_stagnation,
            "most_common_improvement_areas": [area for area, count in common_areas],
            "final_prompt": self.best_prompt,
            "performance_trajectory": [r["best_score_this_iteration"] for r in self.iteration_results]
        }
        
        return final_summary
    
    def _save_iteration_results(self, iteration: int, result: Dict) -> Path:
        """Save individual iteration results"""
        
        iteration_dir = self.run_dir / f"iteration_{iteration:02d}"
        iteration_dir.mkdir(exist_ok=True)
        
        result_file = iteration_dir / "iteration_results.json"
        with open(result_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        return result_file
    
    def _save_complete_results(self, final_summary: Dict) -> Path:
        """Save complete run results"""
        
        complete_results = {
            "final_summary": final_summary,
            "all_iterations": self.iteration_results,
            "run_metadata": {
                "run_id": self.run_id,
                "start_time": self.iteration_results[0]["timestamp"] if self.iteration_results else None,
                "end_time": datetime.now().isoformat(),
                "convergence_threshold": self.convergence_threshold,
                "max_stagnation": self.max_stagnation
            }
        }
        
        results_file = self.run_dir / "complete_results.json"
        with open(results_file, 'w') as f:
            json.dump(complete_results, f, indent=2)
        
        # Also save a readable summary
        summary_file = self.run_dir / "summary_report.md"
        self._generate_markdown_summary(complete_results, summary_file)
        
        print(f"💾 Complete results saved to: {results_file}")
        print(f"📄 Summary report saved to: {summary_file}")
        
        return results_file
    
    def _generate_markdown_summary(self, complete_results: Dict, output_file: Path):
        """Generate a readable markdown summary report"""
        
        summary = complete_results["final_summary"]
        
        markdown_content = f"""# Iterative Prompt Improvement Report

**Run ID:** {summary['run_id']}  
**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Executive Summary

- **Total Iterations:** {summary['total_iterations']}
- **Initial Score:** {summary['first_score']:.1%}
- **Final Score:** {summary['final_score']:.1%}
- **Total Improvement:** {summary['total_improvement']:+.1%}
- **Best Score Achieved:** {summary['best_score']:.1%} (Iteration {summary['best_iteration']})
- **Convergence:** {'✅ Achieved' if summary['convergence_achieved'] else '❌ Not reached'}

## Performance Trajectory

| Iteration | Best Score | Improvement |
|-----------|------------|-------------|
"""
        
        for i, score in enumerate(summary['performance_trajectory']):
            improvement = ""
            if i > 0:
                prev_score = summary['performance_trajectory'][i-1]
                improvement = f"{score - prev_score:+.1%}"
            markdown_content += f"| {i+1:2d} | {score:.1%} | {improvement} |\n"
        
        markdown_content += f"""
## Most Common Improvement Areas

{chr(10).join([f"- {area.replace('_', ' ').title()}" for area in summary['most_common_improvement_areas']])}

## Key Insights

1. **Average improvement per iteration:** {summary['avg_improvement_per_iteration']:+.1%}
2. **Most effective iteration:** #{summary['best_iteration']} with {summary['best_score']:.1%} score
3. **Convergence pattern:** {'Gradual improvement with eventual plateau' if summary['convergence_achieved'] else 'Continuous improvement trend'}

## Final Optimized Prompt

```
{summary.get('final_prompt', 'Not available')[:500]}...
```

---
*Generated by Iterative Prompt Improvement System*
"""
        
        with open(output_file, 'w') as f:
            f.write(markdown_content)


def main():
    """Main function to run iterative improvement"""
    
    parser = argparse.ArgumentParser(description="Run iterative prompt improvement")
    parser.add_argument("--iterations", type=int, default=10, help="Number of iterations to run")
    parser.add_argument("--convergence-threshold", type=float, default=0.02, help="Convergence threshold")
    parser.add_argument("--max-stagnation", type=int, default=3, help="Max stagnation iterations")
    parser.add_argument("--llm-judge", action="store_true", help="Use Gemini 2.5 Pro as LLM-as-judge for evaluation")
    
    args = parser.parse_args()
    
    if args.llm_judge:
        print("🤖 Using Gemini 2.5 Pro as LLM-as-judge for evaluation")
    
    # Initialize and run
    improver = IterativeImprover(max_iterations=args.iterations, use_llm_judge=args.llm_judge)
    improver.convergence_threshold = args.convergence_threshold
    improver.max_stagnation = args.max_stagnation
    
    # Run the complete cycle
    results = improver.run_complete_cycle(args.iterations)
    
    print(f"\n🎯 Final Results:")
    print(f"   Total Improvement: {results['total_improvement']:+.1%}")
    print(f"   Best Score: {results['best_score']:.1%}")
    print(f"   Iterations: {results['total_iterations']}")
    print(f"   Results: {improver.run_dir}")


if __name__ == "__main__":
    main()