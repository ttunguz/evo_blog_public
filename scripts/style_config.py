#!/usr/bin/env python3
"""
Style Configuration Loader
Loads writing style preferences from configuration files
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any

class StyleConfig:
    """Manages writing style configuration"""
    
    def __init__(self, config_path: str = None):
        """
        Initialize style configuration
        
        Args:
            config_path: Path to writing style config file
        """
        self.config_path = config_path or self._find_config_file()
        self.config = self._load_config()
    
    def _find_config_file(self) -> str:
        """Find the writing style configuration file"""
        # Try different locations
        possible_paths = [
            "config/writing_style.json",
            "../config/writing_style.json",
            os.path.join(Path(__file__).parent.parent, "config", "writing_style.json")
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        # Default fallback
        return "config/writing_style.json"
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"⚠️  Configuration file not found: {self.config_path}")
            return self._get_default_config()
        except json.JSONDecodeError as e:
            print(f"⚠️  Invalid JSON in config file: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration"""
        return {
            "author": {
                "name": "Professional Writer",
                "description": "Generic professional writing style"
            },
            "blog_info": {
                "url": "https://yourblog.com"
            },
            "voice_characteristics": [
                "Data-driven analysis",
                "Clear, direct communication", 
                "Business insights focus",
                "Practical actionable advice",
                "Industry expertise"
            ],
            "writing_style": {
                "tone": "professional",
                "target_word_count": [500, 750],
                "sentences_per_paragraph": [2, 4],
                "prefer_short_paragraphs": True,
                "data_points_per_post": [2, 4],
                "opening_hook_required": True,
                "conclusion_style": "forward-looking"
            }
        }
    
    @property
    def author_name(self) -> str:
        """Get author name"""
        return self.config.get("author", {}).get("name", "Professional Writer")
    
    @property
    def blog_url(self) -> str:
        """Get blog URL"""
        return self.config.get("blog_info", {}).get("url", "https://yourblog.com")
    
    @property
    def voice_characteristics(self) -> List[str]:
        """Get voice characteristics"""
        return self.config.get("voice_characteristics", [
            "Data-driven analysis",
            "Clear, direct communication"
        ])
    
    @property
    def target_word_count(self) -> List[int]:
        """Get target word count range"""
        return self.config.get("writing_style", {}).get("target_word_count", [500, 750])
    
    @property
    def sentences_per_paragraph(self) -> List[int]:
        """Get sentences per paragraph range"""
        return self.config.get("writing_style", {}).get("sentences_per_paragraph", [2, 4])
    
    @property
    def data_points_per_post(self) -> List[int]:
        """Get data points per post range"""
        return self.config.get("writing_style", {}).get("data_points_per_post", [2, 4])
    
    @property
    def writing_tone(self) -> str:
        """Get writing tone"""
        return self.config.get("writing_style", {}).get("tone", "professional")
    
    @property
    def conclusion_style(self) -> str:
        """Get conclusion style"""
        return self.config.get("writing_style", {}).get("conclusion_style", "forward-looking")
    
    def format_voice_characteristics(self) -> str:
        """Format voice characteristics for prompts"""
        return "\n".join([f"- {char}" for char in self.voice_characteristics])
    
    def get_system_prompt_variables(self) -> Dict[str, str]:
        """Get variables for system prompt formatting"""
        return {
            "author_name": self.author_name,
            "blog_url": self.blog_url,
            "voice_characteristics": self.format_voice_characteristics(),
            "target_word_count": f"{self.target_word_count[0]}-{self.target_word_count[1]}",
            "sentences_per_paragraph": f"{self.sentences_per_paragraph[0]}-{self.sentences_per_paragraph[1]}",
            "data_points_per_post": f"{self.data_points_per_post[0]}-{self.data_points_per_post[1]}",
            "writing_tone": self.writing_tone,
            "conclusion_style": self.conclusion_style
        }

# Global instance
style_config = StyleConfig()