#!/usr/bin/env python3
"""
Main blog post generation script
Orchestrates the 3-cycle generation process
"""

import os
import json
import argparse
from datetime import datetime
from pathlib import Path
import hashlib
from typing import Dict, List, Any

# Model imports (to be implemented)
# from models import claude_client, gpt_client, gemini_client, local_client
# from evaluation import score_post, compare_posts
# from utils import extract_best_elements, create_improvement_prompt

class BlogGenerator:
    def __init__(self, config_path: Path = None):
        """Initialize the blog generator with configuration"""
        self.base_dir = Path.home() / "Documents" / "evo_blog"
        self.config = self.load_config(config_path)
        self.session_id = None
        self.session_dir = None
        
    def load_config(self, config_path: Path = None) -> Dict:
        """Load configuration from files"""
        if not config_path:
            config_path = self.base_dir / "config" / "global_settings.json"
        
        with open(config_path, 'r') as f:
            config = json.load(f)
            
        # Load evaluation weights
        weights_path = self.base_dir / "config" / "evaluation_weights.json"
        with open(weights_path, 'r') as f:
            config['evaluation'] = json.load(f)
            
        return config
    
    def create_session(self, topic: str, source_content: str) -> Path:
        """Create a new generation session"""
        # Create session ID and directory
        timestamp = datetime.now().strftime("%Y-%m-%d")
        topic_slug = topic.lower().replace(" ", "_")[:30]
        self.session_id = f"{timestamp}_{topic_slug}"
        self.session_dir = self.base_dir / "generations" / self.session_id
        
        # Create directory structure
        directories = [
            "",
            "cycle_1/prompts", "cycle_1/raw_outputs", "cycle_1/scores",
            "cycle_2/prompts", "cycle_2/refined_outputs", 
            "cycle_2/change_tracking", "cycle_2/scores",
            "cycle_3/final_candidates", "cycle_3/micro_edits", "cycle_3/scores",
            "final/alternatives"
        ]
        
        for dir_name in directories:
            (self.session_dir / dir_name).mkdir(parents=True, exist_ok=True)
        
        # Save metadata
        metadata = {
            "session_id": self.session_id,
            "topic": topic,
            "created_at": datetime.now().isoformat(),
            "source_type": "provided",
            "target_length": self.config['writing_style']['target_word_count'],
            "models_used": list(self.config['models'].keys()),
            "status": "initialized"
        }
        
        with open(self.session_dir / "metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Save source material
        with open(self.session_dir / "source_material.md", 'w') as f:
            f.write(f"# {topic}\n\n{source_content}")
        
        print(f"✓ Created session: {self.session_id}")
        return self.session_dir
    
    def generate_cycle_1(self, topic: str, source_content: str) -> Dict[str, Any]:
        """Generate initial variations using all models"""
        print("\n📝 CYCLE 1: Initial Generation")
        print("=" * 40)
        
        outputs = {}
        prompts = {}
        
        # Different angles for variation
        angles = [
            "technical deep-dive focusing on implementation details",
            "business implications and market analysis",
            "future predictions and emerging trends"
        ]
        
        for model_name, model_config in self.config['models'].items():
            print(f"\n🤖 Generating with {model_name}...")
            
            for i, angle in enumerate(angles[:2]):  # 2 variations per model
                version_name = f"{model_name}_v{i+1}"
                
                # Create prompt
                prompt = self.create_generation_prompt(
                    topic, source_content, angle, model_name
                )
                prompts[version_name] = prompt
                
                # TODO: Actually call the model
                # output = self.call_model(model_name, prompt, model_config)
                
                # For now, create placeholder
                output = f"# {topic}\n\n[{model_name} - {angle}]\n\n{source_content[:500]}..."
                
                outputs[version_name] = output
                
                # Save output
                output_path = self.session_dir / "cycle_1" / "raw_outputs" / f"{version_name}.md"
                with open(output_path, 'w') as f:
                    f.write(output)
                
                print(f"  ✓ Generated {version_name}")
        
        # Save prompts
        prompts_path = self.session_dir / "cycle_1" / "prompts" / "generation_prompts.json"
        with open(prompts_path, 'w') as f:
            json.dump(prompts, f, indent=2)
        
        return outputs
    
    def create_generation_prompt(self, topic: str, source: str, angle: str, model: str) -> str:
        """Create a generation prompt for a specific model and angle"""
        style = self.config['writing_style']
        
        prompt = f"""Write a blog post about: {topic}

Angle: {angle}

Requirements:
- Length: {style['target_word_count']} words (between {style['min_word_count']}-{style['max_word_count']})
- Paragraphs: {style['paragraphs']['sentences_per_paragraph'][0]}-{style['paragraphs']['sentences_per_paragraph'][1]} sentences each
- Include {self.config['content_preferences']['data_points_per_post'][0]}-{self.config['content_preferences']['data_points_per_post'][1]} data points or statistics
- Tone: {', '.join(style['tone'])}
- Use "{style['pronouns']}" pronouns
- Strong opening hook in first sentence
- Clear call-to-action in conclusion

Source material:
{source}

Write in the style of a thoughtful technology analyst who backs up insights with data.
"""
        return prompt
    
    def score_outputs(self, outputs: Dict[str, str], cycle: int) -> Dict[str, Any]:
        """Score all outputs from a cycle"""
        print(f"\n📊 Scoring {len(outputs)} outputs...")
        
        scores = {}
        for name, content in outputs.items():
            # TODO: Implement actual scoring
            # score = evaluate_post(content, self.config['evaluation'])
            
            # Placeholder scoring
            import random
            score = {
                "overall_score": random.uniform(70, 90),
                "breakdown": {
                    "style_match": random.uniform(70, 95),
                    "content_quality": random.uniform(70, 90),
                    "engagement": random.uniform(65, 85),
                    "technical": random.uniform(70, 90)
                },
                "word_count": len(content.split()),
                "strengths": ["Good structure", "Clear arguments"],
                "weaknesses": ["Could use more data", "Opening could be stronger"]
            }
            
            scores[name] = score
            print(f"  {name}: {score['overall_score']:.1f}")
        
        # Save scores
        scores_path = self.session_dir / f"cycle_{cycle}" / "scores" / "individual_scores.json"
        with open(scores_path, 'w') as f:
            json.dump(scores, f, indent=2)
        
        # Create ranking
        ranking = sorted(scores.items(), key=lambda x: x[1]['overall_score'], reverse=True)
        
        ranking_path = self.session_dir / f"cycle_{cycle}" / "scores" / "ranking.json"
        with open(ranking_path, 'w') as f:
            json.dump([{"name": k, "score": v['overall_score']} for k, v in ranking], f, indent=2)
        
        return scores
    
    def generate_cycle_2(self, cycle1_outputs: Dict, cycle1_scores: Dict) -> Dict[str, Any]:
        """Refine top performers from cycle 1"""
        print("\n✨ CYCLE 2: Refinement")
        print("=" * 40)
        
        # Get top 3 from cycle 1
        top_3 = sorted(cycle1_scores.items(), key=lambda x: x[1]['overall_score'], reverse=True)[:3]
        
        print(f"Refining top 3 performers:")
        for name, score in top_3:
            print(f"  - {name}: {score['overall_score']:.1f}")
        
        refined_outputs = {}
        
        for i, (original_name, original_score) in enumerate(top_3):
            refined_name = f"refined_v{i+1}_from_{original_name.split('_')[0]}"
            
            # Create improvement strategy
            improvement_prompt = self.create_improvement_prompt(
                cycle1_outputs[original_name],
                original_score,
                cycle1_outputs,
                cycle1_scores
            )
            
            # TODO: Call model for refinement
            # refined = self.call_model_for_refinement(improvement_prompt)
            
            # Placeholder
            refined = f"[REFINED VERSION]\n\n{cycle1_outputs[original_name]}\n\n[Improvements applied]"
            
            refined_outputs[refined_name] = refined
            
            # Save refined output
            output_path = self.session_dir / "cycle_2" / "refined_outputs" / f"{refined_name}.md"
            with open(output_path, 'w') as f:
                f.write(refined)
            
            print(f"  ✓ Created {refined_name}")
        
        return refined_outputs
    
    def create_improvement_prompt(self, original: str, score: Dict, 
                                 all_outputs: Dict, all_scores: Dict) -> str:
        """Create prompt for improving a blog post"""
        # Find best elements from other posts
        best_opening = max(all_scores.items(), 
                          key=lambda x: x[1]['breakdown'].get('engagement', 0))
        
        prompt = f"""Improve this blog post based on the feedback below:

ORIGINAL POST:
{original}

WEAKNESSES TO ADDRESS:
{', '.join(score.get('weaknesses', []))}

IMPROVEMENTS TO MAKE:
1. Strengthen the opening hook (reference best performer: {best_opening[0]})
2. Add more specific data points and statistics
3. Improve transitions between paragraphs
4. Ensure conclusion has clear call-to-action

Maintain the core argument and structure, but polish and enhance the writing.
"""
        return prompt
    
    def generate_cycle_3(self, cycle2_outputs: Dict, cycle2_scores: Dict) -> Dict[str, Any]:
        """Final polish on top candidates"""
        print("\n💎 CYCLE 3: Final Polish")
        print("=" * 40)
        
        # Get top 2 from cycle 2
        top_2 = sorted(cycle2_scores.items(), key=lambda x: x[1]['overall_score'], reverse=True)[:2]
        
        final_candidates = {}
        
        for i, (name, score) in enumerate(top_2):
            final_name = f"final_v{i+1}"
            
            # Polish focusing on micro-edits
            polish_prompt = f"""Final polish for this blog post:

{cycle2_outputs[name]}

Polish requirements:
1. Perfect the opening sentence (max 25 words, compelling hook)
2. Ensure each paragraph transition is smooth
3. Verify all data points are properly cited
4. Strengthen the conclusion with actionable takeaway
5. Check for any redundancy or verbose sections

Make minimal changes - this is about perfection, not rewriting.
"""
            
            # TODO: Call model for final polish
            # final = self.call_model_for_polish(polish_prompt)
            
            # Placeholder
            final = f"[FINAL POLISHED VERSION]\n\n{cycle2_outputs[name]}"
            
            final_candidates[final_name] = final
            
            # Save final candidate
            output_path = self.session_dir / "cycle_3" / "final_candidates" / f"{final_name}.md"
            with open(output_path, 'w') as f:
                f.write(final)
            
            print(f"  ✓ Polished {final_name}")
        
        # Generate third candidate by combining best elements
        combined = self.create_hybrid_candidate(cycle2_outputs, cycle2_scores)
        final_candidates["final_v3"] = combined
        
        output_path = self.session_dir / "cycle_3" / "final_candidates" / "final_v3.md"
        with open(output_path, 'w') as f:
            f.write(combined)
        
        return final_candidates
    
    def create_hybrid_candidate(self, outputs: Dict, scores: Dict) -> str:
        """Create a hybrid candidate combining best elements"""
        # TODO: Implement intelligent combination
        return "[HYBRID VERSION]\n\nCombining best elements from all candidates..."
    
    def select_final(self, final_candidates: Dict, final_scores: Dict) -> str:
        """Select the best final candidate"""
        print("\n🏆 Final Selection")
        print("=" * 40)
        
        # Get winner
        winner = max(final_scores.items(), key=lambda x: x[1]['overall_score'])
        winner_name, winner_score = winner
        
        print(f"Selected: {winner_name} (Score: {winner_score['overall_score']:.1f})")
        
        # Save final selection
        final_content = final_candidates[winner_name]
        
        final_path = self.session_dir / "final" / "selected_post.md"
        with open(final_path, 'w') as f:
            f.write(final_content)
        
        # Save alternatives
        for name, content in final_candidates.items():
            if name != winner_name:
                alt_path = self.session_dir / "final" / "alternatives" / f"{name}.md"
                with open(alt_path, 'w') as f:
                    f.write(content)
        
        # Create selection rationale
        rationale = f"""# Final Selection: {winner_name}

## Scores
- Overall: {winner_score['overall_score']:.1f}
- Style Match: {winner_score['breakdown']['style_match']:.1f}
- Content Quality: {winner_score['breakdown']['content_quality']:.1f}
- Engagement: {winner_score['breakdown']['engagement']:.1f}
- Technical: {winner_score['breakdown']['technical']:.1f}

## Why This Version Won
{', '.join(winner_score.get('strengths', []))}

## Runner-ups
"""
        for name, score in final_scores.items():
            if name != winner_name:
                rationale += f"- {name}: {score['overall_score']:.1f}\n"
        
        rationale_path = self.session_dir / "final" / "selection_rationale.md"
        with open(rationale_path, 'w') as f:
            f.write(rationale)
        
        # Update metadata
        metadata_path = self.session_dir / "metadata.json"
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        metadata['final_selection'] = f"final/{winner_name}.md"
        metadata['final_score'] = winner_score['overall_score']
        metadata['completed_at'] = datetime.now().isoformat()
        metadata['status'] = 'completed'
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return final_content
    
    def run(self, topic: str, source_content: str) -> str:
        """Run the complete generation pipeline"""
        print(f"\n🚀 Generating blog post: {topic}")
        print("=" * 50)
        
        # Create session
        self.create_session(topic, source_content)
        
        # Cycle 1: Initial generation
        cycle1_outputs = self.generate_cycle_1(topic, source_content)
        cycle1_scores = self.score_outputs(cycle1_outputs, 1)
        
        # Cycle 2: Refinement
        cycle2_outputs = self.generate_cycle_2(cycle1_outputs, cycle1_scores)
        cycle2_scores = self.score_outputs(cycle2_outputs, 2)
        
        # Cycle 3: Polish
        final_candidates = self.generate_cycle_3(cycle2_outputs, cycle2_scores)
        final_scores = self.score_outputs(final_candidates, 3)
        
        # Select final
        final_post = self.select_final(final_candidates, final_scores)
        
        print("\n✅ Generation complete!")
        print(f"📁 Session: {self.session_dir}")
        print(f"📝 Final post: {self.session_dir}/final/selected_post.md")
        
        return final_post


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Generate a blog post using evolutionary approach")
    parser.add_argument("--topic", required=True, help="Blog post topic")
    parser.add_argument("--source", help="Source material file", default=None)
    parser.add_argument("--template", help="Template to use", default=None)
    
    args = parser.parse_args()
    
    # Load source content
    if args.source and Path(args.source).exists():
        with open(args.source, 'r') as f:
            source_content = f.read()
    else:
        source_content = f"Generate a comprehensive blog post about {args.topic}"
    
    # Run generator
    generator = BlogGenerator()
    final_post = generator.run(args.topic, source_content)
    
    print("\n📄 Preview of final post:")
    print("-" * 40)
    print(final_post[:500] + "...")


if __name__ == "__main__":
    main()