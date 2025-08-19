#!/usr/bin/env python3
"""
Feedback Manager
Analyzes comparison results and generates prompt optimization recommendations
"""

import os
import sys
import json
import statistics
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict, Counter

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from comparative_evaluator import ComparisonScore
from prompt_generator import PromptVariation
from braintrust_integration import BraintrustTracker


@dataclass
class OptimizationRule:
    """Represents a specific optimization rule for prompts"""
    rule_name: str
    description: str
    target_score: str  # e.g., "style_similarity", "content_depth"
    improvement_text: str
    priority: float  # 0-1, higher is more important
    success_rate: float  # Historical success rate
    conditions: List[str]  # When to apply this rule


@dataclass
class FeedbackSummary:
    """Summary of feedback analysis across iterations"""
    iteration: int
    overall_improvement: float
    best_performing_prompt: str
    worst_performing_areas: List[str]
    optimization_recommendations: List[OptimizationRule]
    performance_trends: Dict[str, List[float]]
    confidence_score: float


class FeedbackManager:
    """Manages feedback analysis and prompt optimization recommendations"""
    
    def __init__(self, braintrust_tracker: Optional[BraintrustTracker] = None):
        self.braintrust_tracker = braintrust_tracker
        self.output_dir = Path(".//iterative_improvements")
        self.output_dir.mkdir(exist_ok=True)
        
        # Historical performance tracking
        self.performance_history: List[Dict] = []
        self.optimization_rules: List[OptimizationRule] = []
        
        # Initialize base optimization rules
        self._initialize_optimization_rules()
    
    def _initialize_optimization_rules(self):
        """Initialize base set of optimization rules"""
        
        base_rules = [
            OptimizationRule(
                rule_name="enhance_data_integration",
                description="Improve specific data point usage and company examples",
                target_score="data_usage_match",
                improvement_text="""
ENHANCED DATA REQUIREMENTS:
- MUST include at least 3 specific, quantified data points
- Use real company examples with exact metrics (e.g., "Stripe processed $640B in 2023")
- Include comparative data (e.g., "3x faster than", "50% more efficient")
- Cite recent studies or reports when possible
- Replace vague terms with specific numbers
""",
                priority=0.9,
                success_rate=0.75,
                conditions=["data_usage_match < 0.7"]
            ),
            
            OptimizationRule(
                rule_name="strengthen_voice_authenticity",
                description="Enhance Tom Tunguz voice characteristics",
                target_score="voice_authenticity",
                improvement_text="""
TOM TUNGUZ VOICE ENHANCEMENT:
- Use analytical confidence: state insights as established facts
- Include practical business implications for every major point
- Reference specific technology trends and market shifts
- Write from insider perspective with access to industry data
- Balance technical sophistication with business accessibility
- Use present tense for active trends, future tense for predictions
""",
                priority=0.85,
                success_rate=0.70,
                conditions=["voice_authenticity < 0.75", "style_similarity < 0.7"]
            ),
            
            OptimizationRule(
                rule_name="improve_structural_flow",
                description="Optimize paragraph structure and transitions",
                target_score="structural_match",
                improvement_text="""
ENHANCED STRUCTURE GUIDELINES:
- First paragraph: Single powerful statement (under 12 words)
- Second paragraph: Provocative question or contrarian observation
- Body paragraphs: Alternate between 2-sentence and 3-sentence paragraphs
- Use specific transition phrases: "However", "More importantly", "The result"
- Each paragraph should advance the core argument progressively
- Conclusion: Forward-looking statement that reinforces competitive advantage
""",
                priority=0.80,
                success_rate=0.65,
                conditions=["structural_match < 0.7"]
            ),
            
            OptimizationRule(
                rule_name="deepen_insight_quality",
                description="Enhance content depth and novelty",
                target_score="content_depth",
                improvement_text="""
INSIGHT DEPTH ENHANCEMENT:
- Lead with non-obvious industry observations
- Connect seemingly unrelated trends to business outcomes
- Include specific market timing analysis ("why now")
- Provide tactical implementation guidance
- Reference exclusive or hard-to-find data sources
- Challenge conventional wisdom with supporting evidence
""",
                priority=0.75,
                success_rate=0.60,
                conditions=["content_depth < 0.7"]
            ),
            
            OptimizationRule(
                rule_name="strengthen_opening_hook",
                description="Improve opening paragraph effectiveness",
                target_score="hook_effectiveness",
                improvement_text="""
POWERFUL OPENING REQUIREMENTS:
- First sentence: Bold, contrarian, or surprising statement
- Under 10 words for maximum impact
- Must immediately establish stakes or urgency
- Avoid generic industry observations
- Example patterns: "X is dead." "The future arrived early." "Everything changed last Tuesday."
""",
                priority=0.70,
                success_rate=0.80,
                conditions=["hook_effectiveness < 0.6"]
            ),
            
            OptimizationRule(
                rule_name="enhance_conclusion_impact",
                description="Strengthen conclusion effectiveness",
                target_score="conclusion_strength",
                improvement_text="""
IMPACTFUL CONCLUSION REQUIREMENTS:
- Tie directly back to opening hook
- Provide specific competitive advantage prediction
- Include actionable next steps or timeline
- Use confident future-oriented language
- End with business implication, not summary
""",
                priority=0.65,
                success_rate=0.75,
                conditions=["conclusion_strength < 0.6"]
            )
        ]
        
        self.optimization_rules = base_rules
    
    def identify_improvement_areas(self, comparison_results: List[ComparisonScore]) -> Dict[str, float]:
        """Identify consistent improvement areas across comparison results"""
        
        if not comparison_results:
            return {}
        
        # Aggregate scores across all comparisons
        score_aggregates = {
            "overall_similarity": [c.overall_similarity for c in comparison_results],
            "structural_match": [c.structural_match for c in comparison_results],
            "style_similarity": [c.style_similarity for c in comparison_results],
            "content_depth": [c.content_depth for c in comparison_results],
            "data_usage_match": [c.data_usage_match for c in comparison_results],
            "hook_effectiveness": [c.hook_effectiveness for c in comparison_results],
            "conclusion_strength": [c.conclusion_strength for c in comparison_results],
            "voice_authenticity": [c.voice_authenticity for c in comparison_results]
        }
        
        # Calculate average scores and identify weak areas
        avg_scores = {}
        for area, scores in score_aggregates.items():
            avg_scores[area] = statistics.mean(scores)
        
        # Sort by score (lowest first = highest priority for improvement)
        improvement_priorities = sorted(avg_scores.items(), key=lambda x: x[1])
        
        print(f"📊 Improvement Area Analysis:")
        for area, score in improvement_priorities:
            print(f"   {area}: {score:.1%}")
        
        return dict(improvement_priorities)
    
    def weight_feedback_importance(self, improvement_areas: Dict[str, float], 
                                 iteration: int) -> List[Tuple[str, float]]:
        """Weight feedback importance based on impact and iteration history"""
        
        # Base importance weights
        importance_weights = {
            "overall_similarity": 1.0,
            "style_similarity": 0.9,
            "content_depth": 0.85,
            "structural_match": 0.8,
            "data_usage_match": 0.75,
            "voice_authenticity": 0.9,
            "hook_effectiveness": 0.7,
            "conclusion_strength": 0.65
        }
        
        # Calculate weighted importance scores
        weighted_feedback = []
        
        for area, current_score in improvement_areas.items():
            base_weight = importance_weights.get(area, 0.5)
            
            # Increase importance for consistently low-scoring areas
            urgency_multiplier = 1.0
            if current_score < 0.6:
                urgency_multiplier = 1.5
            elif current_score < 0.7:
                urgency_multiplier = 1.2
            
            # Increase importance for areas that haven't improved over iterations
            stagnation_multiplier = 1.0
            if len(self.performance_history) > 2:
                # Check if this area has been consistently problematic
                recent_scores = [h.get(area, 0.5) for h in self.performance_history[-3:]]
                if all(score < 0.7 for score in recent_scores):
                    stagnation_multiplier = 1.3
            
            final_weight = base_weight * urgency_multiplier * stagnation_multiplier * (1.0 - current_score)
            weighted_feedback.append((area, final_weight))
        
        # Sort by importance (highest weight first)
        weighted_feedback.sort(key=lambda x: x[1], reverse=True)
        
        return weighted_feedback
    
    def generate_optimization_rules(self, weighted_feedback: List[Tuple[str, float]], 
                                  iteration: int) -> List[OptimizationRule]:
        """Generate specific optimization rules based on feedback"""
        
        applicable_rules = []
        
        for area, weight in weighted_feedback[:5]:  # Top 5 improvement areas
            # Find matching optimization rules
            for rule in self.optimization_rules:
                if rule.target_score == area or area in rule.target_score:
                    # Check if conditions are met
                    should_apply = True
                    for condition in rule.conditions:
                        # Simple condition parsing (in production, use proper parser)
                        if "<" in condition:
                            condition_area, threshold = condition.split(" < ")
                            threshold = float(threshold)
                            current_score = dict(weighted_feedback).get(condition_area, 1.0)
                            if not (1.0 - current_score > threshold):  # Convert weight back to score
                                should_apply = False
                                break
                    
                    if should_apply:
                        # Adjust priority based on current weight
                        adjusted_rule = OptimizationRule(
                            rule_name=rule.rule_name,
                            description=rule.description,
                            target_score=rule.target_score,
                            improvement_text=rule.improvement_text,
                            priority=rule.priority * (weight / max(w for _, w in weighted_feedback)),
                            success_rate=rule.success_rate,
                            conditions=rule.conditions
                        )
                        applicable_rules.append(adjusted_rule)
        
        # Sort by priority
        applicable_rules.sort(key=lambda r: r.priority, reverse=True)
        
        return applicable_rules[:3]  # Return top 3 rules
    
    def track_improvement_metrics(self, current_results: List[ComparisonScore], 
                                iteration: int) -> Dict[str, float]:
        """Track improvement metrics over iterations"""
        
        current_metrics = self.identify_improvement_areas(current_results)
        
        # Calculate improvement trends
        improvements = {}
        if len(self.performance_history) > 0:
            previous_metrics = self.performance_history[-1]
            for area, current_score in current_metrics.items():
                previous_score = previous_metrics.get(area, 0.0)
                improvement = current_score - previous_score
                improvements[f"{area}_improvement"] = improvement
        
        # Store current performance
        performance_record = {
            "iteration": iteration,
            "timestamp": datetime.now().isoformat(),
            **current_metrics,
            **improvements
        }
        
        self.performance_history.append(performance_record)
        
        return improvements
    
    def generate_feedback_summary(self, comparison_results: List[ComparisonScore],
                                prompt_variations: List[PromptVariation],
                                iteration: int) -> FeedbackSummary:
        """Generate comprehensive feedback summary"""
        
        print(f"📋 Generating feedback summary for iteration {iteration}...")
        
        # Identify improvement areas
        improvement_areas = self.identify_improvement_areas(comparison_results)
        
        # Weight feedback importance
        weighted_feedback = self.weight_feedback_importance(improvement_areas, iteration)
        
        # Generate optimization rules
        optimization_rules = self.generate_optimization_rules(weighted_feedback, iteration)
        
        # Track metrics
        improvements = self.track_improvement_metrics(comparison_results, iteration)
        
        # Calculate overall improvement
        overall_improvement = improvements.get("overall_similarity_improvement", 0.0)
        
        # Find best performing prompt variation
        if comparison_results and prompt_variations:
            best_idx = max(range(len(comparison_results)), 
                          key=lambda i: comparison_results[i].overall_similarity)
            best_performing_prompt = prompt_variations[best_idx].name if best_idx < len(prompt_variations) else "unknown"
        else:
            best_performing_prompt = "unknown"
        
        # Identify worst performing areas
        worst_areas = [area for area, score in improvement_areas.items() if score < 0.7][:3]
        
        # Build performance trends
        performance_trends = {}
        if len(self.performance_history) >= 2:
            for area in improvement_areas.keys():
                area_history = [h.get(area, 0.0) for h in self.performance_history[-5:]]  # Last 5 iterations
                performance_trends[area] = area_history
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(comparison_results, iteration)
        
        summary = FeedbackSummary(
            iteration=iteration,
            overall_improvement=overall_improvement,
            best_performing_prompt=best_performing_prompt,
            worst_performing_areas=worst_areas,
            optimization_recommendations=optimization_rules,
            performance_trends=performance_trends,
            confidence_score=confidence_score
        )
        
        # Save summary
        self._save_feedback_summary(summary)
        
        print(f"   📈 Overall improvement: {overall_improvement:+.1%}")
        print(f"   🏆 Best prompt: {best_performing_prompt}")
        print(f"   ⚠️  Focus areas: {', '.join(worst_areas)}")
        print(f"   🎯 Confidence: {confidence_score:.1%}")
        
        return summary
    
    def _calculate_confidence_score(self, comparison_results: List[ComparisonScore], 
                                  iteration: int) -> float:
        """Calculate confidence in the feedback recommendations"""
        
        if not comparison_results:
            return 0.0
        
        # Base confidence on result consistency
        overall_scores = [c.overall_similarity for c in comparison_results]
        consistency = 1.0 - (statistics.stdev(overall_scores) if len(overall_scores) > 1 else 0.0)
        
        # Increase confidence with more iterations
        iteration_confidence = min(iteration / 10.0, 1.0)
        
        # Decrease confidence if performance is declining
        decline_penalty = 0.0
        if len(self.performance_history) >= 3:
            recent_trend = [h.get("overall_similarity", 0.0) for h in self.performance_history[-3:]]
            if recent_trend[2] < recent_trend[0]:  # Declining performance
                decline_penalty = 0.2
        
        confidence = (consistency * 0.6 + iteration_confidence * 0.4) - decline_penalty
        return max(0.0, min(1.0, confidence))
    
    def _save_feedback_summary(self, summary: FeedbackSummary) -> Path:
        """Save feedback summary to file"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_file = self.output_dir / f"feedback_summary_iter{summary.iteration:02d}_{timestamp}.json"
        
        summary_data = {
            "iteration": summary.iteration,
            "timestamp": timestamp,
            "overall_improvement": summary.overall_improvement,
            "best_performing_prompt": summary.best_performing_prompt,
            "worst_performing_areas": summary.worst_performing_areas,
            "confidence_score": summary.confidence_score,
            "optimization_recommendations": [
                {
                    "rule_name": rule.rule_name,
                    "description": rule.description,
                    "target_score": rule.target_score,
                    "improvement_text": rule.improvement_text,
                    "priority": rule.priority,
                    "success_rate": rule.success_rate
                }
                for rule in summary.optimization_recommendations
            ],
            "performance_trends": summary.performance_trends,
            "performance_history": self.performance_history
        }
        
        with open(summary_file, 'w') as f:
            json.dump(summary_data, f, indent=2)
        
        print(f"💾 Feedback summary saved to: {summary_file}")
        return summary_file
    
    def create_next_iteration_prompt(self, summary: FeedbackSummary, 
                                   base_prompt: str) -> str:
        """Create optimized prompt for next iteration"""
        
        print(f"🔧 Creating optimized prompt for iteration {summary.iteration + 1}...")
        
        # Start with base prompt
        optimized_prompt = base_prompt
        
        # Apply top optimization rules
        for rule in summary.optimization_recommendations:
            print(f"   ✨ Applying: {rule.rule_name}")
            optimized_prompt += f"\n\n# {rule.rule_name.upper().replace('_', ' ')}\n{rule.improvement_text}"
        
        # Add iteration-specific guidance
        iteration_guidance = f"""

