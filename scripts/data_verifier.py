#!/usr/bin/env python3
"""
Data Verification and Enhancement for Blog Posts
Identifies claims that need verification and optionally searches for supporting data
"""

import re
import json
from typing import List, Dict, Tuple
from dataclasses import dataclass
import time


@dataclass
class DataPoint:
    """Represents a data point that needs verification"""
    text: str
    claim_type: str  # statistic, company_example, benchmark, quote
    search_query: str
    verified: bool = False
    source: str = ""
    replacement_text: str = ""


class DataVerifier:
    """Verifies and enhances data points in blog posts"""
    
    # Patterns that indicate potential unverified claims
    CLAIM_PATTERNS = [
        (r'\d+%', 'statistic'),  # Percentages
        (r'\$[\d,]+[BMK]?', 'financial'),  # Dollar amounts
        (r'\d+x\s+(?:more|less|faster|slower)', 'comparison'),  # Multipliers
        (r'(?:study|research|report|survey)\s+(?:shows|found|reveals)', 'study'),
        (r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:reported|achieved|reduced|increased)', 'company_claim'),
        (r'\[NEEDS DATA:([^\]]+)\]', 'needs_data'),  # Explicit data needs
    ]
    
    def __init__(self, search_function=None):
        """
        Initialize the verifier
        
        Args:
            search_function: Optional function to search for data online
        """
        self.search_function = search_function
    
    def extract_claims(self, text: str) -> List[DataPoint]:
        """
        Extract claims that might need verification
        
        Args:
            text: Blog post text
            
        Returns:
            List of data points that need verification
        """
        claims = []
        
        # Split into sentences for context
        sentences = re.split(r'[.!?]+', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Check for explicit data needs
            needs_match = re.search(r'\[NEEDS DATA:([^\]]+)\]', sentence)
            if needs_match:
                claims.append(DataPoint(
                    text=sentence,
                    claim_type='needs_data',
                    search_query=needs_match.group(1).strip()
                ))
                continue
            
            # Check for percentages with context
            percent_matches = re.findall(r'(\d+(?:\.\d+)?%)', sentence)
            for match in percent_matches:
                # Extract surrounding context for search query
                context = self._extract_context(sentence, match)
                claims.append(DataPoint(
                    text=sentence,
                    claim_type='statistic',
                    search_query=f"{context} {match} 2024 2025"
                ))
            
            # Check for company-specific claims
            company_pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:reported|achieved|reduced|increased|saw|experienced)\s+([^.]+)'
            company_matches = re.findall(company_pattern, sentence)
            for company, claim in company_matches:
                # Filter out common words that aren't companies
                if company not in ['The', 'This', 'These', 'That', 'Their', 'What', 'When']:
                    claims.append(DataPoint(
                        text=sentence,
                        claim_type='company_example',
                        search_query=f"{company} {claim} case study report"
                    ))
            
            # Check for benchmark/study references
            if re.search(r'(?:benchmark|study|research|report|survey)', sentence, re.I):
                # Extract the name if possible
                name_match = re.search(r'([A-Z][A-Z0-9\s\.]+)\s+(?:benchmark|study|report)', sentence)
                if name_match:
                    claims.append(DataPoint(
                        text=sentence,
                        claim_type='benchmark',
                        search_query=f"{name_match.group(1)} benchmark results 2024 2025"
                    ))
        
        return claims
    
    def _extract_context(self, sentence: str, target: str, window: int = 5) -> str:
        """Extract words around a target for context"""
        words = sentence.split()
        target_words = target.split()
        
        # Find target in sentence
        for i in range(len(words) - len(target_words) + 1):
            if words[i:i+len(target_words)] == target_words:
                # Get surrounding words
                start = max(0, i - window)
                end = min(len(words), i + len(target_words) + window)
                context_words = words[start:i] + words[i+len(target_words):end]
                return ' '.join(context_words)
        
        return sentence[:50]  # Fallback to first 50 chars
    
    def verify_claims(self, claims: List[DataPoint], auto_search: bool = False) -> List[DataPoint]:
        """
        Verify claims, optionally searching for data
        
        Args:
            claims: List of claims to verify
            auto_search: Whether to automatically search for data
            
        Returns:
            List of claims with verification status
        """
        verified_claims = []
        
        for claim in claims:
            if auto_search and self.search_function:
                print(f"  Searching for: {claim.search_query[:50]}...")
                
                try:
                    # Search for verification
                    search_results = self.search_function(claim.search_query)
                    
                    if search_results:
                        claim.verified = True
                        claim.source = search_results.get('source', 'Web search')
                        claim.replacement_text = search_results.get('verified_text', claim.text)
                    else:
                        claim.verified = False
                        claim.replacement_text = self._make_claim_less_specific(claim.text)
                    
                    # Rate limiting
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"    Search failed: {e}")
                    claim.verified = False
            
            verified_claims.append(claim)
        
        return verified_claims
    
    def _make_claim_less_specific(self, text: str) -> str:
        """Make a claim less specific when data can't be verified"""
        
        # Replace specific percentages with qualitative terms
        replacements = {
            r'\d{2,}%': 'a significant portion',
            r'\d+\.\d+%': 'a portion',
            r'[23]x': 'multiple times',
            r'\d+x': 'significantly',
            r'\$\d+[BMK]': 'substantial investment',
            r'reduced by \d+%': 'substantially reduced',
            r'increased by \d+%': 'significantly increased',
        }
        
        modified = text
        for pattern, replacement in replacements.items():
            modified = re.sub(pattern, replacement, modified, count=1)
        
        return modified
    
    def enhance_blog_post(self, blog_text: str, auto_search: bool = False) -> Tuple[str, List[DataPoint]]:
        """
        Enhance a blog post by verifying and updating claims
        
        Args:
            blog_text: Original blog post text
            auto_search: Whether to automatically search for data
            
        Returns:
            Tuple of (enhanced text, list of claims found)
        """
        # Extract claims
        claims = self.extract_claims(blog_text)
        
        if not claims:
            return blog_text, []
        
        print(f"\nFound {len(claims)} potential claims to verify:")
        for claim in claims[:5]:  # Show first 5
            print(f"  - {claim.claim_type}: {claim.text[:80]}...")
        
        # Verify claims if requested
        if auto_search:
            claims = self.verify_claims(claims, auto_search=True)
        
        # Replace unverified claims with less specific versions
        enhanced_text = blog_text
        for claim in claims:
            if claim.claim_type == 'needs_data':
                # Remove the [NEEDS DATA] markers
                enhanced_text = enhanced_text.replace(
                    f"[NEEDS DATA: {claim.search_query}]",
                    "[data pending verification]"
                )
            elif not claim.verified and claim.replacement_text != claim.text:
                enhanced_text = enhanced_text.replace(
                    claim.text,
                    claim.replacement_text
                )
        
        return enhanced_text, claims
    
    def generate_fact_check_report(self, claims: List[DataPoint]) -> str:
        """Generate a report of claims and their verification status"""
        
        report = "# Fact Check Report\n\n"
        
        verified = [c for c in claims if c.verified]
        unverified = [c for c in claims if not c.verified]
        needs_data = [c for c in claims if c.claim_type == 'needs_data']
        
        if verified:
            report += f"## Verified Claims ({len(verified)})\n"
            for claim in verified:
                report += f"- ✅ {claim.text[:100]}...\n"
                if claim.source:
                    report += f"  Source: {claim.source}\n"
        
        if unverified:
            report += f"\n## Unverified Claims ({len(unverified)})\n"
            for claim in unverified:
                report += f"- ❌ {claim.text[:100]}...\n"
                report += f"  Suggested search: {claim.search_query}\n"
        
        if needs_data:
            report += f"\n## Data Needed ({len(needs_data)})\n"
            for claim in needs_data:
                report += f"- 🔍 {claim.search_query}\n"
        
        return report


