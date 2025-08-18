#!/usr/bin/env python3
"""
Prompt Generator
Generates improved prompts based on analysis of published posts and AI performance gaps
"""

import os
import sys
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from post_analyzer import StyleAnalysis, PostAnalyzer
from braintrust_integration import BraintrustTracker


@dataclass
class PromptVariation:
    """Represents a prompt variation for testing"""
    name: str
    description: str
    prompt_text: str
    target_improvements: List[str]
    expected_score_improvement: float
    version: str


class PromptGenerator:
    """Generates improved prompts based on style analysis and performance gaps"""
    
    def __init__(self, braintrust_tracker: Optional[BraintrustTracker] = None):
        self.braintrust_tracker = braintrust_tracker
        self.output_dir = Path("/Users/tomasztunguz/Documents/coding/evo_blog/iterative_improvements")
        self.output_dir.mkdir(exist_ok=True)
        
        # Load current base prompt from generate_blog_post.py
        self.base_prompt = self._load_current_prompt()
        self.prompt_variations: List[PromptVariation] = []
    
    def _load_current_prompt(self) -> str:
        """Extract current prompt from generate_blog_post.py"""
        
        try:
            generator_file = Path(__file__).parent / "generate_blog_post.py"
            with open(generator_file, 'r') as f:
                content = f.read()
            
            # Extract the style guide section
            style_start = content.find('style_guide = """')
            if style_start == -1:
                raise ValueError("Style guide not found in generate_blog_post.py")
            
            style_start += len('style_guide = """')
            style_end = content.find('"""', style_start)
            
            if style_end == -1:
                raise ValueError("Style guide end not found")
            
            return content[style_start:style_end].strip()
            
        except Exception as e:
            print(f"Warning: Could not load current prompt: {e}")
            return self._get_fallback_prompt()
    
    def _get_fallback_prompt(self) -> str:
        """Fallback prompt if we can't load from file"""
        return """
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

STYLE CHARACTERISTICS:
- Include 2-3 specific data points or statistics from real sources
- Use concrete examples from real companies
- Avoid business clichés and adverbs
- Maximum 2 colons in the entire post
- Write concisely and directly - every word counts
"""
    
    def analyze_prompt_gaps(self, style_analysis: StyleAnalysis, 
                           performance_feedback: Optional[Dict] = None) -> List[str]:
        """Identify gaps between current prompt and published post patterns"""
        
        gaps = []
        
        # Analyze style patterns vs current prompt
        if style_analysis.avg_paragraph_length < 30:
            gaps.append("paragraphs_too_short")
        elif style_analysis.avg_paragraph_length > 60:
            gaps.append("paragraphs_too_long")
        
        if style_analysis.data_points_per_post < 2:
            gaps.append("insufficient_data_points")
        
        # Check for specific voice characteristics
        voice_keywords = ["analytical", "data-driven", "practical", "forward-looking"]
        for keyword in voice_keywords:
            if keyword not in self.base_prompt.lower():
                gaps.append(f"missing_voice_{keyword}")
        
        # Add performance-based gaps
        if performance_feedback:
            low_scores = [k for k, v in performance_feedback.items() if v < 0.7]
            gaps.extend([f"low_{score}" for score in low_scores])
        
        return gaps
    
    def generate_prompt_variations(self, style_analysis: StyleAnalysis, 
                                  gaps: List[str], iteration: int = 1) -> List[PromptVariation]:
        """Generate improved prompt variations"""
        
        variations = []
        version_prefix = f"v{iteration}"
        
        # Variation 1: Enhanced Data Integration
        if "insufficient_data_points" in gaps or "low_content_quality" in gaps:
            enhanced_data_prompt = self._create_enhanced_data_prompt(style_analysis)
            variations.append(PromptVariation(
                name="enhanced_data_integration",
                description="Emphasizes specific data points and company examples",
                prompt_text=enhanced_data_prompt,
                target_improvements=["data_usage", "content_quality"],
                expected_score_improvement=0.15,
                version=f"{version_prefix}.1"
            ))
        
        # Variation 2: Improved Structure Flow
        if "paragraphs_too_long" in gaps or "low_structure" in gaps:
            structured_flow_prompt = self._create_structured_flow_prompt(style_analysis)
            variations.append(PromptVariation(
                name="structured_flow",
                description="Optimizes paragraph length and transitions",
                prompt_text=structured_flow_prompt,
                target_improvements=["structure", "writing_style"],
                expected_score_improvement=0.12,
                version=f"{version_prefix}.2"
            ))
        
        # Variation 3: Voice Enhancement
        if any("missing_voice" in gap for gap in gaps) or "low_writing_style" in gaps:
            voice_enhanced_prompt = self._create_voice_enhanced_prompt(style_analysis)
            variations.append(PromptVariation(
                name="voice_enhanced",
                description="Strengthens Tom Tunguz voice characteristics",
                prompt_text=voice_enhanced_prompt,
                target_improvements=["writing_style", "voice_match"],
                expected_score_improvement=0.18,
                version=f"{version_prefix}.3"
            ))
        
        # Variation 4: Topic-Specific Optimization
        top_topics = list(style_analysis.topic_distribution.keys())[:2]
        if top_topics:
            topic_optimized_prompt = self._create_topic_optimized_prompt(style_analysis, top_topics)
            variations.append(PromptVariation(
                name="topic_optimized",
                description=f"Optimized for {', '.join(top_topics)} topics",
                prompt_text=topic_optimized_prompt,
                target_improvements=["content_relevance", "topic_depth"],
                expected_score_improvement=0.10,
                version=f"{version_prefix}.4"
            ))
        
        # Variation 5: Comprehensive Enhancement
        comprehensive_prompt = self._create_comprehensive_prompt(style_analysis, gaps)
        variations.append(PromptVariation(
            name="comprehensive",
            description="Combines all identified improvements",
            prompt_text=comprehensive_prompt,
            target_improvements=["overall_quality", "style_match", "structure"],
            expected_score_improvement=0.25,
            version=f"{version_prefix}.5"
        ))
        
        self.prompt_variations = variations
        return variations
    
    def _create_enhanced_data_prompt(self, style_analysis: StyleAnalysis) -> str:
        """Create prompt with enhanced data integration"""
        
        data_emphasis = f"""
CRITICAL DATA REQUIREMENTS:
- MUST include exactly {int(style_analysis.data_points_per_post)} specific data points or statistics
- Use real company examples with specific metrics (revenue, growth rates, user counts)
- Include percentages, dollar amounts, or quantified comparisons
- Examples: "Klarna reduced costs by 66%", "ARR grew from $10M to $50M", "conversion rates improved 3x"
- If you don't know exact figures, use [NEEDS DATA: description] placeholders
- Prefer recent data from 2024-2025 when possible
"""
        
        return self.base_prompt + data_emphasis
    
    def _create_structured_flow_prompt(self, style_analysis: StyleAnalysis) -> str:
        """Create prompt with improved structure and flow"""
        
        target_para_length = int(style_analysis.avg_paragraph_length)
        
        structure_emphasis = f"""
ENHANCED STRUCTURE REQUIREMENTS:
- Target paragraph length: {target_para_length} words per paragraph
- Use these specific transition patterns: {', '.join(style_analysis.common_transitions[:3])}
- First paragraph: Bold declarative statement (1 sentence, under 10 words)
- Second paragraph: Thought-provoking question or contrarian observation
- Body paragraphs: Mix of 2-sentence and 3-sentence paragraphs for rhythm
- Each paragraph must flow logically to the next with clear connective tissue
- Conclusion: Forward-looking statement that reinforces the main insight
"""
        
        return self.base_prompt + structure_emphasis
    
    def _create_voice_enhanced_prompt(self, style_analysis: StyleAnalysis) -> str:
        """Create prompt with enhanced Tom Tunguz voice"""
        
        voice_emphasis = f"""
TOM TUNGUZ VOICE AMPLIFICATION:
- Channel these specific characteristics: {', '.join(style_analysis.voice_characteristics)}
- Write with analytical confidence - state insights as facts, not opinions
- Use present tense for trends: "Companies are discovering..." not "Companies will discover..."
- Include practical implications: "This means..." or "The result is..."
- Avoid hedge words: "perhaps", "maybe", "could be"
- Write as an industry insider with deep expertise
- Balance optimism about technology with practical business realities
- Reference specific companies and real examples, not hypothetical scenarios
"""
        
        return self.base_prompt + voice_emphasis
    
    def _create_topic_optimized_prompt(self, style_analysis: StyleAnalysis, topics: List[str]) -> str:
        """Create prompt optimized for specific topics"""
        
        topic_guidance = {}
        
        if "SaaS" in topics:
            topic_guidance["SaaS"] = "Focus on metrics like ARR, churn, LTV/CAC, expansion revenue. Reference successful SaaS companies and their growth strategies."
        
        if "AI" in topics:
            topic_guidance["AI"] = "Emphasize practical business applications, not theoretical capabilities. Include real implementation examples and measurable business impact."
        
        if "data" in topics:
            topic_guidance["data"] = "Focus on actionable insights and business outcomes. Avoid technical jargon in favor of business impact and ROI."
        
        topic_emphasis = f"""
TOPIC-SPECIFIC GUIDANCE:
{chr(10).join([f"- {topic}: {guidance}" for topic, guidance in topic_guidance.items()])}

INDUSTRY CONTEXT:
- Assume audience of founders, VCs, and business leaders
- Focus on practical applications and business impact
- Include relevant market sizing and trend data when available
"""
        
        return self.base_prompt + topic_emphasis
    
    def _create_comprehensive_prompt(self, style_analysis: StyleAnalysis, gaps: List[str]) -> str:
        """Create comprehensive prompt addressing all gaps"""
        
        # Combine all enhancements
        comprehensive_additions = f"""
COMPREHENSIVE OPTIMIZATION (Version C):

DATA & EXAMPLES:
- Include {int(style_analysis.data_points_per_post)} specific data points with sources
- Use real company case studies with quantified outcomes
- Prefer recent examples from 2024-2025
- Include market context and competitive landscape when relevant

STRUCTURE & FLOW:
- Target {int(style_analysis.avg_paragraph_length)} words per paragraph
- Use proven transition patterns: {', '.join(style_analysis.common_transitions[:2])}
- Vary paragraph length: short (1-2 sentences) and medium (3-4 sentences)
- Create logical progression: context → problem → analysis → solution

VOICE AUTHENTICITY:
- Channel Tom's analytical confidence and industry expertise
- Write as an insider with access to non-public insights
- Balance technological optimism with business pragmatism
- Use specific, concrete language over abstract concepts
- Include practical "what this means" implications

QUALITY MARKERS:
- Every paragraph serves a specific purpose in the argument
- Insights feel novel and non-obvious to industry experts
- Conclusion provides actionable next steps or predictions
- Overall thesis is defensible and well-supported with evidence
"""
        
        return self.base_prompt + comprehensive_additions
    
    def save_variations(self, iteration: int) -> Path:
        """Save prompt variations to file"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        variations_file = self.output_dir / f"prompt_variations_iter{iteration:02d}_{timestamp}.json"
        
        variations_data = {
            "iteration": iteration,
            "timestamp": timestamp,
            "base_prompt": self.base_prompt,
            "variations": [
                {
                    "name": v.name,
                    "description": v.description,
                    "prompt_text": v.prompt_text,
                    "target_improvements": v.target_improvements,
                    "expected_score_improvement": v.expected_score_improvement,
                    "version": v.version
                }
                for v in self.prompt_variations
            ]
        }
        
        with open(variations_file, 'w') as f:
            json.dump(variations_data, f, indent=2)
        
        print(f"💾 Prompt variations saved to: {variations_file}")
        return variations_file
    
    def get_best_variation_for_testing(self) -> PromptVariation:
        """Get the variation with highest expected improvement for testing"""
        
        if not self.prompt_variations:
            raise ValueError("No prompt variations generated")
        
        return max(self.prompt_variations, key=lambda v: v.expected_score_improvement)
    
    def generate_iterative_improvements(self, style_analysis: StyleAnalysis, 
                                      previous_results: Optional[Dict] = None,
                                      iteration: int = 1) -> List[PromptVariation]:
        """Main function to generate improved prompts"""
        
        print(f"🚀 Generating prompt improvements for iteration {iteration}...")
        
        # Analyze gaps
        performance_feedback = previous_results.get('performance_scores', {}) if previous_results else None
        gaps = self.analyze_prompt_gaps(style_analysis, performance_feedback)
        
        print(f"   🔍 Identified gaps: {', '.join(gaps)}")
        
        # Generate variations
        variations = self.generate_prompt_variations(style_analysis, gaps, iteration)
        
        print(f"   ✨ Generated {len(variations)} prompt variations")
        for v in variations:
            print(f"      • {v.name}: targeting {'+'.join(v.target_improvements)} (+{v.expected_score_improvement:.1%})")
        
        # Save to file
        self.save_variations(iteration)
        
        # Log to Braintrust
        if self.braintrust_tracker:
            for variation in variations:
                self.braintrust_tracker.log_generation(
                    model="prompt_generator",
                    strategy=variation.name,
                    cycle=iteration,
                    prompt=f"Generate improved prompt: {variation.description}",
                    output=variation.prompt_text,
                    cost=0.0,
                    tokens=len(variation.prompt_text.split()),
                    latency=0.1
                )
        
        return variations


def main():
    """Test the prompt generator"""
    
    # Create sample style analysis
    style_analysis = StyleAnalysis(
        avg_paragraph_length=45.0,
        avg_sentence_length=18.0,
        data_points_per_post=2.5,
        common_transitions=["However", "More importantly", "The transformation"],
        hook_patterns=["question_opening", "bold_statement"],
        conclusion_patterns=["future_prediction", "competitive_advantage"],
        voice_characteristics=["analytical", "data-driven", "practical"],
        topic_distribution={"SaaS": 8, "AI": 6, "data": 4}
    )
    
    tracker = BraintrustTracker("prompt-generation-test")
    generator = PromptGenerator(tracker)
    
    # Generate improvements
    variations = generator.generate_iterative_improvements(style_analysis, iteration=1)
    
    print("\n📋 Generated Variations:")
    for v in variations:
        print(f"\n{v.name} ({v.version}):")
        print(f"  Description: {v.description}")
        print(f"  Targets: {', '.join(v.target_improvements)}")
        print(f"  Expected improvement: +{v.expected_score_improvement:.1%}")


if __name__ == "__main__":
    main()