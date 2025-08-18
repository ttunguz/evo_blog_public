#!/usr/bin/env python3
"""
Braintrust Integration for Evolutionary Blog Generator
Provides evaluation tracking and experiment logging
"""

import os
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import braintrust
from autoevals import Factuality, Battle

# Import from scripts directory
try:
    from evaluator import EvaluationScore
except ImportError:
    # Define a minimal EvaluationScore class for standalone use
    class EvaluationScore:
        def __init__(self):
            self.overall_score = 0
            self.overall_grade = "F"
            self.ready_to_ship = False
            self.scores = {}
            self.feedback = {}


class BraintrustTracker:
    """Tracks blog post generation experiments in Braintrust"""
    
    def __init__(self, project_name: str = "evo-blog-generator"):
        """Initialize Braintrust tracker"""
        self.project_name = project_name
        self.experiment = None
        self.current_session_id = None
        
        # Check for API key
        if not os.getenv('BRAINTRUST_API_KEY'):
            print("Warning: BRAINTRUST_API_KEY not set. Braintrust tracking disabled.")
            self.enabled = False
        else:
            self.enabled = True
            print(f"✅ Braintrust tracking enabled for project: {project_name}")
    
    def start_experiment(self, topic: str, title: str = "", metadata: Dict = None) -> str:
        """Start a new Braintrust experiment"""
        if not self.enabled:
            return "disabled"
        
        try:
            # Create experiment name with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            experiment_name = f"blog_generation_{timestamp}"
            
            # Prepare metadata
            exp_metadata = {
                "topic": topic,
                "title": title or "Untitled",
                "timestamp": timestamp,
                "framework": "evolutionary_blog_generator",
                **(metadata or {})
            }
            
            # Initialize experiment
            self.experiment = braintrust.init(
                project=self.project_name,
                experiment=experiment_name,
                metadata=exp_metadata
            )
            
            self.current_session_id = experiment_name
            print(f"🧠 Started Braintrust experiment: {experiment_name}")
            
            return experiment_name
            
        except Exception as e:
            print(f"Warning: Failed to start Braintrust experiment: {e}")
            self.enabled = False
            return "error"
    
    def log_generation(self, 
                      model: str, 
                      strategy: str, 
                      cycle: int,
                      prompt: str,
                      output: str,
                      cost: float,
                      tokens: int,
                      latency: float) -> None:
        """Log a single blog post generation"""
        if not self.enabled or not self.experiment:
            return
        
        try:
            # Use span logging to avoid toplevel log issues
            if hasattr(self.experiment, 'current_span') and self.experiment.current_span:
                self.experiment.current_span.log(
                    input={
                        "prompt": prompt,
                        "model": model,
                        "strategy": strategy,
                        "cycle": cycle
                    },
                    output=output,
                    scores={
                        "cost_efficiency": max(0, 1.0 - min(cost / 0.1, 1.0)),
                        "token_efficiency": max(0, 1.0 - min(tokens / 2000, 1.0)),
                        "speed": max(0, 1.0 - min(latency / 30.0, 1.0))
                    },
                    metadata={
                        "model": model,
                        "strategy": strategy,
                        "cycle": cycle,
                        "cost_usd": cost,
                        "tokens_used": tokens,
                        "latency_seconds": latency,
                        "generation_timestamp": datetime.now().isoformat()
                    },
                    tags=[f"cycle_{cycle}", model, strategy]
                )
            else:
                # Skip logging if experiment not properly initialized
                pass
            
        except Exception as e:
            print(f"Warning: Failed to log generation to Braintrust: {e}")
    
    def log_evaluation(self,
                      model: str,
                      strategy: str,
                      cycle: int,
                      content: str,
                      evaluation: EvaluationScore,
                      input_prompt: str = "") -> None:
        """Log evaluation results to Braintrust"""
        if not self.enabled or not self.experiment:
            return
        
        try:
            # Convert evaluation to scores dictionary (0-1 scale for Braintrust)
            scores = {
                "overall_score": evaluation.overall_score / 100.0,  # Convert to 0-1 scale
                "ready_to_ship": 1.0 if evaluation.ready_to_ship else 0.0,
                "content_quality": evaluation.scores.get("content_quality", 0) / 100.0,
                "writing_style": evaluation.scores.get("writing_style", 0) / 100.0,
                "structure": evaluation.scores.get("structure", 0) / 100.0,
                "data_usage": evaluation.scores.get("data_usage", 0) / 100.0,
                "grade_numeric": self._grade_to_numeric(evaluation.overall_grade) / 100.0
            }
            
            self.experiment.log(
                input={
                    "content": content,
                    "model": model,
                    "strategy": strategy,
                    "cycle": cycle,
                    "prompt": input_prompt
                },
                output={
                    "evaluation_result": evaluation.overall_grade,
                    "feedback": evaluation.feedback
                },
                scores=scores,
                metadata={
                    "evaluation_model": "claude_sonnet_4",
                    "evaluation_timestamp": datetime.now().isoformat(),
                    "evaluation_criteria": "ap_english_grading"
                },
                tags=[f"evaluation_cycle_{cycle}", model, strategy, "evaluated"]
            )
            
        except Exception as e:
            print(f"Warning: Failed to log evaluation to Braintrust: {e}")
    
    def log_best_post_selection(self,
                               best_post: Dict,
                               all_variations: List[Dict],
                               selection_criteria: str = "highest_score") -> None:
        """Log the final best post selection"""
        if not self.enabled or not self.experiment:
            return
        
        try:
            # Prepare comparison data
            comparison_data = {
                "selected_model": best_post['model'],
                "selected_strategy": best_post['strategy'],
                "selected_cycle": best_post['cycle'],
                "selected_score": best_post['score'],
                "total_variations": len(all_variations),
                "ready_posts_count": len([v for v in all_variations if v.get('ready', False)]),
                "score_distribution": {
                    "min": min(v['score'] for v in all_variations),
                    "max": max(v['score'] for v in all_variations),
                    "avg": sum(v['score'] for v in all_variations) / len(all_variations)
                }
            }
            
            self.experiment.log(
                input={
                    "task": "best_post_selection",
                    "criteria": selection_criteria,
                    "candidates": len(all_variations)
                },
                output={
                    "selected_post": best_post['content'][:500] + "...",
                    "selection_metadata": comparison_data
                },
                scores={
                    "final_score": best_post['score'] / 100.0,  # Convert to 0-1 scale
                    "final_grade_numeric": self._grade_to_numeric(best_post['grade']) / 100.0,
                    "ready_to_ship": 1.0 if best_post.get('ready', False) else 0.0
                },
                metadata={
                    "selection_timestamp": datetime.now().isoformat(),
                    "total_cost": sum(v.get('cost', 0) for v in all_variations)
                },
                tags=["final_selection", "best_post"]
            )
            
        except Exception as e:
            print(f"Warning: Failed to log best post selection to Braintrust: {e}")
    
    def finish_experiment(self, final_stats: Dict = None) -> str:
        """Finish the current experiment and return summary URL"""
        if not self.enabled or not self.experiment:
            return "disabled"
        
        try:
            # Log final summary if provided
            if final_stats:
                self.experiment.log(
                    input={"task": "experiment_summary"},
                    output=final_stats,
                    scores={
                        "experiment_success": 1.0 if final_stats.get('final_ready', False) else 0.5,
                        "cost_total": min(final_stats.get('total_cost', 0) / 1.0, 1.0),  # Normalized cost
                        "best_score_achieved": final_stats.get('final_best_score', 0) / 100.0
                    },
                    metadata={
                        "completion_timestamp": datetime.now().isoformat(),
                        "experiment_duration": final_stats.get('duration_seconds', 0)
                    },
                    tags=["experiment_summary"]
                )
            
            # Get experiment URL  
            experiment_url = None
            try:
                if hasattr(self.experiment, 'experiment') and hasattr(self.experiment.experiment, 'url'):
                    experiment_url = self.experiment.experiment.url
                elif hasattr(self.experiment, 'url'):
                    experiment_url = self.experiment.url
            except:
                pass
            
            print(f"🧠 Braintrust experiment completed")
            if experiment_url:
                print(f"📊 View results: {experiment_url}")
            
            return experiment_url or "completed"
            
        except Exception as e:
            print(f"Warning: Failed to finish Braintrust experiment: {e}")
            return "error"
        
        finally:
            self.experiment = None
            self.current_session_id = None
    
    def run_comparative_evaluation(self, posts: List[Dict], title: str = "") -> Dict:
        """Run comparative evaluation between posts using autoevals"""
        if not self.enabled:
            return {"error": "Braintrust not enabled"}
        
        try:
            results = {}
            
            # Factuality check for all posts
            print("Running factuality evaluation...")
            factuality_evaluator = Factuality()
            
            for i, post in enumerate(posts):
                fact_score = factuality_evaluator(
                    output=post['content'],
                    expected="High-quality blog post with accurate information"
                )
                results[f"post_{i}_factuality"] = fact_score
            
            # Battle evaluation (pairwise comparison)
            if len(posts) >= 2:
                print("Running pairwise battle evaluation...")
                battle_evaluator = Battle()
                
                # Compare top 2 posts
                battle_result = battle_evaluator(
                    output=posts[0]['content'],
                    expected=posts[1]['content']
                )
                results["battle_top_2"] = battle_result
            
            return results
            
        except Exception as e:
            print(f"Warning: Comparative evaluation failed: {e}")
            return {"error": str(e)}
    
    def _grade_to_numeric(self, grade: str) -> float:
        """Convert letter grade to numeric score"""
        grade_map = {
            "A+": 98.0, "A": 95.0, "A-": 92.0,
            "B+": 88.0, "B": 85.0, "B-": 82.0,
            "C+": 78.0, "C": 75.0, "C-": 72.0,
            "D": 65.0, "F": 50.0
        }
        return grade_map.get(grade, 0.0)