def test_verifier():
    """Test the data verifier with a sample blog post"""
    
    sample_text = """
    AI agents have transformed customer support, with companies reporting dramatic improvements.
    Klarna reduced their support costs by 66% using AI agents. [NEEDS DATA: Latest Klarna AI metrics]
    
    The SPIDER benchmark shows only 20% accuracy on complex queries. Microsoft reports their 
    engineers are 50% more productive with AI tools. 
    
    According to a recent Gartner study, 75% of enterprises will shift from piloting to 
    operationalizing AI by 2024. Snowflake achieved 3x faster query performance with their 
    new optimization engine.
    """
    
    verifier = DataVerifier()
    claims = verifier.extract_claims(sample_text)
    
    print("Extracted Claims:")
    print("=" * 60)
    for claim in claims:
        print(f"\nType: {claim.claim_type}")
        print(f"Text: {claim.text[:100]}...")
        print(f"Search: {claim.search_query}")
    
    # Test enhancement without search
    enhanced_text, _ = verifier.enhance_blog_post(sample_text, auto_search=False)
    
    print("\n" + "=" * 60)
    print("Enhanced Text (without verification):")
    print("=" * 60)
    print(enhanced_text)
    
    # Generate report
    report = verifier.generate_fact_check_report(claims)
    print("\n" + report)


if __name__ == "__main__":
    test_verifier()