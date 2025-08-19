#!/usr/bin/env python3
"""
Content Retrieval Module for Enhanced Blog Generation

Integrates with the unified LanceDB content index to provide rich context
from both blog posts and podcast transcripts.
"""

import sys
from pathlib import Path
from typing import List, Dict, Optional

# Add the h48 content directory to path for imports
sys.path.insert(0, "./content")

try:
    # First try direct import
    from blog_indexer import ContentIndexer
except ImportError:
    try:
        # Try importing with full path
        import importlib.util
        spec = importlib.util.spec_from_file_location("blog_indexer", "./content/blog_indexer.py")
        blog_indexer_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(blog_indexer_module)
        ContentIndexer = blog_indexer_module.ContentIndexer
    except Exception as e:
        print(f"Warning: ContentIndexer not available ({e}). Blog generation will proceed without enhanced context.")
        ContentIndexer = None


class ContentRetriever:
    """Retrieves relevant content from the unified LanceDB index"""
    
    def __init__(self):
        """Initialize the content retriever"""
        self.indexer = None
        if ContentIndexer:
            try:
                self.indexer = ContentIndexer()
                print("✅ Content retriever initialized with LanceDB index")
            except Exception as e:
                print(f"⚠️  Warning: Could not initialize content indexer: {e}")
        else:
            print("⚠️  Warning: ContentIndexer not available")
    
    def get_context_for_topic(self, topic: str, max_items: int = 6) -> Dict[str, List[Dict]]:
        """
        Retrieve relevant context for a blog topic.
        
        Args:
            topic: The blog topic/prompt
            max_items: Maximum items to retrieve (split between blogs and podcasts)
            
        Returns:
            Dictionary with 'blogs' and 'podcasts' lists containing relevant content
        """
        if not self.indexer:
            return {'blogs': [], 'podcasts': []}
        
        try:
            # Split search between blogs and podcasts for balanced context
            blog_limit = max_items // 2
            podcast_limit = max_items - blog_limit
            
            # Search for relevant blog posts
            blog_results = self.indexer.search(
                query=topic, 
                limit=blog_limit, 
                content_type='blog'
            )
            
            # Search for relevant podcast transcripts
            podcast_results = self.indexer.search(
                query=topic, 
                limit=podcast_limit, 
                content_type='podcast'
            )
            
            return {
                'blogs': self._format_blog_results(blog_results),
                'podcasts': self._format_podcast_results(podcast_results)
            }
            
        except Exception as e:
            print(f"Error retrieving content: {e}")
            return {'blogs': [], 'podcasts': []}
    
    def _format_blog_results(self, results: List[Dict]) -> List[Dict]:
        """Format blog search results for context"""
        formatted = []
        for result in results:
            formatted.append({
                'title': result['title'],
                'type': 'blog',
                'categories': result.get('categories', []),
                'date': result.get('date'),
                'content': result['content_preview'],
                'word_count': result.get('word_count', 0),
                'filename': result.get('filename', ''),
                'relevance_score': 1.0 - result.get('score', 0)  # Convert distance to relevance
            })
        return formatted
    
    def _format_podcast_results(self, results: List[Dict]) -> List[Dict]:
        """Format podcast search results for context"""
        formatted = []
        for result in results:
            formatted.append({
                'title': result['title'],
                'type': 'podcast',
                'show_name': result.get('show_name', 'Unknown Podcast'),
                'categories': result.get('categories', []),
                'date': result.get('date'),
                'content': result['content_preview'],
                'word_count': result.get('word_count', 0),
                'filename': result.get('filename', ''),
                'relevance_score': 1.0 - result.get('score', 0)  # Convert distance to relevance
            })
        return formatted
    
    def format_context_for_prompt(self, context: Dict[str, List[Dict]]) -> str:
        """
        Format retrieved context into a prompt-ready string.
        
        Args:
            context: Dictionary with 'blogs' and 'podcasts' lists
            
        Returns:
            Formatted context string for inclusion in prompts
        """
        if not context['blogs'] and not context['podcasts']:
            return ""
        
        context_str = "## RELEVANT CONTEXT\n\n"
        
        # Add blog context
        if context['blogs']:
            context_str += "### Your Previous Writing:\n"
            for i, blog in enumerate(context['blogs'], 1):
                context_str += f"{i}. **{blog['title']}** ({', '.join(blog['categories'])})\n"
                context_str += f"   {blog['content']}\n\n"
        
        # Add podcast context
        if context['podcasts']:
            context_str += "### Expert Conversations:\n"
            for i, podcast in enumerate(context['podcasts'], 1):
                show_info = f"from {podcast['show_name']}" if podcast['show_name'] != 'Unknown Podcast' else ""
                context_str += f"{i}. **{podcast['title']}** {show_info}\n"
                context_str += f"   {podcast['content']}\n\n"
        
        context_str += "---\n\n"
        return context_str
    
    def get_enhanced_prompt(self, original_prompt: str, topic: str) -> str:
        """
        Enhance a blog generation prompt with relevant context.
        
        Args:
            original_prompt: The original blog generation prompt
            topic: The blog topic for context retrieval
            
        Returns:
            Enhanced prompt with context
        """
        context = self.get_context_for_topic(topic)
        context_str = self.format_context_for_prompt(context)
        
        if not context_str:
            return original_prompt
        
        # Insert context before the main prompt
        enhanced_prompt = f"""{context_str}

Using the relevant context above as background and inspiration (but not copying directly), please {original_prompt.lower()}"""
        
        return enhanced_prompt
    
    def get_context_summary(self, context: Dict[str, List[Dict]]) -> str:
        """Get a summary of retrieved context for logging"""
        blog_count = len(context['blogs'])
        podcast_count = len(context['podcasts'])
        
        if blog_count == 0 and podcast_count == 0:
            return "No relevant context found"
        
        summary_parts = []
        if blog_count > 0:
            summary_parts.append(f"{blog_count} blog post{'s' if blog_count != 1 else ''}")
        if podcast_count > 0:
            summary_parts.append(f"{podcast_count} podcast transcript{'s' if podcast_count != 1 else ''}")
        
        return f"Retrieved {' and '.join(summary_parts)} for context"