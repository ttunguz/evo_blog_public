#!/usr/bin/env python3
"""
SCQA Planning Module
Uses Claude Opus 4 to structure blog topics into SCQA framework before generation
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))
from models import ClaudeClient


@dataclass
class SCQAStructure:
    """Represents the SCQA structure for a blog post"""
    situation: str          # Current stable state/context
    complication: str       # The disruption/problem/change
    question: str          # The key question this creates
    answer: str            # The insight/solution/response
    confidence_score: float # 0-100, how well-structured this SCQA is
    narrative_flow: str    # Brief description of the logical flow


class SCQAPlanner:
    """Plans blog post structure using SCQA framework with Claude Opus 4"""
    
    def __init__(self, claude_client: ClaudeClient = None):
        """Initialize the SCQA planner"""
        self.claude_client = claude_client
        self.template_path = Path(__file__).parent.parent / "templates" / "scqa_structure.json"
        self.templates = self._load_templates()
    
    def _load_templates(self) -> Dict:
        """Load SCQA templates from config"""
        try:
            if self.template_path.exists():
                with open(self.template_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load SCQA templates: {e}")
        
        # Default template if file doesn't exist
        return {
            "situation": {
                "description": "Current stable state/context",
                "prompts": ["What is the current status quo?", "What stable situation exists?"]
            },
            "complication": {
                "description": "The disruption/problem/change", 
                "prompts": ["What is changing?", "What problem has emerged?"]
            },
            "question": {
                "description": "The key question this creates",
                "prompts": ["What question does this raise?", "What needs to be answered?"]
            },
            "answer": {
                "description": "The insight/solution/response",
                "prompts": ["What evidence-based answer do we have?", "What should be done?"]
            }
        }
    
    def plan_structure(self, topic: str, title: str = "") -> SCQAStructure:
        """
        Analyze a topic and create SCQA structure
        
        Args:
            topic: The raw topic or prompt
            title: Optional title for context
            
        Returns:
            SCQAStructure with all components
        """
        if not self.claude_client:
            # Fallback to basic structure if no Claude available
            return self._create_fallback_structure(topic, title)
        
        # Build the SCQA analysis prompt
        analysis_prompt = self._build_analysis_prompt(topic, title)
        
        try:
            # Get SCQA analysis from Claude Opus 4
            response = self.claude_client.generate(
                analysis_prompt,
                temperature=0.3,  # Lower temperature for structured analysis
                max_tokens=1500
            )
            
            if response.error:
                print(f"SCQA planning error: {response.error}")
                return self._create_fallback_structure(topic, title)
            
            # Parse the response into SCQA structure
            scqa_structure = self._parse_scqa_response(response.content, topic)
            
            print(f"✅ SCQA structure planned (confidence: {scqa_structure.confidence_score:.1f}/100)")
            return scqa_structure
            
        except Exception as e:
            print(f"SCQA planning failed: {e}")
            return self._create_fallback_structure(topic, title)
    
    def _build_analysis_prompt(self, topic: str, title: str) -> str:
        """Build the prompt for SCQA analysis"""
        
        return f"""You are an expert content strategist helping structure a blog post using the SCQA framework (Situation, Complication, Question, Answer).

TOPIC: {topic}
{f"TITLE: {title}" if title else ""}

Your task is to analyze this topic and create a clear SCQA structure that will guide blog post generation.

SCQA FRAMEWORK:
- SITUATION: The current stable state, status quo, or established context
- COMPLICATION: The disruption, problem, change, or tension that has emerged
- QUESTION: The key question or challenge this creates (often implicit)
- ANSWER: The insight, solution, or response based on evidence and analysis

REQUIREMENTS:
1. Each component should be 1-3 sentences
2. Ensure logical flow: Situation → Complication → Question → Answer
3. Make the Question compelling and specific
4. Base the Answer on evidence, data, or logical reasoning
5. Focus on practical insights for startup founders and VCs
6. Avoid generic business clichés

RESPONSE FORMAT:
Please respond with EXACTLY this JSON structure:

{{
  "situation": "Current stable context or status quo...",
  "complication": "The disruption or problem that has emerged...", 
  "question": "The key question this creates...",
  "answer": "The evidence-based insight or solution...",
  "confidence_score": 85,
  "narrative_flow": "Brief description of how this flows logically"
}}

