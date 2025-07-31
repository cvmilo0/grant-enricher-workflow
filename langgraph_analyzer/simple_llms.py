#!/usr/bin/env python3
"""
Simplified LLM class for LangGraph CLI compatibility
===================================================

This is a simplified version that only supports OpenAI models to avoid
dependency issues when testing with langgraph dev.
"""

import os
from langchain_openai import ChatOpenAI
from langchain_core.runnables.config import RunnableConfig
from langsmith import traceable
from dotenv import load_dotenv

load_dotenv()


class SimpleLLM:
    """Simplified LLM class that only supports OpenAI models."""
    
    def __init__(self, model_name: str = "gpt-4o-mini"):
        """Initialize with OpenAI model only."""
        self.model_name = model_name
        
        # Only support OpenAI models for CLI testing
        if model_name not in ["gpt-4o-mini", "gpt-4o"]:
            model_name = "gpt-4o-mini"  # Default fallback
            
        self.model = ChatOpenAI(
            model_name=model_name,
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            temperature=0.2,
            max_tokens=4000
        )
    
    @traceable(name="simple_llm_invoke")
    def invoke(self, input, config: RunnableConfig = None):
        """Invoke the model and return response with simple token tracking."""
        # For CLI testing, we'll use a simplified approach
        response = self.model.invoke(input, config=config)
        
        # Simple token estimation (for demo purposes)
        input_text = ""
        if isinstance(input, list):
            for msg in input:
                if hasattr(msg, 'content'):
                    input_text += str(msg.content)
        elif isinstance(input, str):
            input_text = input
            
        # Very rough token estimation
        input_tokens = len(input_text.split()) * 1.3  # Rough approximation
        output_tokens = len(response.content.split()) * 1.3 if hasattr(response, 'content') else 0
        
        token_usage = [{
            "model_name": self.model_name,
            "input_tokens": int(input_tokens),
            "output_tokens": int(output_tokens)
        }]
        
        return response, token_usage