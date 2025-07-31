#!/usr/bin/env python3
"""
Factory functions for LangGraph CLI
==================================

This module provides factory functions to create graphs for the LangGraph CLI.
"""

from typing import Dict, Any, Optional
from .graph import SubsidyAnalyzerGraph


def create_subsidy_analyzer(config: Optional[Dict[str, Any]] = None) -> SubsidyAnalyzerGraph:
    """
    Factory function to create a SubsidyAnalyzerGraph instance.
    
    This function is used by the LangGraph CLI to instantiate the graph.
    
    Args:
        config: Configuration dictionary with optional parameters
        
    Returns:
        SubsidyAnalyzerGraph instance
    """
    if config is None:
        config = {}
    
    # Extract model from config, default to gpt-4o-mini
    model = config.get("model", "gpt-4o-mini")
    
    # Create and return the graph
    return SubsidyAnalyzerGraph(model=model)


# Alias for backwards compatibility
subsidy_analyzer = create_subsidy_analyzer