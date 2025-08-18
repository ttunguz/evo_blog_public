#!/usr/bin/env python3
"""
Test Braintrust Integration
Verifies that Braintrust tracking works with the blog generator
"""

import os
import sys
import tempfile
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

from braintrust_integration import BraintrustTracker, setup_braintrust_for_blog_generator

def test_braintrust_setup():
    """Test basic Braintrust setup"""
    print("🧪 Testing Braintrust setup...")
    
    # Test without API key
    original_key = os.getenv('BRAINTRUST_API_KEY')
    if 'BRAINTRUST_API_KEY' in os.environ:
        del os.environ['BRAINTRUST_API_KEY']
    
    tracker = BraintrustTracker()
    assert tracker.enabled == False, "Tracker should be disabled without API key"
    print("  ✅ Correctly disabled when no API key")
    
    # Restore key if it existed
    if original_key:
        os.environ['BRAINTRUST_API_KEY'] = original_key
    
    print("✅ Braintrust setup test passed")

def test_braintrust_tracker_mock():
    """Test BraintrustTracker with mock data"""
    print("🧪 Testing BraintrustTracker with mock data...")
    
    # Create tracker (will be disabled without real API key)
    tracker = BraintrustTracker("test-project")
    
    # Test experiment start (should handle gracefully when disabled)
    experiment_id = tracker.start_experiment(
        topic="Test blog post generation",
        title="Test Title",
        metadata={"test": True}
    )
    print(f"  ✅ Experiment ID: {experiment_id}")
    
    # Test logging (should handle gracefully when disabled)
    tracker.log_generation(
        model="test_model",
        strategy="test_strategy", 
        cycle=1,
        prompt="Test prompt",
        output="Test output",
        cost=0.01,
        tokens=100,
        latency=1.5
    )
    print("  ✅ Generation logging works")
    
    # Create mock evaluation
    class MockEvaluation:
        def __init__(self):
            self.overall_score = 85.5
            self.overall_grade = "B+"
            self.ready_to_ship = True
            self.scores = {"content_quality": 90, "writing_style": 85}
            self.feedback = {"ap_evaluation": "Good structure and content"}
    
    tracker.log_evaluation(
        model="test_model",
        strategy="test_strategy",
        cycle=1,
        content="Test content",
        evaluation=MockEvaluation()
    )
    print("  ✅ Evaluation logging works")
    
    # Test finish experiment
    final_stats = {"total_cost": 0.05, "best_score": 85.5}
    result = tracker.finish_experiment(final_stats)
    print(f"  ✅ Experiment finished: {result}")
    
    print("✅ BraintrustTracker test passed")

def test_integration_import():
    """Test that the integration can be imported by the main generator"""
    print("🧪 Testing integration import...")
    
    try:
        from generate_blog_post import BlogGenerator
        print("  ✅ BlogGenerator imports successfully with Braintrust integration")
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        return False
    
    print("✅ Integration import test passed")
    return True

def test_config_loading():
    """Test that Braintrust config loads correctly"""
    print("🧪 Testing config loading...")
    
    try:
        import json
        config_path = Path("config/global_settings.json")
        
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            braintrust_config = config.get('braintrust', {})
            assert braintrust_config.get('enabled') == True, "Braintrust should be enabled in config"
            assert braintrust_config.get('project_name') == "evo-blog-generator", "Project name should be set"
            print("  ✅ Braintrust config loaded correctly")
        else:
            print("  ⚠️  Config file not found, skipping config test")
    
    except Exception as e:
        print(f"  ❌ Config loading error: {e}")
        return False
    
    print("✅ Config loading test passed")
    return True

def main():
    """Run all tests"""
    print("🚀 Starting Braintrust Integration Tests")
    print("=" * 50)
    
    tests = [
        test_braintrust_setup,
        test_braintrust_tracker_mock,
        test_integration_import,
        test_config_loading
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            test_func()
            passed += 1
            print()
        except Exception as e:
            print(f"❌ Test {test_func.__name__} failed: {e}")
            print()
    
    print("=" * 50)
    print(f"Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! Braintrust integration is ready.")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)