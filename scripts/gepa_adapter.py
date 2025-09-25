#!/usr/bin/env python3
"""
GEPA Adapter for Blog Post Generation

This module provides the GEPA (Genetic Evolution Program Assistant) adapter
for optimizing blog post generation components including system prompts,
style guides, and content structures.
"""

import asyncio
import re
import time
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import numpy as np

# GEPA imports
try:
    from gepa import optimize, GEPAAdapter, GEPAResult, EvaluationBatch
    GEPA_AVAILABLE = True
except ImportError:
    GEPA_AVAILABLE = False
    print("Warning: GEPA not available. Install with: pip install gepa")

    # Mock classes for when GEPA is not available
    class EvaluationBatch:
        def __init__(self, metrics=None, traces=None):
            self.metrics = metrics or []
            self.traces = traces or []


@dataclass
class BlogPostDataInstance:
    """Data instance for GEPA optimization containing blog requirements."""
    source_content: str
    prompt: str
    target_categories: List[str]
    expected_quality_score: Optional[float] = None


@dataclass
class StyleAnalysis:
    """Style analysis for blog generation."""
    common_patterns: List[str]
    avg_paragraph_length: int
    hook_examples: List[str]
    conclusion_examples: List[str]
    tone_characteristics: List[str]


class BlogPostGEPAAdapter:
    """GEPA Adapter for optimizing blog post generation components."""

    def __init__(self, blog_generator):
        """
        Initialize the GEPA adapter.

        Args:
            blog_generator: The main BlogGenerator instance
        """
        self.generator = blog_generator
        self.evaluation_cache = {}

    def evaluate(self, batch: List[BlogPostDataInstance],
                candidate: Dict[str, str],
                capture_traces: bool = False) -> EvaluationBatch:
        """
        Evaluate candidate components on a batch of blog post instances.

        Args:
            batch: List of BlogPostDataInstance objects
            candidate: Single component dictionary with text values
            capture_traces: Whether to capture execution traces

        Returns:
            EvaluationBatch object with metrics and traces
        """
        candidate_metrics = []
        traces = []

        for instance in batch:
            # Extract components from candidate
            system_prompt = candidate.get("system_prompt", "")
            content_structure = candidate.get("content_structure", "")
            style_guide = candidate.get("style_guide", "")

            # Generate blog post using these components
            try:
                # Create modified style analysis with candidate components
                style_analysis = self._create_custom_style_analysis(
                    style_guide, content_structure)

                # Generate a single variant using the optimized components
                variant_result = asyncio.run(self._generate_optimized_variant(
                    instance.source_content,
                    instance.prompt,
                    system_prompt,
                    style_analysis
                ))

                if variant_result and variant_result.get('content'):
                    # Evaluate the variant using the blog generator's evaluator
                    evaluation = self.generator.evaluator.evaluate(
                        variant_result['content'],
                        instance.prompt
                    )

                    # Calculate additional scores
                    originality = self._calculate_originality_score(variant_result['content'])
                    style_consistency = self._calculate_style_consistency_score(
                        variant_result['content'], instance.target_categories)
                    generation_speed = 1.0 / max(variant_result.get('generation_time', 1.0), 0.1)

                    metrics = {
                        "quality_score": evaluation.overall_score / 100.0,
                        "fitness_score": evaluation.overall_score / 100.0,  # Simplified fitness
                        "originality_score": originality,
                        "style_consistency_score": style_consistency,
                        "generation_speed": generation_speed
                    }

                    if capture_traces:
                        trace = f"Generated: {variant_result.get('title', 'Untitled')} (Score: {evaluation.overall_score}, Grade: {evaluation.overall_grade})"
                        traces.append(trace)
                else:
                    # Failed generation
                    metrics = {
                        "quality_score": 0.0,
                        "fitness_score": 0.0,
                        "originality_score": 0.0,
                        "style_consistency_score": 0.0,
                        "generation_speed": 0.0
                    }

                    if capture_traces:
                        traces.append("Generation failed for instance")

            except Exception as e:
                print(f"Error evaluating candidate: {e}")
                metrics = {
                    "quality_score": 0.0,
                    "fitness_score": 0.0,
                    "originality_score": 0.0,
                    "style_consistency_score": 0.0,
                    "generation_speed": 0.0
                }

                if capture_traces:
                    traces.append(f"Error: {str(e)}")

            candidate_metrics.append(metrics)

        # Aggregate metrics across instances
        if candidate_metrics:
            aggregated_metrics = {
                "quality_score": np.mean([m["quality_score"] for m in candidate_metrics]),
                "fitness_score": np.mean([m["fitness_score"] for m in candidate_metrics]),
                "originality_score": np.mean([m["originality_score"] for m in candidate_metrics]),
                "style_consistency_score": np.mean([m["style_consistency_score"] for m in candidate_metrics]),
                "generation_speed": np.mean([m["generation_speed"] for m in candidate_metrics])
            }
        else:
            aggregated_metrics = {
                "quality_score": 0.0,
                "fitness_score": 0.0,
                "originality_score": 0.0,
                "style_consistency_score": 0.0,
                "generation_speed": 0.0
            }

        # Return EvaluationBatch object
        return EvaluationBatch(
            metrics=[aggregated_metrics],
            traces=traces if capture_traces else []
        )

    def make_reflective_dataset(self, batch: List[BlogPostDataInstance]) -> List[Dict[str, str]]:
        """
        Create a reflective dataset for GEPA optimization.

        Args:
            batch: List of BlogPostDataInstance objects

        Returns:
            List of component dictionaries that can be optimized
        """
        # Define components that GEPA can optimize
        components = [
            {
                "system_prompt": "You are an expert business writer creating insightful blog content.",
                "style_guide": "Professional, data-driven content with specific examples",
                "content_structure": "Hook opening, supporting evidence, clear conclusion"
            },
            {
                "system_prompt": "You are a thought leader writing compelling business insights.",
                "style_guide": "Conversational yet authoritative, challenging conventional wisdom",
                "content_structure": "Problem statement, analysis, solution framework"
            },
            {
                "system_prompt": "You are creating high-quality content for business leaders.",
                "style_guide": "Direct, actionable insights with real-world examples",
                "content_structure": "Clear thesis, supporting data, practical implications"
            }
        ]

        return components

    def _create_custom_style_analysis(self, style_guide: str, content_structure: str) -> StyleAnalysis:
        """Create a StyleAnalysis object from GEPA-optimized components."""
        # Parse style guide and content structure
        patterns = []
        tone_chars = []

        if style_guide:
            # Extract style patterns
            if "data-driven" in style_guide.lower():
                patterns.append("Data-driven insights with specific statistics")
            if "conversational" in style_guide.lower():
                patterns.append("Direct, conversational tone")
            if "examples" in style_guide.lower():
                patterns.append("Industry examples and analogies")

            # Extract tone characteristics
            if "professional" in style_guide.lower():
                tone_chars.append("Professional but accessible")
            if "specific" in style_guide.lower():
                tone_chars.append("Uses specific examples and data")
            if "challenging" in style_guide.lower():
                tone_chars.append("Challenges conventional wisdom")

        # Use defaults if not specified
        if not patterns:
            patterns = ["Clear, engaging content", "Evidence-based arguments"]
        if not tone_chars:
            tone_chars = ["Professional tone", "Reader-focused insights"]

        return StyleAnalysis(
            common_patterns=patterns,
            avg_paragraph_length=100,  # Default
            hook_examples=["Engaging opening statement"],
            conclusion_examples=["Strong closing argument"],
            tone_characteristics=tone_chars
        )

    async def _generate_optimized_variant(self, source_content: str, prompt: str,
                                        system_prompt: str, style_analysis: StyleAnalysis) -> Optional[Dict[str, Any]]:
        """Generate a single variant using optimized components."""

        # Combine optimized system prompt with style analysis
        enhanced_system_prompt = f"""
        {system_prompt}

        Style Requirements:
        - {', '.join(style_analysis.tone_characteristics)}
        - Use patterns: {', '.join(style_analysis.common_patterns)}
        - Paragraph length target: ~{style_analysis.avg_paragraph_length} words
        """

        user_prompt = f"""
        Source content: {source_content}

        Blog post prompt: {prompt}

        Generate a complete blog post following the system requirements.
        """

        try:
            start_time = time.time()

            # Use the blog generator's models to generate content
            if hasattr(self.generator, 'models') and 'claude' in self.generator.models:
                claude_client = self.generator.models['claude']
                response = claude_client.generate(
                    user_prompt,
                    system_prompt=enhanced_system_prompt,
                    temperature=0.7,
                    max_tokens=1500
                )

                if response and not response.error:
                    generation_time = time.time() - start_time

                    # Extract title from content
                    content = response.content
                    title_match = re.search(r'title:\s*["\']?([^"\'\n]+)["\']?', content, re.IGNORECASE)
                    if not title_match:
                        # Try to extract from first line
                        lines = content.strip().split('\n')
                        title = lines[0].strip() if lines else "Generated Post"
                    else:
                        title = title_match.group(1)

                    return {
                        'title': title,
                        'content': content,
                        'generation_time': generation_time,
                        'model': 'claude-gepa-optimized'
                    }

            return None

        except Exception as e:
            print(f"Error generating optimized variant: {e}")
            return None

    def _calculate_originality_score(self, content: str) -> float:
        """Calculate originality score (simplified implementation)."""
        # Simplified originality check based on content length and variety
        words = content.split()
        unique_words = set(word.lower() for word in words)

        if len(words) == 0:
            return 0.0

        variety_score = len(unique_words) / len(words)
        length_bonus = min(len(words) / 500, 1.0)  # Bonus for appropriate length

        return (variety_score * 0.7 + length_bonus * 0.3)

    def _calculate_style_consistency_score(self, content: str, target_categories: List[str]) -> float:
        """Calculate style consistency score (simplified implementation)."""
        content_lower = content.lower()

        # Check for business/professional language markers
        professional_markers = ['data', 'analysis', 'strategy', 'business', 'company', 'market']
        marker_count = sum(1 for marker in professional_markers if marker in content_lower)

        # Check for specific examples
        example_markers = ['for example', 'such as', 'like', 'including']
        example_count = sum(1 for marker in example_markers if marker in content_lower)

        # Basic scoring
        marker_score = min(marker_count / len(professional_markers), 1.0)
        example_score = min(example_count / 3, 1.0)  # Expect at least 3 examples

        return (marker_score * 0.6 + example_score * 0.4)


