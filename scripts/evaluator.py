#!/usr/bin/env python3
"""
Blog Post Evaluation System
Evaluates generated blog posts against Tom Tunguz's writing style and quality standards
"""

import re
import json
from typing import Dict, List, Tuple
from dataclasses import dataclass
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))
from models import ClaudeClient


@dataclass
class EvaluationScore:
    """Represents the evaluation score for a blog post"""
    grammatical_correctness: float  # 0-100
    argument_strength: float  # 0-100
    style_match: float  # 0-100
    cliche_absence: float  # 0-100
    brevity_score: float  # 0-100
    overall_grade: str  # A+, A, A-, B+, B, B-, C+, etc.
    overall_score: float  # 0-100
    feedback: Dict[str, str]
    ready_to_ship: bool  # True if B+ or better


class BlogEvaluator:
    """Evaluates blog posts against Tom Tunguz's style and quality standards"""
    
    # Common clichés to avoid
    CLICHES = [
        "at the end of the day", "low-hanging fruit", "game-changer", 
        "paradigm shift", "move the needle", "boil the ocean",
        "think outside the box", "win-win", "synergy", "leverage",
        "circle back", "touch base", "deep dive", "best practice",
        "cutting edge", "state of the art", "next generation",
        "revolutionary", "breakthrough", "innovative solution",
        "seamlessly", "robust", "scalable solution", "best-in-class",
        "world-class", "industry-leading", "transformative",
        "disruptive", "groundbreaking", "unprecedented"
    ]
    
    # Tom's writing style characteristics - Updated to match blog_post_generator.py
    STYLE_CHARACTERISTICS = {
        "word_count_range": (500, 600),
        "ideal_word_count": 500,
        "max_word_count": 600,  # Acceptable range up to 600
        "sentences_per_paragraph": (1, 2),  # Max 2 sentences longer than 20 words each
        "max_colons_per_post": 2,
        "first_sentence_standalone": True,  # Must be its own paragraph
        "second_sentence_standalone": True,  # Must be its own paragraph with question/provocation
        "no_adverbs": True,  # Never use words ending in -ly
        "uses_data": True,
        "strong_opening": True,
        "clear_thesis": True,
        "practical_insights": True,
        "no_h2_headers": True,
        "no_section_headers": True,  # Continuous flowing prose only
        "conclusion_ties_to_hook": True,  # Must tie back to opening
        "problem_solving_narrative": True,  # Stable context → disruption → solution
        "smooth_transitions": True,
        "brevity_premium": True  # Reward shorter, tighter writing
    }
    
    def __init__(self, claude_client: ClaudeClient = None):
        """Initialize the evaluator with optional Claude client for AP English grading"""
        self.claude_client = claude_client
    
    def evaluate(self, blog_post: str, title: str = "") -> EvaluationScore:
        """
        Evaluate a blog post against all criteria
        
        Args:
            blog_post: The blog post content
            title: Optional title for context
            
        Returns:
            EvaluationScore with detailed feedback
        """
        # Basic style evaluation
        style_score, style_feedback = self._evaluate_style(blog_post)
        
        # Cliché detection
        cliche_score, cliche_feedback = self._evaluate_cliches(blog_post)
        
        # AP English teacher evaluation (grammar + argument strength)
        if self.claude_client:
            grammar_score, argument_score, ap_feedback = self._evaluate_with_ap_teacher(
                blog_post, title
            )
        else:
            # Fallback to basic evaluation
            grammar_score, argument_score = 80, 80
            ap_feedback = "AP English evaluation not available"
        
        # Calculate brevity score
        brevity_score = self._evaluate_brevity(blog_post)
        
        # Calculate overall score with brevity as a factor
        overall_score = (
            grammar_score * 0.20 +
            argument_score * 0.30 +
            style_score * 0.20 +
            cliche_score * 0.15 +
            brevity_score * 0.15
        )
        
        # Convert to letter grade
        overall_grade = self._score_to_grade(overall_score)
        
        # Determine if ready to ship (B+ or better)
        ready_to_ship = overall_score >= 87
        
        return EvaluationScore(
            grammatical_correctness=grammar_score,
            argument_strength=argument_score,
            style_match=style_score,
            cliche_absence=cliche_score,
            brevity_score=brevity_score,
            overall_grade=overall_grade,
            overall_score=overall_score,
            feedback={
                "style": style_feedback,
                "cliches": cliche_feedback,
                "brevity": f"Word count: {len(blog_post.split())} (target: 500)",
                "ap_evaluation": ap_feedback
            },
            ready_to_ship=ready_to_ship
        )
    
    def _evaluate_style(self, blog_post: str) -> Tuple[float, str]:
        """Evaluate how well the post matches Tom's writing style"""
        score = 100.0
        feedback = []
        
        # Word count with emphasis on brevity
        word_count = len(blog_post.split())
        ideal_words = self.STYLE_CHARACTERISTICS["ideal_word_count"]
        max_words = self.STYLE_CHARACTERISTICS["max_word_count"]
        
        if word_count > max_words:
            # Heavy penalty for exceeding 500 words
            penalty = (word_count - max_words) / max_words * 40
            score -= penalty
            feedback.append(f"Too long ({word_count} words, max: {max_words})")
        elif word_count > ideal_words:
            # Moderate penalty for exceeding ideal length
            penalty = (word_count - ideal_words) / ideal_words * 15
            score -= penalty
            feedback.append(f"Slightly long ({word_count} words, ideal: {ideal_words})")
        elif word_count < 400:
            # Penalty for being too short
            penalty = (400 - word_count) / 400 * 25
            score -= penalty
            feedback.append(f"Too short ({word_count} words, minimum: 400)")
        
        # Paragraph structure
        paragraphs = [p for p in blog_post.split('\n\n') if p.strip()]
        long_paragraphs = 0
        
        for para in paragraphs:
            sentences = re.split(r'[.!?]+', para)
            sentences = [s for s in sentences if s.strip()]
            if len(sentences) > 4:
                long_paragraphs += 1
        
        if long_paragraphs > 0:
            score -= long_paragraphs * 3
            feedback.append(f"{long_paragraphs} paragraphs too long (>4 sentences)")
        
        # Check for colons
        colon_count = blog_post.count(':')
        if colon_count > 2:
            score -= (colon_count - 2) * 5
            feedback.append(f"Too many colons ({colon_count}, max: 2)")
        
        # Check for H2 headers (##)
        if '##' in blog_post and not blog_post.startswith('##'):
            score -= 10
            feedback.append("Contains H2 headers (avoid in blog posts)")
        
        # Check for data/statistics
        has_numbers = bool(re.search(r'\d+[%x]|\$\d+|\d+\.\d+', blog_post))
        if not has_numbers:
            score -= 15
            feedback.append("No data or statistics found")
        
        # Strong opening (first sentence should be compelling)
        first_sentence = blog_post.split('.')[0] if '.' in blog_post else blog_post[:100]
        if len(first_sentence.split()) < 8:
            score -= 10
            feedback.append("Opening sentence too weak/short")
        
        return max(0, score), " | ".join(feedback) if feedback else "Style matches well"
    
    def _evaluate_brevity(self, blog_post: str) -> float:
        """Evaluate brevity and conciseness of the blog post"""
        word_count = len(blog_post.split())
        ideal_words = self.STYLE_CHARACTERISTICS["ideal_word_count"]
        max_words = self.STYLE_CHARACTERISTICS["max_word_count"]
        
        # Start with perfect score
        score = 100.0
        
        if word_count <= ideal_words:
            # Reward for being at or under ideal length
            if word_count >= 400:  # But not too short
                score = 100.0
            else:
                # Light penalty for being too short
                score = 85.0
        elif word_count <= max_words:
            # Moderate penalty for being longer than ideal but under max
            excess_ratio = (word_count - ideal_words) / (max_words - ideal_words)
            score = 100 - (excess_ratio * 25)  # 25 point penalty at max
        else:
            # Heavy penalty for exceeding max length
            excess_ratio = (word_count - max_words) / max_words
            score = 75 - (excess_ratio * 50)  # Up to 50 additional points off
            score = max(0, score)
        
        return score
    
    def _evaluate_cliches(self, blog_post: str) -> Tuple[float, str]:
        """Evaluate the absence of clichés"""
        blog_lower = blog_post.lower()
        found_cliches = []
        
        for cliche in self.CLICHES:
            if cliche in blog_lower:
                found_cliches.append(cliche)
        
        score = 100 - (len(found_cliches) * 10)
        score = max(0, score)
        
        if found_cliches:
            feedback = f"Found clichés: {', '.join(found_cliches[:5])}"
            if len(found_cliches) > 5:
                feedback += f" and {len(found_cliches) - 5} more"
        else:
            feedback = "No clichés detected"
        
        return score, feedback
    
    def _evaluate_with_ap_teacher(self, blog_post: str, title: str) -> Tuple[float, float, str]:
        """Use Claude to evaluate like an AP English teacher"""
        
        prompt = f"""You are an AP English teacher evaluating a technology blog post. 
Please evaluate this blog post on two criteria:

1. Grammatical Correctness (0-100): Grammar, punctuation, sentence structure, clarity
2. Argument Strength (0-100): Logic, evidence, persuasiveness, coherence, insights

Title: {title if title else "Untitled"}

Blog Post:
{blog_post[:2000]}...  # Truncate for evaluation if too long

Provide scores and brief feedback. Return ONLY valid JSON with no additional text:
{{
    "grammar_score": 85,
    "argument_score": 90,
    "overall_letter_grade": "B+",
    "strengths": "Clear thesis, strong evidence, compelling examples",
    "weaknesses": "Some repetition in middle paragraphs, could use stronger conclusion",
    "ready_to_publish": true
}}

Be strict but fair. A B+ or better means the post is ready to publish.
Focus on: clarity, conciseness, argument flow, evidence quality, and practical insights."""
        
        try:
            response = self.claude_client.generate(
                prompt,
                temperature=0.3,
                max_tokens=500
            )
            
            # Extract JSON from response
            content = response.content
            
            # Try to find JSON in the response
            import re
            json_match = re.search(r'\{[^{}]*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                evaluation = json.loads(json_str)
            else:
                # Try parsing the whole content
                evaluation = json.loads(content)
            
            grammar = evaluation.get("grammar_score", 80)
            argument = evaluation.get("argument_score", 80)
            feedback = f"Strengths: {evaluation.get('strengths', 'N/A')} | Weaknesses: {evaluation.get('weaknesses', 'N/A')}"
            
            return grammar, argument, feedback
            
        except Exception as e:
            # Fallback scores if evaluation fails
            return 75, 75, f"AP evaluation error: {str(e)}"
    
    def _score_to_grade(self, score: float) -> str:
        """Convert numerical score to letter grade"""
        if score >= 97: return "A+"
        elif score >= 93: return "A"
        elif score >= 90: return "A-"
        elif score >= 87: return "B+"
        elif score >= 83: return "B"
        elif score >= 80: return "B-"
        elif score >= 77: return "C+"
        elif score >= 73: return "C"
        elif score >= 70: return "C-"
        elif score >= 67: return "D+"
        elif score >= 63: return "D"
        elif score >= 60: return "D-"
        else: return "F"
    
    def compare_posts(self, posts: List[Dict[str, str]]) -> List[Dict]:
        """
        Compare multiple blog posts and rank them
        
        Args:
            posts: List of dicts with 'content' and optionally 'title' and 'model'
            
        Returns:
            Sorted list of posts with evaluation scores
        """
        evaluated_posts = []
        
        for post in posts:
            evaluation = self.evaluate(
                post['content'],
                post.get('title', '')
            )
            
            evaluated_posts.append({
                'model': post.get('model', 'unknown'),
                'title': post.get('title', 'Untitled'),
                'content': post['content'],
                'evaluation': evaluation,
                'overall_score': evaluation.overall_score,
                'grade': evaluation.overall_grade,
                'ready': evaluation.ready_to_ship
            })
        
        # Sort by overall score (highest first)
        evaluated_posts.sort(key=lambda x: x['overall_score'], reverse=True)
        
        return evaluated_posts
    
    def generate_improvement_suggestions(self, evaluation: EvaluationScore) -> List[str]:
        """Generate specific suggestions for improving the blog post"""
        suggestions = []
        
        if evaluation.grammatical_correctness < 85:
            suggestions.append("Review grammar and sentence structure for clarity")
        
        if evaluation.argument_strength < 85:
            suggestions.append("Strengthen arguments with more data and examples")
        
        if evaluation.style_match < 85:
            suggestions.append("Adjust writing style to be more concise and data-driven")
        
        if evaluation.cliche_absence < 90:
            suggestions.append("Remove business clichés and use more specific language")
        
        if not evaluation.ready_to_ship:
            suggestions.append(f"Current grade: {evaluation.overall_grade}. Target: B+ or better")
        
        return suggestions


def test_evaluator():
    """Test the evaluation system with a sample blog post"""
    
    sample_post = """Software pricing models are undergoing a fundamental shift as AI agents replace human operators.

The traditional SaaS model built on per-seat pricing faces an existential question when AI agents perform the work of multiple humans. Companies must rethink their pricing strategies to capture the value these systems create.

Three models are emerging. First, companies could triple seat prices to reflect the 3x productivity gains AI delivers. ServiceNow reported their engineers are 50% more productive with AI assistance, suggesting significant value creation. Second, usage-based pricing aligns costs with consumption, similar to how AWS charges for compute. This model provides transparency but introduces unpredictability that finance teams dislike. Third, outcome-based pricing ties fees directly to results, whether leads generated or tickets resolved.

The shift mirrors the transition from perpetual licenses to SaaS twenty years ago. Salesforce disrupted incumbents with the "No Software" message and monthly pricing. Today's startups have a similar opportunity to challenge established players with "No SaaS" positioning.

Early data suggests AI reduces customer support costs by 66% at companies like Klarna. Engineering productivity improves 50-75% according to Microsoft's internal metrics. These efficiency gains will reshape software economics fundamentally.

Winners in this transition will be companies that align pricing with customer value while maintaining predictable revenue streams. The next decade will determine which model becomes the industry standard."""
    
    # Initialize evaluator
    evaluator = BlogEvaluator()
    
    # Evaluate the post
    evaluation = evaluator.evaluate(sample_post, "AI Agents and Software Pricing")
    
    print("=" * 60)
    print("Blog Post Evaluation Results")
    print("=" * 60)
    print(f"Overall Grade: {evaluation.overall_grade}")
    print(f"Overall Score: {evaluation.overall_score:.1f}/100")
    print(f"Ready to Ship: {'✅ Yes' if evaluation.ready_to_ship else '❌ No'}")
    print("-" * 60)
    print(f"Grammar: {evaluation.grammatical_correctness:.1f}/100")
    print(f"Argument: {evaluation.argument_strength:.1f}/100")
    print(f"Style Match: {evaluation.style_match:.1f}/100")
    print(f"No Clichés: {evaluation.cliche_absence:.1f}/100")
    print("-" * 60)
    print("Feedback:")
    for category, feedback in evaluation.feedback.items():
        print(f"  {category}: {feedback}")
    
    # Generate improvement suggestions
    suggestions = evaluator.generate_improvement_suggestions(evaluation)
    if suggestions:
        print("-" * 60)
        print("Improvement Suggestions:")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"  {i}. {suggestion}")


if __name__ == "__main__":
    test_evaluator()