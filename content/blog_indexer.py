#!/usr/bin/env python3
"""
Blog Post LanceDB Indexer

This script creates and maintains a LanceDB index of all blog posts in the h48/content/post folder
using local SentenceTransformer embeddings.

Usage:
    python blog_indexer.py --rebuild          # Rebuild entire index
    python blog_indexer.py --update           # Update with new/modified posts
    python blog_indexer.py --search "query"   # Search the index
"""

import argparse
import hashlib
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import lancedb
import pandas as pd
import pyarrow as pa
from sentence_transformers import SentenceTransformer


class ContentIndexer:
    def __init__(self, 
                 blog_dir: str = "/Users/tomasztunguz/Documents/coding/h48/content/post",
                 podcast_dir: str = "/Users/tomasztunguz/Documents/coding/whisper-cpp-official/podcast_transcripts",
                 db_path: str = "/Users/tomasztunguz/Documents/coding/lance/content_index.lancedb",
                 model_name: str = "all-mpnet-base-v2"):
        """
        Initialize the content indexer for both blog posts and podcast transcripts.
        
        Args:
            blog_dir: Directory containing blog post markdown files
            podcast_dir: Directory containing podcast transcript files
            db_path: Path to LanceDB database
            model_name: SentenceTransformer model name
        """
        self.blog_dir = Path(blog_dir)
        self.podcast_dir = Path(podcast_dir)
        self.db_path = db_path
        self.model_name = model_name
        
        # Initialize embedding model
        print(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        
        # Connect to LanceDB
        self.db = lancedb.connect(db_path)
        
        # Table name
        self.table_name = "content"
    
    def extract_blog_metadata(self, content: str, file_path: Path) -> Dict:
        """Extract metadata from blog markdown file."""
        # Extract front matter
        metadata = {
            'title': file_path.stem.replace('-', ' ').title(),
            'categories': [],
            'date': None,
            'draft': False,
            'content_type': 'blog'
        }
        
        # Parse YAML front matter
        if content.startswith('---'):
            try:
                front_matter_end = content.find('---', 3)
                if front_matter_end != -1:
                    front_matter = content[3:front_matter_end].strip()
                    for line in front_matter.split('\n'):
                        if ':' in line:
                            key, value = line.split(':', 1)
                            key = key.strip()
                            value = value.strip().strip('"\'')
                            
                            if key == 'title':
                                metadata['title'] = value
                            elif key == 'date':
                                metadata['date'] = value
                            elif key == 'categories':
                                # Parse categories list
                                if value.startswith('[') and value.endswith(']'):
                                    cats = value[1:-1].split(',')
                                    metadata['categories'] = [c.strip().strip('"\'') for c in cats]
                            elif key == 'draft':
                                metadata['draft'] = value.lower() == 'true'
                    
                    # Remove front matter from content
                    content = content[front_matter_end + 3:].strip()
            except Exception as e:
                print(f"Warning: Could not parse front matter in {file_path}: {e}")
        
        # Extract plain text content (remove markdown)
        plain_content = self.markdown_to_text(content)
        
        return {
            'title': metadata['title'],
            'categories': metadata['categories'],
            'date': metadata['date'],
            'draft': metadata['draft'],
            'content_type': metadata['content_type'],
            'content': plain_content,
            'word_count': len(plain_content.split()),
            'file_path': str(file_path),
            'filename': file_path.name
        }
    
    def markdown_to_text(self, markdown: str) -> str:
        """Convert markdown to plain text for embedding."""
        # Remove front matter if present
        if markdown.startswith('---'):
            end_idx = markdown.find('---', 3)
            if end_idx != -1:
                markdown = markdown[end_idx + 3:]
        
        # Remove markdown formatting
        text = re.sub(r'```.*?```', '', markdown, flags=re.DOTALL)  # Code blocks
        text = re.sub(r'`[^`]*`', '', text)  # Inline code
        text = re.sub(r'!\[.*?\]\(.*?\)', '', text)  # Images
        text = re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', text)  # Links
        text = re.sub(r'[#*_~`]', '', text)  # Markdown formatting
        text = re.sub(r'\n+', ' ', text)  # Multiple newlines
        text = re.sub(r'\s+', ' ', text)  # Multiple spaces
        
        return text.strip()
    
    def extract_podcast_metadata(self, content: str, file_path: Path) -> Dict:
        """Extract metadata from podcast transcript file."""
        # Extract title from filename (remove common patterns)
        title = file_path.stem
        title = title.replace('-', ' ').replace('_', ' ')
        
        # Clean up common podcast filename patterns
        title = re.sub(r'\d{4}-\d{2}-\d{2}', '', title)  # Remove dates
        title = re.sub(r'\s+', ' ', title).strip().title()
        
        # Try to extract show/guest info from filename
        show_name = "Unknown Podcast"
        guest_name = ""
        
        # Common patterns for podcast files
        if "20vc" in title.lower():
            show_name = "20VC"
        elif "invest-like-the-best" in title.lower() or "patrick" in title.lower():
            show_name = "Invest Like the Best"
        elif "all-in" in title.lower():
            show_name = "All-In Podcast"
        elif "acquired" in title.lower():
            show_name = "Acquired"
        
        # Basic content preprocessing for podcasts (they're usually plain text)
        clean_content = content.strip()
        
        # Try to extract date from content or filename
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', str(file_path))
        date = date_match.group(1) if date_match else None
        
        return {
            'title': title,
            'categories': ['podcast'],
            'date': date,
            'draft': False,
            'content_type': 'podcast',
            'show_name': show_name,
            'content': clean_content,
            'word_count': len(clean_content.split()),
            'file_path': str(file_path),
            'filename': file_path.name
        }
    
    def get_file_hash(self, file_path: Path) -> str:
        """Get MD5 hash of file for change detection."""
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    
    def get_existing_hashes(self) -> Dict[str, str]:
        """Get existing file hashes from the database."""
        try:
            table = self.db.open_table(self.table_name)
            df = table.to_pandas()
            return dict(zip(df['file_path'], df['file_hash']))
        except Exception:
            return {}
    
    def scan_blog_posts(self) -> List[Path]:
        """Scan for all markdown files in the blog directory."""
        return list(self.blog_dir.glob("*.md"))
    
    def scan_podcast_transcripts(self) -> List[Path]:
        """Scan for all transcript files in the podcast directory."""
        if not self.podcast_dir.exists():
            print(f"Warning: Podcast directory {self.podcast_dir} does not exist")
            return []
        return list(self.podcast_dir.glob("*.txt"))
    
    def scan_all_content(self) -> List[Tuple[Path, str]]:
        """Scan for all content files and return with their type."""
        content_files = []
        
        # Add blog posts
        for blog_file in self.scan_blog_posts():
            content_files.append((blog_file, 'blog'))
        
        # Add podcast transcripts
        for podcast_file in self.scan_podcast_transcripts():
            content_files.append((podcast_file, 'podcast'))
        
        return content_files
    
    def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings for a list of texts."""
        print(f"Creating embeddings for {len(texts)} texts...")
        embeddings = self.model.encode(texts, show_progress_bar=True)
        return embeddings.tolist()
    
    def rebuild_index(self):
        """Rebuild the entire index from scratch."""
        print("🔄 Rebuilding content index...")
        
        # Drop existing table if it exists
        try:
            self.db.drop_table(self.table_name)
        except Exception:
            pass
        
        content_files = self.scan_all_content()
        blog_count = sum(1 for _, content_type in content_files if content_type == 'blog')
        podcast_count = sum(1 for _, content_type in content_files if content_type == 'podcast')
        
        print(f"Found {blog_count} blog posts and {podcast_count} podcast transcripts")
        
        if not content_files:
            print("No content found!")
            return
        
        # Process all files
        records = []
        texts_for_embedding = []
        
        for file_path, content_type in content_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract metadata based on content type
                if content_type == 'blog':
                    metadata = self.extract_blog_metadata(content, file_path)
                else:  # podcast
                    metadata = self.extract_podcast_metadata(content, file_path)
                
                file_hash = self.get_file_hash(file_path)
                
                # Combine title and content for embedding
                embedding_text = f"{metadata['title']} {metadata['content']}"
                texts_for_embedding.append(embedding_text)
                
                record = {
                    'file_path': metadata['file_path'],
                    'filename': metadata['filename'],
                    'title': metadata['title'],
                    'content': metadata['content'],
                    'categories': metadata['categories'],
                    'date': metadata['date'],
                    'draft': metadata['draft'],
                    'content_type': metadata['content_type'],
                    'word_count': metadata['word_count'],
                    'file_hash': file_hash,
                    'indexed_at': datetime.now().isoformat()
                }
                
                # Add podcast-specific fields
                if content_type == 'podcast':
                    record['show_name'] = metadata.get('show_name', 'Unknown')
                else:
                    record['show_name'] = None
                
                records.append(record)
                
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
                continue
        
        if not records:
            print("No valid blog posts to index!")
            return
        
        # Create embeddings
        embeddings = self.create_embeddings(texts_for_embedding)
        
        # Add embeddings to records
        for record, embedding in zip(records, embeddings):
            record['embedding'] = embedding
        
        # Create DataFrame and LanceDB table
        df = pd.DataFrame(records)
        
        # Define schema
        schema = pa.schema([
            pa.field("file_path", pa.string()),
            pa.field("filename", pa.string()),
            pa.field("title", pa.string()),
            pa.field("content", pa.string()),
            pa.field("categories", pa.list_(pa.string())),
            pa.field("date", pa.string()),
            pa.field("draft", pa.bool_()),
            pa.field("content_type", pa.string()),
            pa.field("show_name", pa.string()),
            pa.field("word_count", pa.int64()),
            pa.field("file_hash", pa.string()),
            pa.field("indexed_at", pa.string()),
            pa.field("embedding", pa.list_(pa.float32(), list_size=self.embedding_dim))
        ])
        
        # Create table
        table = self.db.create_table(self.table_name, df, schema=schema)
        
        # Note: Vector index will be created automatically by LanceDB for vector searches
        
        print(f"✅ Successfully indexed {len(records)} blog posts")
    
    def update_index(self):
        """Update index with new or modified posts."""
        print("🔄 Updating blog post index...")
        
        blog_files = self.scan_blog_posts()
        existing_hashes = self.get_existing_hashes()
        
        new_or_modified = []
        for file_path in blog_files:
            current_hash = self.get_file_hash(file_path)
            stored_hash = existing_hashes.get(str(file_path))
            
            if stored_hash != current_hash:
                new_or_modified.append(file_path)
        
        if not new_or_modified:
            print("✅ No new or modified posts found")
            return
        
        print(f"Found {len(new_or_modified)} new/modified posts")
        
        # Process new/modified files
        records = []
        texts_for_embedding = []
        
        for file_path in new_or_modified:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                metadata = self.extract_metadata(content, file_path)
                file_hash = self.get_file_hash(file_path)
                
                embedding_text = f"{metadata['title']} {metadata['content']}"
                texts_for_embedding.append(embedding_text)
                
                record = {
                    'file_path': metadata['file_path'],
                    'filename': metadata['filename'],
                    'title': metadata['title'],
                    'content': metadata['content'],
                    'categories': metadata['categories'],
                    'date': metadata['date'],
                    'draft': metadata['draft'],
                    'word_count': metadata['word_count'],
                    'file_hash': file_hash,
                    'indexed_at': datetime.now().isoformat()
                }
                records.append(record)
                
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
                continue
        
        if not records:
            print("No valid posts to update!")
            return
        
        # Create embeddings
        embeddings = self.create_embeddings(texts_for_embedding)
        
        # Add embeddings to records
        for record, embedding in zip(records, embeddings):
            record['embedding'] = embedding
        
        # Update table
        table = self.db.open_table(self.table_name)
        
        # Remove old records for these files
        file_paths_to_update = [r['file_path'] for r in records]
        # Note: LanceDB doesn't have a direct delete by condition, so we'll append and handle duplicates
        
        df = pd.DataFrame(records)
        table.add(df)
        
        print(f"✅ Successfully updated {len(records)} blog posts")
    
    def search(self, query: str, limit: int = 5, content_type: str = None) -> List[Dict]:
        """Search the content index."""
        try:
            table = self.db.open_table(self.table_name)
            
            # Create query embedding
            query_embedding = self.model.encode([query])[0]
            
            # Search with optional content type filter
            search_query = table.search(query_embedding).limit(limit * 2)  # Get more results for filtering
            
            if content_type:
                # Apply content type filter
                search_query = search_query.where(f"content_type = '{content_type}'")
            
            results = search_query.to_pandas()
            
            # Convert to list of dicts
            search_results = []
            for _, row in results.iterrows():
                result = {
                    'title': row['title'],
                    'filename': row['filename'],
                    'categories': row['categories'],
                    'date': row['date'],
                    'content_type': row['content_type'],
                    'word_count': row['word_count'],
                    'score': row.get('_distance', 0),  # Similarity score
                    'content_preview': row['content'][:200] + "..." if len(row['content']) > 200 else row['content']
                }
                
                # Add podcast-specific fields
                if row['content_type'] == 'podcast':
                    result['show_name'] = row.get('show_name', 'Unknown')
                
                search_results.append(result)
                
                # Stop when we have enough results
                if len(search_results) >= limit:
                    break
            
            return search_results
            
        except Exception as e:
            print(f"Error searching index: {e}")
            return []


def main():
    parser = argparse.ArgumentParser(description="Content LanceDB Indexer (Blog Posts + Podcast Transcripts)")
    parser.add_argument("--rebuild", action="store_true", help="Rebuild entire index")
    parser.add_argument("--update", action="store_true", help="Update with new/modified content")
    parser.add_argument("--search", type=str, help="Search the index")
    parser.add_argument("--limit", type=int, default=5, help="Number of search results")
    parser.add_argument("--type", choices=["blog", "podcast"], help="Filter by content type")
    
    args = parser.parse_args()
    
    # Initialize indexer
    indexer = ContentIndexer()
    
    if args.rebuild:
        indexer.rebuild_index()
    elif args.update:
        indexer.update_index()
    elif args.search:
        results = indexer.search(args.search, args.limit, args.type)
        print(f"\n🔍 Search results for: '{args.search}'")
        if args.type:
            print(f"   Filtered by: {args.type}")
        print("=" * 50)
        for i, result in enumerate(results, 1):
            print(f"{i}. {result['title']}")
            print(f"   File: {result['filename']}")
            print(f"   Type: {result['content_type']}")
            if result['content_type'] == 'podcast':
                print(f"   Show: {result.get('show_name', 'Unknown')}")
            print(f"   Categories: {', '.join(result['categories'])}")
            print(f"   Words: {result['word_count']}")
            print(f"   Preview: {result['content_preview']}")
            print()
    else:
        print("Please specify --rebuild, --update, or --search")


if __name__ == "__main__":
    main()