async def run_gepa_optimization(blog_generator, topic: str, title: str = "",
                               gepa_iterations: int = 10) -> Dict[str, Any]:
    """
    Run GEPA optimization for blog post generation.

    Args:
        blog_generator: The BlogGenerator instance
        topic: Blog post topic
        title: Optional title
        gepa_iterations: Number of optimization iterations

    Returns:
        Dict containing the optimized blog post and metadata
    """

    if not GEPA_AVAILABLE:
        print("⚠️  GEPA not available, falling back to standard generation")
        return None

    print(f"🧬 Starting GEPA optimization with {gepa_iterations} iterations...")

    # Create training data instances
    training_instances = [
        BlogPostDataInstance(
            source_content=topic,
            prompt=title or topic,
            target_categories=["business", "technology", "analysis"],
            expected_quality_score=90.0
        )
    ]

    # Initialize GEPA adapter
    adapter = BlogPostGEPAAdapter(blog_generator)

    # Define seed candidate components to optimize
    seed_candidate = {
        "system_prompt": """
        You are an expert blog writer specializing in technology and business content.
        Write engaging, data-driven posts that challenge conventional thinking.
        Use specific examples and maintain a professional but accessible tone.
        """,
        "style_guide": """
        Professional tone with conversational elements. Use data-driven insights
        with specific statistics. Include industry examples and analogies.
        Challenge conventional wisdom with evidence-based arguments.
        """,
        "content_structure": """
        Start with compelling hook. Build context, present problem, provide solution.
        Use varied paragraph lengths. Mix short punchy sentences with longer explanatory ones.
        End with strong conclusion that ties back to opening.
        """
    }

    try:
        # Run GEPA optimization
        print(f"  Running {gepa_iterations} optimization iterations...")
        gepa_result = optimize(
            seed_candidate=seed_candidate,
            trainset=training_instances,
            valset=training_instances[:1],  # Use subset for validation
            adapter=adapter,
            max_metric_calls=gepa_iterations * len(training_instances),
            reflection_lm="gpt-4o",  # Use GPT-4 for reflection
            display_progress_bar=True
        )

        print(f"✅ GEPA optimization completed!")
        print(f"📈 Best fitness achieved: {gepa_result.best_score:.3f}")

        # Generate final blog post using optimized components
        optimized_components = gepa_result.best_candidate

        # Create style analysis from optimized components
        style_analysis = adapter._create_custom_style_analysis(
            optimized_components.get("style_guide", ""),
            optimized_components.get("content_structure", "")
        )

        # Generate final variant
        final_result = await adapter._generate_optimized_variant(
            topic,
            title or topic,
            optimized_components.get("system_prompt", ""),
            style_analysis
        )

        if final_result:
            print(f"🏆 GEPA-optimized post generated successfully")
            print(f"   Title: {final_result['title']}")

            # Evaluate the final result
            evaluation = blog_generator.evaluator.evaluate(final_result['content'], topic)

            return {
                'content': final_result['content'],
                'title': final_result['title'],
                'model': 'claude-gepa-optimized',
                'score': evaluation.overall_score,
                'grade': evaluation.overall_grade,
                'ready': evaluation.ready_to_ship,
                'evaluation': evaluation,
                'optimized_components': optimized_components,
                'gepa_score': gepa_result.best_score
            }
        else:
            print("❌ Failed to generate final variant")
            return None

    except Exception as e:
        print(f"❌ GEPA optimization failed: {e}")
        print("🔄 Falling back to standard generation")
        return None