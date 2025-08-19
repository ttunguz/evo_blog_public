#!/usr/bin/env python3
"""
Comparative Evaluator
Compares AI-generated posts with published posts to identify improvement areas
"""

import os
import sys
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import difflib
import google.generativeai as genai

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from post_analyzer import BlogPost
from braintrust_integration import BraintrustTracker
from autoevals import Battle, Factuality


@dataclass
class ComparisonScore:
    """Detailed comparison between AI and published post"""
    overall_similarity: float
    structural_match: float
    style_similarity: float
    content_depth: float
    data_usage_match: float
    hook_effectiveness: float
    conclusion_strength: float
    voice_authenticity: float
    improvement_areas: List[str]
    specific_feedback: Dict[str, str]
    llm_judge_score: Optional[float] = None
    llm_judge_feedback: Optional[str] = None


class ComparativeEvaluator:
    """Evaluates AI-generated posts against published posts"""
    
    def __init__(self, braintrust_tracker: Optional[BraintrustTracker] = None, use_llm_judge: bool = False):
        self.braintrust_tracker = braintrust_tracker
        self.use_llm_judge = use_llm_judge
        self.output_dir = Path(".//iterative_improvements")
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize autoevals
        self.battle_evaluator = Battle()
        self.factuality_evaluator = Factuality()
        
        # Initialize Gemini for LLM-as-judge if enabled
        if self.use_llm_judge:
            self._init_gemini()
    
    def _init_gemini(self):
        """Initialize Gemini 2.5 Pro for LLM-as-judge evaluation"""
        try:
            # Try to get API key from environment
            api_key = os.getenv('GOOGLE_API_KEY')
            if not api_key:
                # Try loading from config
                config_path = Path(__file__).parent.parent / "config" / "model_configs.json"
                if config_path.exists():
                    with open(config_path) as f:
                        config = json.load(f)
                        api_key = config.get('google_api_key')
            
            if api_key:
                genai.configure(api_key=api_key)
                self.gemini_model = genai.GenerativeModel('gemini-2.0-flash-exp')
                print("✅ Gemini 2.5 Pro initialized for LLM-as-judge evaluation")
            else:
                print("⚠️ Google API key not found. LLM-as-judge evaluation disabled.")
                self.use_llm_judge = False
        except Exception as e:
            print(f"⚠️ Failed to initialize Gemini: {e}. LLM-as-judge evaluation disabled.")
            self.use_llm_judge = False
    
    def llm_judge_evaluation(self, ai_content: str, published_content: str, topic: str = "") -> Tuple[float, str]:
        """Use Gemini 2.5 Pro as judge to compare AI vs published content"""
        
        if not self.use_llm_judge or not hasattr(self, 'gemini_model'):
            return 0.0, "LLM judge not available"
        
        prompt = f"""You are an expert blog post evaluator comparing AI-generated content with published reference content.

**Task**: Evaluate how well the AI-generated post matches the style, quality, and characteristics of the published reference post.

**Published Reference Post** (high-quality reference writing):
{published_content}

**AI-Generated Post** (to be evaluated):
{ai_content}

**Evaluation Criteria** (score each 0-100):

1. **Voice & Style Match** (25%): Does the AI capture the analytical, data-driven voice?
2. **Structure & Flow** (20%): Does it follow the reference paragraph structure and logical flow?
3. **Content Depth** (20%): Is the insight depth comparable to the reference?
4. **Data Integration** (15%): Does it use statistics and examples effectively?
5. **Hook Effectiveness** (10%): Is the opening as engaging as the reference style?
6. **Conclusion Impact** (10%): Does it end with forward-looking insights?

**Output Format**:
Score: [0-100 overall score]

**Detailed Analysis**:
- Voice Match: [score]/100 - [brief explanation]
- Structure: [score]/100 - [brief explanation] 
- Content Depth: [score]/100 - [brief explanation]
- Data Usage: [score]/100 - [brief explanation]
- Hook: [score]/100 - [brief explanation]
- Conclusion: [score]/100 - [brief explanation]

**Key Strengths**: [2-3 things the AI did well]
**Key Weaknesses**: [2-3 areas needing improvement]
**Overall Assessment**: [1-2 sentences on overall quality]

Be precise and constructive in your feedback. Focus on actionable insights."""
        
        try:
            response = self.gemini_model.generate_content(prompt)
            full_response = response.text
            
            # Extract score from response
            score_match = re.search(r'Score:\s*(\d+(?:\.\d+)?)', full_response)
            score = float(score_match.group(1)) if score_match else 0.0
            
            # Normalize to 0-1 scale
            normalized_score = score / 100.0
            
            return normalized_score, full_response
            
        except Exception as e:
            return 0.0, f"LLM judge evaluation failed: {str(e)}"
    
    def structural_comparison(self, ai_content: str, published_content: str) -> Dict[str, float]:
        """Compare structural elements between AI and published posts"""
        
        # Parse both posts
        ai_paragraphs = [p.strip() for p in ai_content.split('\n\n') if p.strip()]
        pub_paragraphs = [p.strip() for p in published_content.split('\n\n') if p.strip()]
        
        # Compare paragraph counts
        paragraph_count_score = 1.0 - abs(len(ai_paragraphs) - len(pub_paragraphs)) / max(len(ai_paragraphs), len(pub_paragraphs), 1)
        
        # Compare word counts
        ai_words = len(ai_content.split())
        pub_words = len(published_content.split())
        word_count_score = 1.0 - abs(ai_words - pub_words) / max(ai_words, pub_words, 1)
        
        # Compare paragraph length distribution
        ai_para_lengths = [len(p.split()) for p in ai_paragraphs]
        pub_para_lengths = [len(p.split()) for p in pub_paragraphs]
        
        if ai_para_lengths and pub_para_lengths:
            ai_avg = sum(ai_para_lengths) / len(ai_para_lengths)
            pub_avg = sum(pub_para_lengths) / len(pub_para_lengths)
            para_length_score = 1.0 - abs(ai_avg - pub_avg) / max(ai_avg, pub_avg, 1)
        else:
            para_length_score = 0.0
        
        # Hook comparison (first paragraph)
        ai_hook = ai_paragraphs[0] if ai_paragraphs else ""
        pub_hook = pub_paragraphs[0] if pub_paragraphs else ""
        
        hook_score = self._calculate_text_similarity(ai_hook, pub_hook)
        
        # Conclusion comparison (last paragraph)
        ai_conclusion = ai_paragraphs[-1] if ai_paragraphs else ""
        pub_conclusion = pub_paragraphs[-1] if pub_paragraphs else ""
        
        conclusion_score = self._calculate_text_similarity(ai_conclusion, pub_conclusion)
        
        return {
            "paragraph_count": paragraph_count_score,
            "word_count": word_count_score,
            "paragraph_length": para_length_score,
            "hook_quality": hook_score,
            "conclusion_quality": conclusion_score,
            "overall": (paragraph_count_score + word_count_score + para_length_score + hook_score + conclusion_score) / 5
        }
    
    def style_similarity_score(self, ai_content: str, published_content: str) -> Dict[str, float]:
        """Measure style similarity using various metrics"""
        
        # Voice pattern matching
        voice_patterns = [
            r'\b(?:However|More importantly|The transformation|This approach|Consider how)\b',
            r'\?\s*$',  # Questions
            r'\b\d+%\b',  # Percentages
            r'\$[\d,]+\b',  # Dollar amounts
            r'\b(?:will|future|next|coming)\b'  # Future-oriented language
        ]
        
        ai_pattern_matches = sum(len(re.findall(pattern, ai_content, re.IGNORECASE)) for pattern in voice_patterns)
        pub_pattern_matches = sum(len(re.findall(pattern, published_content, re.IGNORECASE)) for pattern in voice_patterns)
        
        if pub_pattern_matches > 0:
            pattern_score = min(ai_pattern_matches / pub_pattern_matches, 1.0)
        else:
            pattern_score = 1.0 if ai_pattern_matches == 0 else 0.0
        
        # Sentence length distribution
        ai_sentences = [s.strip() for s in re.split(r'[.!?]+', ai_content) if s.strip()]
        pub_sentences = [s.strip() for s in re.split(r'[.!?]+', published_content) if s.strip()]
        
        ai_avg_sentence = sum(len(s.split()) for s in ai_sentences) / len(ai_sentences) if ai_sentences else 0
        pub_avg_sentence = sum(len(s.split()) for s in pub_sentences) / len(pub_sentences) if pub_sentences else 0
        
        sentence_score = 1.0 - abs(ai_avg_sentence - pub_avg_sentence) / max(ai_avg_sentence, pub_avg_sentence, 1)
        
        # Tone analysis (simple keyword-based)
        analytical_words = ["data", "analysis", "evidence", "research", "study", "results"]
        confident_words = ["will", "must", "clearly", "obviously", "demonstrates"]
        practical_words = ["implement", "apply", "use", "adopt", "strategy"]
        
        ai_analytical = sum(ai_content.lower().count(word) for word in analytical_words)
        pub_analytical = sum(published_content.lower().count(word) for word in analytical_words)
        
        ai_confident = sum(ai_content.lower().count(word) for word in confident_words)
        pub_confident = sum(published_content.lower().count(word) for word in confident_words)
        
        ai_practical = sum(ai_content.lower().count(word) for word in practical_words)
        pub_practical = sum(published_content.lower().count(word) for word in practical_words)
        
        # Calculate tone similarity
        tone_score = 0.0
        total_comparisons = 0
        
        for ai_count, pub_count in [(ai_analytical, pub_analytical), (ai_confident, pub_confident), (ai_practical, pub_practical)]:
            if pub_count > 0:
                tone_score += min(ai_count / pub_count, 1.0)
            elif ai_count == 0:
                tone_score += 1.0
            total_comparisons += 1
        
        tone_score = tone_score / max(total_comparisons, 1)
        
        return {
            "voice_patterns": pattern_score,
            "sentence_structure": sentence_score,
            "tone_match": tone_score,
            "overall": (pattern_score + sentence_score + tone_score) / 3
        }
    
    def content_depth_analysis(self, ai_content: str, published_content: str, topic: str) -> Dict[str, float]:
        """Analyze content depth and insight quality"""
        
        # Use Battle evaluator for head-to-head comparison
        try:
            battle_result = self.battle_evaluator(
                output=ai_content,
                expected=published_content
            )
            battle_score = battle_result.score if hasattr(battle_result, 'score') else 0.5
        except:
            battle_score = 0.5  # Fallback
        
        # Insight density (unique concepts per paragraph)
        ai_paragraphs = [p.strip() for p in ai_content.split('\n\n') if p.strip()]
        pub_paragraphs = [p.strip() for p in published_content.split('\n\n') if p.strip()]
        
        # Simple insight detection based on keywords
        insight_keywords = [
            "trend", "shift", "transformation", "disruption", "opportunity",
            "challenge", "advantage", "strategy", "approach", "solution",
            "implication", "result", "consequence", "outcome", "impact"
        ]
        
        ai_insights = sum(p.lower().count(keyword) for p in ai_paragraphs for keyword in insight_keywords)
        pub_insights = sum(p.lower().count(keyword) for p in pub_paragraphs for keyword in insight_keywords)
        
        insight_density_score = min(ai_insights / max(pub_insights, 1), 1.0)
        
        # Specificity score (proper nouns, specific numbers)
        ai_specifics = len(re.findall(r'\b[A-Z][a-z]+\b|\b\d+(?:,\d+)*(?:\.\d+)?\b', ai_content))
        pub_specifics = len(re.findall(r'\b[A-Z][a-z]+\b|\b\d+(?:,\d+)*(?:\.\d+)?\b', published_content))
        
        specificity_score = min(ai_specifics / max(pub_specifics, 1), 1.0)
        
        # Novelty assessment (harder to measure programmatically, use Battle score as proxy)
        novelty_score = battle_score
        
        return {
            "battle_comparison": battle_score,
            "insight_density": insight_density_score,
            "specificity": specificity_score,
            "novelty": novelty_score,
            "overall": (battle_score + insight_density_score + specificity_score + novelty_score) / 4
        }
    
    def data_usage_comparison(self, ai_content: str, published_content: str) -> Dict[str, float]:
        """Compare data point usage between AI and published posts"""
        
        # Extract data points
        ai_data_points = self._extract_data_points(ai_content)
        pub_data_points = self._extract_data_points(published_content)
        
        # Count comparison
        count_score = 1.0 - abs(len(ai_data_points) - len(pub_data_points)) / max(len(ai_data_points), len(pub_data_points), 1)
        
        # Quality assessment (specific vs vague)
        ai_specific = sum(1 for dp in ai_data_points if re.search(r'\d', dp))
        pub_specific = sum(1 for dp in pub_data_points if re.search(r'\d', dp))
        
        quality_score = min(ai_specific / max(pub_specific, 1), 1.0) if pub_specific > 0 else (1.0 if ai_specific == 0 else 0.0)
        
        # Context integration (data points embedded in sentences vs standalone)
        ai_contextual = sum(1 for dp in ai_data_points if len(dp.split()) > 3)
        pub_contextual = sum(1 for dp in pub_data_points if len(dp.split()) > 3)
        
        context_score = min(ai_contextual / max(pub_contextual, 1), 1.0) if pub_contextual > 0 else (1.0 if ai_contextual == 0 else 0.0)
        
        return {
            "count_match": count_score,
            "quality_match": quality_score,
            "context_integration": context_score,
            "overall": (count_score + quality_score + context_score) / 3
        }
    
    def _extract_data_points(self, content: str) -> List[str]:
        """Extract data points from content"""
        
        data_points = []
        
        # Percentages
        percentages = re.findall(r'\d+%', content)
        data_points.extend(percentages)
        
        # Dollar amounts
        dollar_amounts = re.findall(r'\$[\d,]+(?:\.\d+)?(?:\s*(?:million|billion|thousand))?', content, re.IGNORECASE)
        data_points.extend(dollar_amounts)
        
        # Numbers with units
        numbers_with_units = re.findall(r'\b\d+(?:,\d+)*(?:\.\d+)?\s*(?:million|billion|thousand|times|x|percent|users|customers|companies)\b', content, re.IGNORECASE)
        data_points.extend(numbers_with_units)
        
        # Growth rates and multiples
        growth_rates = re.findall(r'\b\d+x\b|\bgrew\s+\d+%|\bincreased\s+\d+%|\bimproved\s+\d+%', content, re.IGNORECASE)
        data_points.extend(growth_rates)
        
        return data_points
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two text strings"""
        
        if not text1 or not text2:
            return 0.0
        
        # Use difflib for sequence matching
        similarity = difflib.SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
        return similarity
    
    def comprehensive_comparison(self, ai_content: str, published_post: BlogPost, 
                               topic: str, prompt_name: str = "unknown") -> ComparisonScore:
        """Perform comprehensive comparison between AI and published post"""
        
        print(f"🔍 Comparing AI vs Published: {published_post.title[:50]}...")
        
        # Structural analysis
        structural_scores = self.structural_comparison(ai_content, published_post.content)
        
        # Style analysis
        style_scores = self.style_similarity_score(ai_content, published_post.content)
        
        # Content depth analysis
        content_scores = self.content_depth_analysis(ai_content, published_post.content, topic)
        
        # Data usage analysis
        data_scores = self.data_usage_comparison(ai_content, published_post.content)
        
        # LLM-as-judge evaluation if enabled
        llm_judge_score = None
        llm_judge_feedback = None
        if self.use_llm_judge:
            print("🤖 Running LLM-as-judge evaluation with Gemini 2.5 Pro...")
            llm_judge_score, llm_judge_feedback = self.llm_judge_evaluation(
                ai_content, published_post.content, topic
            )
        
        # Calculate overall scores
        structural_match = structural_scores["overall"]
        style_similarity = style_scores["overall"]
        content_depth = content_scores["overall"]
        data_usage_match = data_scores["overall"]
        hook_effectiveness = structural_scores["hook_quality"]
        conclusion_strength = structural_scores["conclusion_quality"]
        voice_authenticity = style_scores["tone_match"]
        
        # Overall similarity (weighted average)
        if self.use_llm_judge and llm_judge_score is not None:
            # Use LLM judge score as primary evaluation with traditional metrics as secondary
            overall_similarity = (
                llm_judge_score * 0.60 +  # LLM judge gets 60% weight
                structural_match * 0.10 +
                style_similarity * 0.15 +
                content_depth * 0.10 +
                data_usage_match * 0.05
            )
        else:
            # Traditional weighted average
            overall_similarity = (
                structural_match * 0.25 +
                style_similarity * 0.30 +
                content_depth * 0.25 +
                data_usage_match * 0.20
            )
        
        # Identify improvement areas
        improvement_areas = []
        
        if structural_match < 0.7:
            improvement_areas.append("structure_flow")
        if style_similarity < 0.7:
            improvement_areas.append("voice_authenticity")
        if content_depth < 0.7:
            improvement_areas.append("insight_depth")
        if data_usage_match < 0.7:
            improvement_areas.append("data_integration")
        if hook_effectiveness < 0.6:
            improvement_areas.append("opening_hook")
        if conclusion_strength < 0.6:
            improvement_areas.append("conclusion_impact")
        
        # Specific feedback
        specific_feedback = {
            "structural": f"Paragraph structure: {structural_match:.1%}, Word count alignment: {structural_scores['word_count']:.1%}",
            "style": f"Voice patterns: {style_scores['voice_patterns']:.1%}, Tone match: {style_scores['tone_match']:.1%}",
            "content": f"Insight depth: {content_scores['insight_density']:.1%}, Specificity: {content_scores['specificity']:.1%}",
            "data": f"Data point count: {data_scores['count_match']:.1%}, Quality: {data_scores['quality_match']:.1%}"
        }
        
        score = ComparisonScore(
            overall_similarity=overall_similarity,
            structural_match=structural_match,
            style_similarity=style_similarity,
            content_depth=content_depth,
            data_usage_match=data_usage_match,
            hook_effectiveness=hook_effectiveness,
            conclusion_strength=conclusion_strength,
            voice_authenticity=voice_authenticity,
            improvement_areas=improvement_areas,
            specific_feedback=specific_feedback,
            llm_judge_score=llm_judge_score,
            llm_judge_feedback=llm_judge_feedback
        )
        
        # Log to Braintrust
        if self.braintrust_tracker:
            self.braintrust_tracker.log_evaluation(
                model="comparative_evaluator",
                strategy=prompt_name,
                cycle=1,
                content=ai_content,
                evaluation=self._convert_to_evaluation_score(score),
                input_prompt=f"Compare with: {published_post.title}"
            )
        
        print(f"   📊 Overall similarity: {overall_similarity:.1%}")
        print(f"   📊 Top improvement areas: {', '.join(improvement_areas[:3])}")
        
        return score
    
    def _convert_to_evaluation_score(self, comparison_score: ComparisonScore):
        """Convert ComparisonScore to EvaluationScore format for Braintrust"""
        
        # Create a mock evaluation score for Braintrust logging
        class MockEvaluation:
            def __init__(self, score: ComparisonScore):
                self.overall_score = score.overall_similarity * 100
                self.overall_grade = self._score_to_grade(score.overall_similarity)
                self.ready_to_ship = score.overall_similarity > 0.8
                self.scores = {
                    "structural_match": score.structural_match * 100,
                    "style_similarity": score.style_similarity * 100,
                    "content_depth": score.content_depth * 100,
                    "data_usage_match": score.data_usage_match * 100
                }
                self.feedback = {
                    "improvement_areas": score.improvement_areas,
                    "specific_feedback": score.specific_feedback
                }
            
            def _score_to_grade(self, score: float) -> str:
                if score >= 0.95: return "A+"
                elif score >= 0.90: return "A"
                elif score >= 0.85: return "A-"
                elif score >= 0.80: return "B+"
                elif score >= 0.75: return "B"
                elif score >= 0.70: return "B-"
                elif score >= 0.65: return "C+"
                else: return "C"
        
        return MockEvaluation(comparison_score)
    
    def batch_comparison(self, ai_posts: List[Tuple[str, str]], published_posts: List[BlogPost]) -> List[ComparisonScore]:
        """Compare multiple AI posts with published posts"""
        
        print(f"🔄 Running batch comparison: {len(ai_posts)} AI posts vs {len(published_posts)} published posts")
        
        comparisons = []
        
        for i, (ai_content, prompt_name) in enumerate(ai_posts):
            # Match with corresponding published post (or use round-robin)
            published_post = published_posts[i % len(published_posts)]
            
            # Extract topic from published post
            topic = published_post.topic_tags[0] if published_post.topic_tags else "general"
            
            comparison = self.comprehensive_comparison(ai_content, published_post, topic, prompt_name)
            comparisons.append(comparison)
        
        # Save batch results
        self._save_batch_results(comparisons)
        
        return comparisons
    
    def _save_batch_results(self, comparisons: List[ComparisonScore]) -> Path:
        """Save batch comparison results"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = self.output_dir / f"comparison_results_{timestamp}.json"
        
        results_data = {
            "timestamp": timestamp,
            "total_comparisons": len(comparisons),
            "average_similarity": sum(c.overall_similarity for c in comparisons) / len(comparisons),
            "comparisons": [
                {
                    "overall_similarity": c.overall_similarity,
                    "structural_match": c.structural_match,
                    "style_similarity": c.style_similarity,
                    "content_depth": c.content_depth,
                    "data_usage_match": c.data_usage_match,
                    "improvement_areas": c.improvement_areas,
                    "specific_feedback": c.specific_feedback
                }
                for c in comparisons
            ]
        }
        
        with open(results_file, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        print(f"💾 Comparison results saved to: {results_file}")
        return results_file


def main():
    """Test the comparative evaluator"""
    
    # Sample data for testing
    ai_content = """
The landscape of B2B sales is shifting beneath our feet.

What happens when artificial intelligence becomes your best sales development representative?

Companies like Klarna have demonstrated remarkable results with AI agents, achieving 66% cost reduction in customer service. This same transformation is now beginning in B2B sales environments.

The enabling factors are clear. Language models have reached sophisticated conversation capabilities. Integration tools now connect seamlessly with CRM and email platforms. The cost differential has become impossible to ignore.

A human SDR costs approximately $75,000 annually. An AI agent handles similar tasks for under $500 monthly. This represents a 150x cost advantage that early adopters are leveraging.

The most successful implementations create hybrid teams where AI handles prospecting while humans focus on relationship building and complex negotiations.
"""
    
    published_post = BlogPost(
        title="Why AI Agents Will Transform B2B Sales in 2025",
        url="https://tomtunguz.com/ai-agents-b2b-sales/",
        content="""The landscape of B2B sales is shifting beneath our feet.

What happens when artificial intelligence becomes your best sales development representative?

Companies like Klarna have already demonstrated the power of AI agents in customer service, reducing costs by 66% while improving resolution times. The same transformation is now beginning in B2B sales, where AI agents are starting to handle lead qualification, meeting scheduling, and initial prospect research with remarkable effectiveness.

Three factors are driving this transformation. First, the quality of language models has reached a threshold where they can engage in sophisticated sales conversations. GPT-4 and Claude can understand context, ask relevant questions, and provide personalized responses that feel genuinely human. Second, integration capabilities have matured to the point where AI agents can seamlessly access CRM systems, email platforms, and scheduling tools. Third, the cost differential is becoming impossible to ignore.

The math is compelling for early adopters. A human SDR costs approximately $75,000 annually in total compensation, while an AI agent can handle similar tasks for less than $500 per month. This 150x cost advantage means companies can deploy dozens of AI agents for the price of a single human hire.

However, the most successful implementations won't replace human sales professionals entirely. Instead, they'll create hybrid teams where AI agents handle initial prospecting and qualification, freeing human salespeople to focus on relationship building and complex deal negotiations. This division of labor plays to each participant's strengths.

The companies that embrace this transformation in 2025 will build significant competitive advantages in pipeline generation and sales efficiency.""",
        date="2025-01-15",
        word_count=350,
        paragraph_count=5,
        data_points=["66%", "$75,000", "$500", "150x"],
        topic_tags=["AI", "B2B", "sales"],
        hook_type="question",
        conclusion_type="forward-looking"
    )
    
    tracker = BraintrustTracker("comparative-evaluation-test")
    evaluator = ComparativeEvaluator(tracker)
    
    # Run comparison
    result = evaluator.comprehensive_comparison(ai_content, published_post, "AI", "test_prompt")
    
    print(f"\n📋 Comparison Results:")
    print(f"Overall Similarity: {result.overall_similarity:.1%}")
    print(f"Structural Match: {result.structural_match:.1%}")
    print(f"Style Similarity: {result.style_similarity:.1%}")
    print(f"Content Depth: {result.content_depth:.1%}")
    print(f"Data Usage Match: {result.data_usage_match:.1%}")
    print(f"Improvement Areas: {', '.join(result.improvement_areas)}")


if __name__ == "__main__":
    main()