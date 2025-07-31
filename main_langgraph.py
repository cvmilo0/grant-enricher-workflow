#!/usr/bin/env python3
"""
Main script for the LangGraph Subsidy Analyzer
==============================================

This script demonstrates how to use the LangGraph-based subsidy analyzer
with LangSmith tracing.
"""

import os
import json
from dotenv import load_dotenv
from langgraph_analyzer import SubsidyAnalyzerGraph

# Load environment variables
load_dotenv()


def main():
    """Main function to demonstrate the analyzer."""
    
    # Check for required environment variables
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Error: OPENAI_API_KEY not found in environment variables")
        return
    
    # Optional: Set up LangSmith tracing
    # These should be set in your .env file
    langchain_tracing = os.getenv('LANGCHAIN_TRACING_V2', 'false').lower() == 'true'
    if langchain_tracing:
        print("✅ LangSmith tracing is enabled")
        print(f"   Project: {os.getenv('LANGCHAIN_PROJECT', 'default')}")
    else:
        print("ℹ️  LangSmith tracing is disabled")
    
    # Initialize the analyzer
    print("\n🚀 Initializing LangGraph Subsidy Analyzer...")
    analyzer = SubsidyAnalyzerGraph(model="gpt-4o-mini")
    
    # Test cases
    test_cases = [
        {
            "name": "Test with BDNS code",
            "method": "analyze_from_bdns",
            "input": "845133"
        },
        {
            "name": "Test with URL",
            "method": "analyze_from_url", 
            "input": "https://www.subvenciones.gob.es/bdnstrans/GE/es/convocatorias/845133"
        },
        {
            "name": "Test with subsidy data",
            "method": "analyze_from_data",
            "input": {
                "codigo_bdns": "845133",
                "title": "Test Subsidy",
                "source_url": "https://www.subvenciones.gob.es/bdnstrans/GE/es/convocatorias/845133"
            }
        }
    ]
    
    # Run test cases
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📊 Running Test {i}: {test_case['name']}")
        print("-" * 50)
        
        try:
            # Call the appropriate method
            method = getattr(analyzer, test_case['method'])
            result = method(test_case['input'])
            
            # Display results
            print(f"✅ Success: {result['success']}")
            print(f"⏱️  Processing time: {result['processing_time']:.2f}s")
            print(f"📄 PDFs processed: {result['pdf_count']}")
            
            if result['success']:
                analysis = result.get('analysis_result') or result.get('raw_analysis')
                if analysis:
                    # Show key extracted information
                    if hasattr(analysis, 'identificacion'):
                        # Pydantic model
                        print(f"🏛️  Organismo: {analysis.identificacion.organismo_emisor}")
                        print(f"📋 Título: {analysis.identificacion.titulo_convocatoria}")
                        print(f"💰 Presupuesto: {analysis.condiciones_economicas.presupuesto_total}")
                    elif isinstance(analysis, dict):
                        # Raw dict
                        identificacion = analysis.get('identificacion', {})
                        condiciones = analysis.get('condiciones_economicas', {})
                        print(f"🏛️  Organismo: {identificacion.get('organismo_emisor', 'N/A')}")
                        print(f"📋 Título: {identificacion.get('titulo_convocatoria', 'N/A')}")
                        print(f"💰 Presupuesto: {condiciones.get('presupuesto_total', 'N/A')}")
                else:
                    print("⚠️  No analysis result available")
            else:
                print(f"❌ Error: {result.get('error', 'Unknown error')}")
            
            # Show processing logs
            logs = result.get('logs', [])
            if logs:
                print("\n📝 Processing logs:")
                for log in logs[-3:]:  # Show last 3 logs
                    print(f"   • {log}")
            
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
        
        print("\n" + "="*50)
    
    print("\n🎉 All tests completed!")
    
    # Additional demonstration: batch processing
    if input("\n🔄 Run batch processing demo? (y/n): ").lower() == 'y':
        batch_demo(analyzer)


def batch_demo(analyzer: SubsidyAnalyzerGraph):
    """Demonstrate batch processing of multiple subsidies."""
    print("\n🔄 Batch Processing Demo")
    print("-" * 30)
    
    # List of BDNS codes to process
    bdns_codes = ["845133", "123456", "789012"]  # Mix of real and fake codes
    
    results = []
    for i, bdns_code in enumerate(bdns_codes, 1):
        print(f"\n🔍 Processing {i}/{len(bdns_codes)}: BDNS {bdns_code}")
        
        try:
            result = analyzer.analyze_from_bdns(bdns_code)
            results.append({
                "bdns_code": bdns_code,
                "success": result['success'],
                "processing_time": result['processing_time'],
                "pdf_count": result['pdf_count'],
                "error": result.get('error')
            })
            
            if result['success']:
                print(f"   ✅ Success ({result['processing_time']:.2f}s, {result['pdf_count']} PDFs)")
            else:
                print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"   💥 Exception: {e}")
            results.append({
                "bdns_code": bdns_code,
                "success": False,
                "processing_time": 0,
                "pdf_count": 0,
                "error": str(e)
            })
    
    # Summary
    print(f"\n📊 Batch Processing Summary:")
    print(f"   Total processed: {len(results)}")
    print(f"   Successful: {sum(1 for r in results if r['success'])}")
    print(f"   Failed: {sum(1 for r in results if not r['success'])}")
    
    total_time = sum(r['processing_time'] for r in results)
    total_pdfs = sum(r['pdf_count'] for r in results)
    print(f"   Total time: {total_time:.2f}s")
    print(f"   Total PDFs: {total_pdfs}")
    
    if total_time > 0:
        print(f"   Average time per subsidy: {total_time/len(results):.2f}s")


if __name__ == "__main__":
    main()