Analyze the topic and provide the SCQA structure:"""
    
    def _parse_scqa_response(self, response: str, topic: str) -> SCQAStructure:
        """Parse Claude's response into SCQAStructure"""
        try:
            # Extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in response")
            
            json_str = response[json_start:json_end]
            data = json.loads(json_str)
            
            return SCQAStructure(
                situation=data.get('situation', ''),
                complication=data.get('complication', ''),
                question=data.get('question', ''),
                answer=data.get('answer', ''),
                confidence_score=data.get('confidence_score', 75),
                narrative_flow=data.get('narrative_flow', 'Standard SCQA progression')
            )
            
        except Exception as e:
            print(f"Failed to parse SCQA response: {e}")
            return self._create_fallback_structure(topic, "")
    
    def _create_fallback_structure(self, topic: str, title: str) -> SCQAStructure:
        """Create a basic SCQA structure when Claude is unavailable"""
        return SCQAStructure(
            situation=f"Current state in the area of {topic}",
            complication=f"Emerging challenges or changes related to {topic}",
            question=f"What does this mean for the future of {topic}?",
            answer=f"Analysis and insights about {topic}",
            confidence_score=50,
            narrative_flow="Basic fallback structure"
        )
    
    def create_enhanced_prompt(self, scqa_structure: SCQAStructure, original_topic: str) -> str:
        """
        Create an enhanced prompt using the SCQA structure
        
        Args:
            scqa_structure: The planned SCQA structure
            original_topic: The original topic for fallback
            
        Returns:
            Enhanced prompt for blog generation
        """
        
        enhanced_prompt = f"""Write a blog post following this SCQA narrative structure:

SITUATION (Current Context): {scqa_structure.situation}

COMPLICATION (The Problem/Change): {scqa_structure.complication}

QUESTION (What This Raises): {scqa_structure.question}

ANSWER (Your Insight/Solution): {scqa_structure.answer}

NARRATIVE FLOW: {scqa_structure.narrative_flow}

CRITICAL INSTRUCTIONS:
- Structure your post to naturally flow through this SCQA progression
- Don't explicitly label the sections - weave them into natural prose
- The opening should establish the SITUATION
- Introduce the COMPLICATION as the central tension
- The QUESTION should be implicit (readers should feel it, not see it stated)
- The ANSWER should provide evidence-based insights and practical solutions

Original topic for reference: {original_topic}"""

        return enhanced_prompt
    
    def validate_scqa_structure(self, scqa_structure: SCQAStructure) -> Tuple[bool, List[str]]:
        """
        Validate that the SCQA structure is complete and logical
        
        Returns:
            (is_valid, list_of_issues)
        """
        issues = []
        
        # Check completeness
        if not scqa_structure.situation.strip():
            issues.append("Missing or empty Situation")
        
        if not scqa_structure.complication.strip():
            issues.append("Missing or empty Complication")
        
        if not scqa_structure.question.strip():
            issues.append("Missing or empty Question")
        
        if not scqa_structure.answer.strip():
            issues.append("Missing or empty Answer")
        
        # Check quality thresholds
        if scqa_structure.confidence_score < 60:
            issues.append(f"Low confidence score: {scqa_structure.confidence_score}")
        
        # Check for generic content
        generic_terms = ["emerging challenges", "current state", "analysis and insights"]
        for term in generic_terms:
            if term.lower() in scqa_structure.answer.lower():
                issues.append(f"Generic content detected: '{term}'")
        
        return len(issues) == 0, issues
    
    def get_scqa_summary(self, scqa_structure: SCQAStructure) -> str:
        """Get a readable summary of the SCQA structure"""
        return f"""
SCQA Structure Summary:
📍 Situation: {scqa_structure.situation[:100]}{"..." if len(scqa_structure.situation) > 100 else ""}
⚠️  Complication: {scqa_structure.complication[:100]}{"..." if len(scqa_structure.complication) > 100 else ""}
❓ Question: {scqa_structure.question[:100]}{"..." if len(scqa_structure.question) > 100 else ""}
✅ Answer: {scqa_structure.answer[:100]}{"..." if len(scqa_structure.answer) > 100 else ""}

Confidence: {scqa_structure.confidence_score}/100
Flow: {scqa_structure.narrative_flow}
"""


def test_scqa_planner():
    """Test the SCQA planner with a sample topic"""
    # This would normally use a real Claude client
    planner = SCQAPlanner()
    
    test_topic = "How AI agents are transforming customer support based on recent results showing 66% cost reduction"
    
    structure = planner.plan_structure(test_topic)
    print("Test SCQA Structure:")
    print(planner.get_scqa_summary(structure))
    
    is_valid, issues = planner.validate_scqa_structure(structure)
    print(f"\nValidation: {'✅ Valid' if is_valid else '❌ Issues found'}")
    if issues:
        for issue in issues:
            print(f"  - {issue}")


if __name__ == "__main__":
    test_scqa_planner()