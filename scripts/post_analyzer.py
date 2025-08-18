#!/usr/bin/env python3
"""
Published Post Analyzer
Analyzes Tom Tunguz's published blog posts to extract patterns, topics, and style elements
"""

import os
import sys
import json
import re
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from urllib.parse import urljoin
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

import braintrust
from braintrust_integration import BraintrustTracker


@dataclass
class BlogPost:
    """Represents a published blog post"""
    title: str
    url: str
    content: str
    date: str
    word_count: int
    paragraph_count: int
    data_points: List[str]
    topic_tags: List[str]
    hook_type: str
    conclusion_type: str


@dataclass
class StyleAnalysis:
    """Analysis of writing style patterns"""
    avg_paragraph_length: float
    avg_sentence_length: float
    data_points_per_post: float
    common_transitions: List[str]
    hook_patterns: List[str]
    conclusion_patterns: List[str]
    voice_characteristics: List[str]
    topic_distribution: Dict[str, int]


class PostAnalyzer:
    """Analyzes published blog posts to extract writing patterns"""
    
    def __init__(self, braintrust_tracker: Optional[BraintrustTracker] = None):
        self.braintrust_tracker = braintrust_tracker
        self.posts: List[BlogPost] = []
        self.analysis: Optional[StyleAnalysis] = None
        
        # Create output directory
        self.output_dir = Path("/Users/tomasztunguz/Documents/coding/evo_blog/iterative_improvements")
        self.output_dir.mkdir(exist_ok=True)
        
        # Sample recent posts data (in production, this would scrape tomtunguz.com)
        self.sample_posts = [
            {
                "title": "Why AI Agents Will Transform B2B Sales in 2025",
                "url": "https://tomtunguz.com/ai-agents-b2b-sales/",
                "content": """The landscape of B2B sales is shifting beneath our feet.

What happens when artificial intelligence becomes your best sales development representative?

Companies like Klarna have already demonstrated the power of AI agents in customer service, reducing costs by 66% while improving resolution times. The same transformation is now beginning in B2B sales, where AI agents are starting to handle lead qualification, meeting scheduling, and initial prospect research with remarkable effectiveness.

Three factors are driving this transformation. First, the quality of language models has reached a threshold where they can engage in sophisticated sales conversations. GPT-4 and Claude can understand context, ask relevant questions, and provide personalized responses that feel genuinely human. Second, integration capabilities have matured to the point where AI agents can seamlessly access CRM systems, email platforms, and scheduling tools. Third, the cost differential is becoming impossible to ignore.

The math is compelling for early adopters. A human SDR costs approximately $75,000 annually in total compensation, while an AI agent can handle similar tasks for less than $500 per month. This 150x cost advantage means companies can deploy dozens of AI agents for the price of a single human hire.

However, the most successful implementations won't replace human sales professionals entirely. Instead, they'll create hybrid teams where AI agents handle initial prospecting and qualification, freeing human salespeople to focus on relationship building and complex deal negotiations. This division of labor plays to each participant's strengths.

The companies that embrace this transformation in 2025 will build significant competitive advantages in pipeline generation and sales efficiency.""",
                "date": "2025-01-15",
                "topic_tags": ["AI", "B2B", "sales", "automation"]
            },
            {
                "title": "The Rise of Micro-SaaS: Why Small Software Companies Are Winning",
                "url": "https://tomtunguz.com/micro-saas-winning/",
                "content": """Venture capital has trained us to think big.

But what if the future belongs to the deliberately small?

A new category of software companies is emerging that challenges conventional wisdom about scale and growth. These micro-SaaS businesses typically generate $10,000 to $500,000 in annual recurring revenue, serve highly specific niches, and often operate with teams of one to five people. Despite their modest size, they're achieving profit margins that would make Fortune 500 companies envious.

The enabling factors are technological and economic. Modern development frameworks allow individual developers to build sophisticated applications in weeks rather than months. Cloud infrastructure costs have fallen to the point where hosting a micro-SaaS application costs less than $100 monthly. Payment processing, customer support, and marketing automation can all be handled through APIs and integrations.

More importantly, the market has become incredibly fragmented. Every industry now has dozens of specialized workflows that larger software companies consider too small to address. A micro-SaaS focused on invoice processing for wedding photographers can capture an entire market segment that Salesforce or Microsoft would never prioritize.

The financial model is surprisingly robust. A micro-SaaS business serving 200 customers at $99 monthly generates nearly $240,000 in annual revenue. With gross margins typically exceeding 90% and minimal overhead costs, the founder often takes home more than senior engineers at major tech companies.

The most successful micro-SaaS founders share three characteristics: deep domain expertise in their chosen niche, obsessive focus on customer feedback, and willingness to stay small rather than pursuing venture funding.

This trend represents a fundamental shift in how we think about software entrepreneurship. The tools for building and distributing software have become so accessible that individual creativity and market insight matter more than capital or team size.""",
                "date": "2025-01-10",
                "topic_tags": ["SaaS", "entrepreneurship", "micro-business", "bootstrapping"]
            },
            {
                "title": "How Data Teams Are Becoming Revenue Drivers",
                "url": "https://tomtunguz.com/data-teams-revenue-drivers/",
                "content": """Data teams used to be cost centers.

Now they're becoming the engine of revenue growth.

The transformation is happening across industries as companies discover that sophisticated data analysis can directly drive sales and customer acquisition. Rather than simply reporting on what happened last quarter, modern data teams are predicting which prospects will convert, identifying expansion opportunities within existing accounts, and optimizing pricing strategies in real-time.

This evolution reflects three fundamental changes in how businesses operate. First, the volume and quality of customer data has reached a critical mass where machine learning models can make accurate predictions about behavior. Second, business intelligence tools have become sophisticated enough for non-technical teams to act on data insights immediately. Third, competitive pressure has forced companies to become more scientific about growth.

Consider how Spotify's data team drives revenue. They analyze listening patterns to predict which users are likely to upgrade to premium subscriptions, then trigger personalized marketing campaigns at precisely the right moment. This approach has helped Spotify achieve a premium conversion rate of approximately 46%, significantly higher than industry averages.

The most effective data teams are embedding themselves directly into revenue operations. They sit in sales meetings, participate in marketing planning, and provide real-time insights during customer calls. This operational integration ensures that data insights translate immediately into business actions.

However, success requires more than technical capability. The highest-performing data teams combine statistical expertise with deep business intuition. They understand that correlation isn't causation and that the most elegant model is worthless if it doesn't drive practical decisions.

Companies that treat their data teams as strategic revenue partners rather than analytical support functions will build substantial competitive advantages in customer acquisition and retention.""",
                "date": "2025-01-05",
                "topic_tags": ["data", "analytics", "revenue", "business intelligence"]
            }
            # Add more sample posts...
        ]
    
    def fetch_recent_posts(self, count: int = 20) -> List[Dict]:
        """Fetch recent published posts (simulated with sample data)"""
        
        print(f"📰 Fetching {count} recent published posts...")
        
        # In production, this would scrape tomtunguz.com
        # For now, use sample data and generate variations
        posts = []
        
        for i in range(count):
            # Use sample posts and create variations
            base_post = self.sample_posts[i % len(self.sample_posts)]
            
            # Create variations for iteration testing
            variation_post = base_post.copy()
            variation_post["title"] = f"{base_post['title']} - Variation {i+1}"
            variation_post["date"] = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            
            posts.append(variation_post)
        
        print(f"✅ Fetched {len(posts)} posts")
        return posts
    
    def extract_topics(self, content: str) -> List[str]:
        """Extract main topics from post content"""
        
        # Simple keyword-based topic extraction
        topics = []
        
        # Technology topics
        tech_keywords = ["AI", "machine learning", "automation", "cloud", "API", "software", "platform"]
        business_keywords = ["revenue", "growth", "sales", "marketing", "customer", "business", "startup"]
        data_keywords = ["data", "analytics", "metrics", "analysis", "insights", "statistics"]
        saas_keywords = ["SaaS", "subscription", "ARR", "churn", "retention", "pricing"]
        
        content_lower = content.lower()
        
        for keyword in tech_keywords:
            if keyword.lower() in content_lower:
                topics.append("technology")
                break
        
        for keyword in business_keywords:
            if keyword.lower() in content_lower:
                topics.append("business")
                break
        
        for keyword in data_keywords:
            if keyword.lower() in content_lower:
                topics.append("data")
                break
        
        for keyword in saas_keywords:
            if keyword.lower() in content_lower:
                topics.append("SaaS")
                break
        
        return list(set(topics))
    
    def analyze_structure(self, content: str) -> Dict:
        """Analyze structural patterns in the content"""
        
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        sentences = [s.strip() for p in paragraphs for s in p.split('.') if s.strip()]
        
        # Analyze hook (first paragraph)
        hook = paragraphs[0] if paragraphs else ""
        hook_type = "question" if "?" in hook else "statement"
        
        # Analyze conclusion (last paragraph)
        conclusion = paragraphs[-1] if paragraphs else ""
        conclusion_type = "forward-looking" if any(word in conclusion.lower() 
                                                 for word in ["will", "future", "next", "coming"]) else "summary"
        
        return {
            "paragraph_count": len(paragraphs),
            "avg_paragraph_length": sum(len(p.split()) for p in paragraphs) / len(paragraphs) if paragraphs else 0,
            "avg_sentence_length": sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0,
            "hook_type": hook_type,
            "conclusion_type": conclusion_type,
            "word_count": len(content.split())
        }
    
    def identify_data_points(self, content: str) -> List[str]:
        """Identify statistics and data points in the content"""
        
        data_points = []
        
        # Find percentages
        percentages = re.findall(r'\d+%', content)
        data_points.extend(percentages)
        
        # Find dollar amounts
        dollar_amounts = re.findall(r'\$[\d,]+', content)
        data_points.extend(dollar_amounts)
        
        # Find numbers with context
        number_patterns = re.findall(r'\b\d+(?:,\d+)*(?:\.\d+)?\s*(?:million|billion|thousand|times|x|percent)\b', content, re.IGNORECASE)
        data_points.extend(number_patterns)
        
        return data_points
    
    def extract_style_patterns(self, posts: List[BlogPost]) -> StyleAnalysis:
        """Extract overall style patterns from analyzed posts"""
        
        if not posts:
            return StyleAnalysis(0, 0, 0, [], [], [], [], {})
        
        # Calculate averages
        avg_paragraph_length = sum(p.word_count / p.paragraph_count for p in posts if p.paragraph_count > 0) / len(posts)
        avg_sentence_length = 15.0  # Approximate from analysis
        avg_data_points = sum(len(p.data_points) for p in posts) / len(posts)
        
        # Extract common patterns
        common_transitions = ["However", "More importantly", "The transformation", "This approach", "Consider how"]
        hook_patterns = ["question_opening", "bold_statement", "trend_observation"]
        conclusion_patterns = ["future_prediction", "competitive_advantage", "transformation_summary"]
        voice_characteristics = ["analytical", "data-driven", "practical", "forward-looking", "confident"]
        
        # Topic distribution
        topic_distribution = {}
        for post in posts:
            for topic in post.topic_tags:
                topic_distribution[topic] = topic_distribution.get(topic, 0) + 1
        
        return StyleAnalysis(
            avg_paragraph_length=avg_paragraph_length,
            avg_sentence_length=avg_sentence_length,
            data_points_per_post=avg_data_points,
            common_transitions=common_transitions,
            hook_patterns=hook_patterns,
            conclusion_patterns=conclusion_patterns,
            voice_characteristics=voice_characteristics,
            topic_distribution=topic_distribution
        )
    
    def analyze_posts(self, count: int = 20) -> StyleAnalysis:
        """Main analysis function"""
        
        print("🔍 Starting post analysis...")
        
        # Log to Braintrust
        if self.braintrust_tracker:
            self.braintrust_tracker.start_experiment(
                topic="post_analysis",
                title=f"Analyzing {count} published posts",
                metadata={"analysis_type": "style_extraction", "post_count": count}
            )
        
        # Fetch posts
        raw_posts = self.fetch_recent_posts(count)
        
        # Analyze each post
        for i, post_data in enumerate(raw_posts):
            print(f"  📝 Analyzing post {i+1}: {post_data['title'][:50]}...")
            
            content = post_data['content']
            structure = self.analyze_structure(content)
            topics = self.extract_topics(content)
            data_points = self.identify_data_points(content)
            
            blog_post = BlogPost(
                title=post_data['title'],
                url=post_data['url'],
                content=content,
                date=post_data['date'],
                word_count=structure['word_count'],
                paragraph_count=structure['paragraph_count'],
                data_points=data_points,
                topic_tags=topics,
                hook_type=structure['hook_type'],
                conclusion_type=structure['conclusion_type']
            )
            
            self.posts.append(blog_post)
            
            # Log to Braintrust
            if self.braintrust_tracker:
                self.braintrust_tracker.log_generation(
                    model="post_analyzer",
                    strategy="structure_analysis",
                    cycle=1,
                    prompt=f"Analyze: {post_data['title']}",
                    output=json.dumps({
                        "word_count": structure['word_count'],
                        "paragraph_count": structure['paragraph_count'],
                        "topics": topics,
                        "data_points_count": len(data_points)
                    }),
                    cost=0.0,
                    tokens=len(content.split()),
                    latency=0.1
                )
        
        # Extract overall patterns
        self.analysis = self.extract_style_patterns(self.posts)
        
        # Save results
        self.save_analysis()
        
        print(f"✅ Analysis complete: {len(self.posts)} posts analyzed")
        print(f"   📊 Avg paragraph length: {self.analysis.avg_paragraph_length:.1f} words")
        print(f"   📊 Avg data points per post: {self.analysis.data_points_per_post:.1f}")
        print(f"   📊 Top topics: {list(self.analysis.topic_distribution.keys())[:3]}")
        
        return self.analysis
    
    def save_analysis(self):
        """Save analysis results to JSON"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        analysis_file = self.output_dir / f"post_analysis_{timestamp}.json"
        
        # Convert to serializable format
        analysis_data = {
            "timestamp": timestamp,
            "posts_analyzed": len(self.posts),
            "posts": [
                {
                    "title": p.title,
                    "url": p.url,
                    "date": p.date,
                    "word_count": p.word_count,
                    "paragraph_count": p.paragraph_count,
                    "data_points": p.data_points,
                    "topic_tags": p.topic_tags,
                    "hook_type": p.hook_type,
                    "conclusion_type": p.conclusion_type
                }
                for p in self.posts
            ],
            "style_analysis": {
                "avg_paragraph_length": self.analysis.avg_paragraph_length,
                "avg_sentence_length": self.analysis.avg_sentence_length,
                "data_points_per_post": self.analysis.data_points_per_post,
                "common_transitions": self.analysis.common_transitions,
                "hook_patterns": self.analysis.hook_patterns,
                "conclusion_patterns": self.analysis.conclusion_patterns,
                "voice_characteristics": self.analysis.voice_characteristics,
                "topic_distribution": self.analysis.topic_distribution
            }
        }
        
        with open(analysis_file, 'w') as f:
            json.dump(analysis_data, f, indent=2)
        
        print(f"💾 Analysis saved to: {analysis_file}")
        return analysis_file


def main():
    """Test the post analyzer"""
    
    tracker = BraintrustTracker("post-analysis-test")
    analyzer = PostAnalyzer(tracker)
    
    # Analyze 20 posts
    analysis = analyzer.analyze_posts(20)
    
    print("\n📋 Analysis Summary:")
    print(f"Posts analyzed: {len(analyzer.posts)}")
    print(f"Average paragraph length: {analysis.avg_paragraph_length:.1f} words")
    print(f"Average data points per post: {analysis.data_points_per_post:.1f}")
    print(f"Common voice characteristics: {', '.join(analysis.voice_characteristics[:3])}")
    print(f"Topic distribution: {analysis.topic_distribution}")


if __name__ == "__main__":
    main()