class BraintrustEvaluator:
    """Braintrust-based evaluator for blog posts"""
    
    def __init__(self, project_name: str = "evo-blog-evaluations"):
        self.project_name = project_name
        self.tracker = BraintrustTracker(project_name)
    
    def evaluate_blog_post_quality(self, 
                                  content: str, 
                                  expected_style: str = "tom_tunguz",
                                  metadata: Dict = None) -> Dict:
        """Evaluate blog post quality using Braintrust"""
        
        if not self.tracker.enabled:
            return {"error": "Braintrust not enabled"}
        
        try:
            # Start evaluation experiment
            eval_exp = braintrust.init(
                project=self.project_name,
                experiment=f"quality_eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            
            # Use autoevals for quality assessment
            factuality = Factuality()
            
            fact_result = factuality(
                output=content,
                expected="High-quality, factually accurate blog post"
            )
            
            # Log evaluation
            eval_exp.log(
                input={
                    "content": content,
                    "expected_style": expected_style,
                    "metadata": metadata or {}
                },
                output={
                    "factuality_score": fact_result
                },
                scores={
                    "factuality": fact_result.score if hasattr(fact_result, 'score') else 0.0
                },
                metadata={
                    "evaluator": "braintrust_quality_evaluator",
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            return {
                "factuality": fact_result,
                "experiment_url": eval_exp.experiment.url if hasattr(eval_exp, 'experiment') else None
            }
            
        except Exception as e:
            return {"error": f"Evaluation failed: {e}"}


# Integration helper functions
def setup_braintrust_for_blog_generator(api_key: str = None) -> bool:
    """Setup Braintrust for the blog generator"""
    
    if api_key:
        os.environ['BRAINTRUST_API_KEY'] = api_key
    
    # Check if API key is available
    if not os.getenv('BRAINTRUST_API_KEY'):
        print("❌ BRAINTRUST_API_KEY not found in environment")
        print("Set it with: export BRAINTRUST_API_KEY='your-api-key'")
        return False
    
    # Test connection
    try:
        test_tracker = BraintrustTracker("test-connection")
        if test_tracker.enabled:
            print("✅ Braintrust connection successful")
            return True
        else:
            print("❌ Braintrust connection failed")
            return False
    except Exception as e:
        print(f"❌ Braintrust setup error: {e}")
        return False


def create_braintrust_config() -> Dict:
    """Create default Braintrust configuration"""
    return {
        "enabled": True,
        "project_name": "evo-blog-generator",
        "log_generations": True,
        "log_evaluations": True,
        "log_comparisons": True,
        "run_factuality_checks": True,
        "auto_battle_evaluation": True,
        "experiment_tags": ["evolutionary", "blog", "generation"]
    }