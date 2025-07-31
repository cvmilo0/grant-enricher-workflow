#!/usr/bin/env python3
"""
LangGraph workflow definition for the Subsidy Analyzer
=====================================================

This module defines the main LangGraph workflow.
"""

import time
from typing import Dict, Any
import sys
import os
from pathlib import Path

# Add the parent directory to the path for absolute imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from langgraph_analyzer.llms import LanguageModel
except ImportError:
    # Fallback to simplified LLM for CLI testing
    from langgraph_analyzer.simple_llms import SimpleLLM as LanguageModel
from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableConfig
from langsmith import traceable

from langgraph_analyzer.schemas import SubsidyState
from langgraph_analyzer.nodes import (
    extract_bdns_node,
    fetch_subsidy_info_node, 
    find_pdf_urls_node,
    download_pdfs_node,
    analyze_subsidy_node,
    save_results_node
)
from langgraph_analyzer.utils import setup_logging

logger = setup_logging()


class SubsidyAnalyzerGraph:
    """
    LangGraph-based Subsidy Analyzer workflow.
    
    This class orchestrates the complete subsidy analysis process using LangGraph,
    with full tracing through LangSmith.
    """
    
    def __init__(self, model: str = "gpt-4o-mini"):
        """
        Initialize the analyzer graph.
        
        Args:
            model: LLM model to use (supports OpenAI, Gemini, DeepSeek, HuggingFace)
        """
        self.llm = LanguageModel(model_name=model)
        
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(SubsidyState)
        
        # Add nodes
        workflow.add_node("extract_bdns", extract_bdns_node)
        workflow.add_node("fetch_subsidy_info", fetch_subsidy_info_node)
        workflow.add_node("find_pdf_urls", find_pdf_urls_node)
        workflow.add_node("download_pdfs", download_pdfs_node)
        workflow.add_node("analyze_subsidy", self._create_analyze_node())
        workflow.add_node("save_results", save_results_node)
        
        # Define the flow
        workflow.set_entry_point("extract_bdns")
        workflow.add_edge("extract_bdns", "fetch_subsidy_info")
        workflow.add_edge("fetch_subsidy_info", "find_pdf_urls")
        workflow.add_edge("find_pdf_urls", "download_pdfs")
        workflow.add_edge("download_pdfs", "analyze_subsidy")
        workflow.add_edge("analyze_subsidy", "save_results")
        workflow.add_edge("save_results", END)
        
        return workflow.compile()
    
    def _create_analyze_node(self):
        """Create the analyze node with LLM dependency injection."""
        def analyze_with_llm(state: SubsidyState) -> SubsidyState:
            return analyze_subsidy_node(state, self.llm)
        return analyze_with_llm
    
    @traceable(name="analyze_subsidy_from_bdns")
    def analyze_from_bdns(self, bdns_code: str) -> Dict[str, Any]:
        """
        Analyze a subsidy from its BDNS code.
        
        Args:
            bdns_code: The BDNS code of the subsidy
            
        Returns:
            Analysis results and execution state
        """
        start_time = time.time()
        
        # Initialize state
        initial_state = SubsidyState(
            bdns_code=bdns_code,
            source_url=f"https://www.subvenciones.gob.es/bdnstrans/GE/es/convocatorias/{bdns_code}",
            subsidy_data={},
            pdf_urls=[],
            pdf_texts=[],
            pdf_count=0,
            analysis_result=None,
            raw_analysis=None,
            error=None,
            logs=[],
            processing_time=None
        )
        
        # Create run configuration
        config = RunnableConfig(
            tags=["subsidy-analysis", "bdns-input"],
            metadata={
                "bdns_code": bdns_code,
                "input_type": "bdns_code",
                "timestamp": time.time()
            }
        )
        
        try:
            # Run the workflow
            logger.info(f"Starting analysis for BDNS code: {bdns_code}")
            final_state = self.workflow.invoke(initial_state, config)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            final_state["processing_time"] = processing_time
            
            # Log results
            logger.info(f"Workflow completed for BDNS {bdns_code} in {processing_time:.2f}s")
            for log in final_state.get("logs", []):
                logger.info(f"  - {log}")
            
            if final_state.get("error"):
                logger.error(f"Workflow error: {final_state['error']}")
            
            return {
                "success": not bool(final_state.get("error")),
                "analysis_result": final_state.get("analysis_result"),
                "raw_analysis": final_state.get("raw_analysis"),
                "processing_time": processing_time,
                "pdf_count": final_state.get("pdf_count", 0),
                "logs": final_state.get("logs", []),
                "error": final_state.get("error")
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Workflow failed for BDNS {bdns_code}: {e}")
            return {
                "success": False,
                "analysis_result": None,
                "raw_analysis": None,
                "processing_time": processing_time,
                "pdf_count": 0,
                "logs": [f"Workflow failed: {str(e)}"],
                "error": str(e)
            }
    
    @traceable(name="analyze_subsidy_from_data")
    def analyze_from_data(self, subsidy_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a subsidy from existing data.
        
        Args:
            subsidy_data: Subsidy data dictionary
            
        Returns:
            Analysis results and execution state
        """
        start_time = time.time()
        
        # Extract BDNS code and URL from data
        bdns_code = subsidy_data.get("codigo_bdns") or subsidy_data.get("bdns_code")
        source_url = subsidy_data.get("source_url")
        
        if not bdns_code and not source_url:
            return {
                "success": False,
                "analysis_result": None,
                "raw_analysis": None, 
                "processing_time": 0,
                "pdf_count": 0,
                "logs": [],
                "error": "Either bdns_code or source_url must be provided in subsidy_data"
            }
        
        # Initialize state
        initial_state = SubsidyState(
            bdns_code=bdns_code or "",
            source_url=source_url,
            subsidy_data=subsidy_data,
            pdf_urls=[],
            pdf_texts=[],
            pdf_count=0,
            analysis_result=None,
            raw_analysis=None,
            error=None,
            logs=[],
            processing_time=None
        )
        
        # Create run configuration
        config = RunnableConfig(
            tags=["subsidy-analysis", "data-input"],
            metadata={
                "bdns_code": bdns_code or "unknown",
                "input_type": "subsidy_data",
                "timestamp": time.time()
            }
        )
        
        try:
            # Run the workflow
            logger.info(f"Starting analysis from data for BDNS: {bdns_code}")
            final_state = self.workflow.invoke(initial_state, config)
            
            # Calculate processing time
            processing_time = time.time() - start_time
            final_state["processing_time"] = processing_time
            
            # Log results
            logger.info(f"Workflow completed in {processing_time:.2f}s")
            for log in final_state.get("logs", []):
                logger.info(f"  - {log}")
            
            if final_state.get("error"):
                logger.error(f"Workflow error: {final_state['error']}")
            
            return {
                "success": not bool(final_state.get("error")),
                "analysis_result": final_state.get("analysis_result"),
                "raw_analysis": final_state.get("raw_analysis"),
                "processing_time": processing_time,
                "pdf_count": final_state.get("pdf_count", 0),
                "logs": final_state.get("logs", []),
                "error": final_state.get("error")
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Workflow failed: {e}")
            return {
                "success": False,
                "analysis_result": None,
                "raw_analysis": None,
                "processing_time": processing_time,
                "pdf_count": 0,
                "logs": [f"Workflow failed: {str(e)}"],
                "error": str(e)
            }
    
    @traceable(name="analyze_subsidy_from_url")
    def analyze_from_url(self, url: str) -> Dict[str, Any]:
        """
        Analyze a subsidy from a URL.
        
        Args:
            url: URL of the subsidy page
            
        Returns:
            Analysis results and execution state
        """
        # Extract BDNS code from URL
        from .utils import extract_bdns_from_url
        bdns_code = extract_bdns_from_url(url)
        
        if not bdns_code:
            return {
                "success": False,
                "analysis_result": None,
                "raw_analysis": None,
                "processing_time": 0,
                "pdf_count": 0,
                "logs": [],
                "error": f"Could not extract BDNS code from URL: {url}"
            }
        
        return self.analyze_from_bdns(bdns_code)


# Create a compiled graph instance for LangGraph CLI
def create_compiled_graph():
    """Create a compiled graph for the LangGraph CLI."""
    # Get model from environment variable, default to gpt-4o-mini
    model = os.getenv("DEFAULT_MODEL", "gpt-4o-mini")
    
    # Create analyzer instance
    analyzer = SubsidyAnalyzerGraph(model=model)
    
    # Return the compiled workflow
    return analyzer.workflow


# Export compiled graph for LangGraph CLI
compiled_graph = create_compiled_graph()