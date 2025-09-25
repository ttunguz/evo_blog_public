#!/usr/bin/env python3
"""
Test script for GEPA integration
"""

import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

try:
    from gepa_adapter import GEPA_AVAILABLE, BlogPostDataInstance, BlogPostGEPAAdapter
    print(f"✅ GEPA adapter imported successfully")
    print(f"📦 GEPA available: {GEPA_AVAILABLE}")

    # Test data instance creation
    instance = BlogPostDataInstance(
        source_content="Test content",
        prompt="Test prompt",
        target_categories=["test"],
        expected_quality_score=90.0
    )
    print(f"✅ BlogPostDataInstance created successfully")

    print("\n🧬 GEPA Integration Test Passed!")

    if GEPA_AVAILABLE:
        print("🚀 Ready for full GEPA optimization")
    else:
        print("⚠️  GEPA library not installed - will fallback to standard generation")
        print("💡 Install with: pip install gepa")

except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Test failed: {e}")
    sys.exit(1)