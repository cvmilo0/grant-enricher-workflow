#!/usr/bin/env python3
"""
Simple test to verify the LangGraph structure works correctly.
"""

import os
import sys
from pathlib import Path

# Add the current directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all imports work correctly."""
    print("🧪 Testing imports...")
    
    try:
        from langgraph_analyzer import SubsidyAnalyzerGraph
        print("✅ SubsidyAnalyzerGraph imported successfully")
        
        from langgraph_analyzer.llms import LanguageModel
        print("✅ LanguageModel imported successfully")
        
        from langgraph_analyzer.schemas import SubsidyState, SubsidyAnalysisResult
        print("✅ Schemas imported successfully")
        
        from langgraph_analyzer.graph import compiled_graph
        print("✅ compiled_graph imported successfully")
        
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False


def test_compiled_graph():
    """Test that the compiled graph can be created."""
    print("\n🔧 Testing compiled graph creation...")
    
    try:
        from langgraph_analyzer.graph import compiled_graph
        print(f"✅ Compiled graph created: {type(compiled_graph)}")
        print(f"   Graph nodes: {list(compiled_graph.nodes.keys()) if hasattr(compiled_graph, 'nodes') else 'Unknown'}")
        return True
    except Exception as e:
        print(f"❌ Compiled graph error: {e}")
        return False


def test_llm_creation():
    """Test that LLM instances can be created."""
    print("\n🤖 Testing LLM creation...")
    
    # Set a dummy API key for testing (won't actually call the API)
    os.environ.setdefault("OPENAI_API_KEY", "test-key")
    
    try:
        from langgraph_analyzer.llms import LanguageModel
        
        # Test with different models
        models_to_test = ["gpt-4o-mini"]  # Only test OpenAI since it's most likely to be available
        
        for model in models_to_test:
            try:
                llm = LanguageModel(model)
                print(f"✅ {model}: Created successfully")
            except ValueError as e:
                if "not found" in str(e):
                    print(f"⚠️  {model}: Not configured (missing API key)")
                else:
                    print(f"❌ {model}: {e}")
            except Exception as e:
                print(f"❌ {model}: {e}")
        
        return True
    except Exception as e:
        print(f"❌ LLM creation error: {e}")
        return False


def test_graph_instantiation():
    """Test that the SubsidyAnalyzerGraph can be instantiated."""
    print("\n🏗️  Testing graph instantiation...")
    
    # Set a dummy API key for testing
    os.environ.setdefault("OPENAI_API_KEY", "test-key")
    
    try:
        from langgraph_analyzer import SubsidyAnalyzerGraph
        
        # Test with default model
        analyzer = SubsidyAnalyzerGraph()
        print("✅ SubsidyAnalyzerGraph created with default model")
        print(f"   Model: {analyzer.llm.model_name}")
        print(f"   Workflow type: {type(analyzer.workflow)}")
        
        # Test with specific model
        analyzer2 = SubsidyAnalyzerGraph(model="gpt-4o")
        print("✅ SubsidyAnalyzerGraph created with specific model")
        print(f"   Model: {analyzer2.llm.model_name}")
        
        return True
    except Exception as e:
        print(f"❌ Graph instantiation error: {e}")
        return False


def main():
    """Run all tests."""
    print("🚀 LangGraph Subsidy Analyzer - Structure Test")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_compiled_graph,
        test_llm_creation,
        test_graph_instantiation
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
        print()
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print("📊 Test Summary")
    print("-" * 20)
    print(f"Passed: {passed}/{total}")
    print(f"Failed: {total - passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed! Structure is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)