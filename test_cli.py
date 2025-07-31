#!/usr/bin/env python3
"""
CLI Test Script for LangGraph Subsidy Analyzer
==============================================

This script demonstrates how to test the analyzer using the LangGraph CLI.
"""

import subprocess
import json
import os
from pathlib import Path


def test_langgraph_cli():
    """Test the analyzer using LangGraph CLI commands."""
    
    print("🧪 Testing LangGraph Subsidy Analyzer CLI")
    print("=" * 50)
    
    # Check if langgraph CLI is available
    try:
        result = subprocess.run(["langgraph", "--version"], 
                              capture_output=True, text=True, check=True)
        print(f"✅ LangGraph CLI version: {result.stdout.strip()}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ LangGraph CLI not found. Install with: pip install langgraph-cli")
        return
    
    # Test 1: List available graphs
    print("\n📋 Step 1: List available graphs")
    try:
        result = subprocess.run(["langgraph", "list"], 
                              capture_output=True, text=True, check=True)
        print("Available graphs:")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error listing graphs: {e}")
        print(f"stderr: {e.stderr}")
    
    # Test 2: Test with different inputs
    test_cases = [
        {
            "name": "BDNS code analysis",
            "input": {"bdns_code": "845133"}
        },
        {
            "name": "URL analysis", 
            "input": {"source_url": "https://www.subvenciones.gob.es/bdnstrans/GE/es/convocatorias/845133"}
        },
        {
            "name": "Subsidy data analysis",
            "input": {
                "subsidy_data": {
                    "codigo_bdns": "845133",
                    "title": "Test Subsidy",
                    "source_url": "https://www.subvenciones.gob.es/bdnstrans/GE/es/convocatorias/845133"
                }
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Step {i+1}: {test_case['name']}")
        print("-" * 40)
        
        # Create input file
        input_file = f"test_input_{i}.json"
        with open(input_file, 'w') as f:
            json.dump(test_case["input"], f, indent=2)
        
        try:
            # Run the graph with langgraph CLI (no config needed now)
            cmd = [
                "langgraph", "run",
                "--graph", "subsidy_analyzer",
                "--input", input_file
            ]
            
            print(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, 
                                  timeout=300, check=True)  # 5 minute timeout
            
            print("✅ Test completed successfully!")
            print("Output preview:")
            output = result.stdout
            if len(output) > 500:
                print(output[:500] + "...")
            else:
                print(output)
                
        except subprocess.TimeoutExpired:
            print("⏰ Test timed out (5 minutes)")
        except subprocess.CalledProcessError as e:
            print(f"❌ Test failed: {e}")
            if e.stderr:
                print(f"Error details: {e.stderr}")
        finally:
            # Cleanup temp files
            if os.path.exists(input_file):
                os.remove(input_file)
    
    print("\n🎉 CLI testing completed!")


def show_usage_examples():
    """Show example commands for using the LangGraph CLI."""
    
    print("\n📚 LangGraph CLI Usage Examples")
    print("=" * 40)
    
    examples = [
        {
            "description": "List available graphs",
            "command": "langgraph list"
        },
        {
            "description": "Run with BDNS code",
            "command": """langgraph run --graph subsidy_analyzer \\
  --input '{"bdns_code": "845133"}'"""
        },
        {
            "description": "Run with URL",
            "command": """langgraph run --graph subsidy_analyzer \\
  --input '{"source_url": "https://www.subvenciones.gob.es/bdnstrans/GE/es/convocatorias/845133"}'"""
        },
        {
            "description": "Run with subsidy data",
            "command": """langgraph run --graph subsidy_analyzer \\
  --input '{"subsidy_data": {"codigo_bdns": "845133", "title": "Test"}}'"""
        },
        {
            "description": "Start development server",
            "command": "langgraph dev"
        },
        {
            "description": "Deploy to LangGraph Cloud",
            "command": "langgraph deploy"
        }
    ]
    
    for example in examples:
        print(f"\n📌 {example['description']}:")
        print(f"   {example['command']}")
    
    print(f"\n💡 Available models:")
    models = [
        "gpt-4o-mini", "gpt-4o", "deepseek-chat",
        "gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash-lite",
        "mistral/ministral-8b", "meta-llama/llama-3.3-70b-instruct",
        "anthropic/claude-3-haiku"
    ]
    for model in models:
        print(f"   - {model}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--examples":
        show_usage_examples()
    else:
        test_langgraph_cli()
        show_usage_examples()