# ITERATION {summary.iteration + 1} FOCUS AREAS
Based on analysis of {summary.iteration} previous iterations:

PRIORITY IMPROVEMENTS:
{chr(10).join([f"- {area.replace('_', ' ').title()}" for area in summary.worst_performing_areas])}

CONFIDENCE LEVEL: {summary.confidence_score:.1%}
- High confidence (>80%): Follow recommendations precisely
- Medium confidence (60-80%): Test recommendations with variations  
- Low confidence (<60%): Use conservative improvements

PERFORMANCE TREND:
Overall improvement this iteration: {summary.overall_improvement:+.1%}
"""
        
        optimized_prompt += iteration_guidance
        
        return optimized_prompt


def main():
    """Test the feedback manager"""
    
    # Sample comparison results
    comparison_results = [
        ComparisonScore(
            overall_similarity=0.75,
            structural_match=0.80,
            style_similarity=0.65,
            content_depth=0.70,
            data_usage_match=0.60,
            hook_effectiveness=0.85,
            conclusion_strength=0.70,
            voice_authenticity=0.65,
            improvement_areas=["data_integration", "voice_authenticity"],
            specific_feedback={}
        ),
        ComparisonScore(
            overall_similarity=0.78,
            structural_match=0.75,
            style_similarity=0.70,
            content_depth=0.80,
            data_usage_match=0.65,
            hook_effectiveness=0.80,
            conclusion_strength=0.75,
            voice_authenticity=0.70,
            improvement_areas=["data_integration"],
            specific_feedback={}
        )
    ]
    
    # Sample prompt variations
    from prompt_generator import PromptVariation
    prompt_variations = [
        PromptVariation("enhanced_data", "Enhanced data integration", "test prompt", ["data"], 0.15, "v1.1"),
        PromptVariation("voice_enhanced", "Enhanced voice", "test prompt", ["voice"], 0.18, "v1.2")
    ]
    
    tracker = BraintrustTracker("feedback-management-test")
    manager = FeedbackManager(tracker)
    
    # Generate feedback summary
    summary = manager.generate_feedback_summary(comparison_results, prompt_variations, 1)
    
    print(f"\n📋 Feedback Summary:")
    print(f"Overall Improvement: {summary.overall_improvement:+.1%}")
    print(f"Best Prompt: {summary.best_performing_prompt}")
    print(f"Worst Areas: {', '.join(summary.worst_performing_areas)}")
    print(f"Confidence: {summary.confidence_score:.1%}")
    print(f"Optimization Rules: {len(summary.optimization_recommendations)}")


if __name__ == "__main__":
    main()