#!/usr/bin/env python3
"""
Utility functions for the Subsidy Analyzer
=========================================

This module contains helper functions used across the analyzer.
"""

import re
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List


def setup_logging(log_file: str = "langgraph_subsidy_analyzer.log") -> logging.Logger:
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


def extract_bdns_from_url(url: str) -> Optional[str]:
    """Extract BDNS code from a URL."""
    bdns_match = re.search(r'/(\d+)$', url)
    if bdns_match:
        return bdns_match.group(1)
    return None


def clean_filename(filename: str, max_length: int = 50) -> str:
    """Clean a filename to be filesystem-safe."""
    # Remove special characters
    safe_name = re.sub(r'[^\w\s-]', '', filename)
    # Replace spaces and hyphens with underscores
    safe_name = re.sub(r'[-\s]+', '_', safe_name)
    # Limit length
    return safe_name[:max_length]


def create_download_directory(base_dir: str = "downloaded_files") -> Path:
    """Create and return the download directory path."""
    download_path = Path(base_dir)
    download_path.mkdir(parents=True, exist_ok=True)
    return download_path


def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """Extract JSON object from text that might contain other content."""
    # Try to find JSON in the text
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_match:
        import json
        try:
            return json.loads(json_match.group())
        except json.JSONDecodeError:
            return None
    return None


def validate_subsidy_data(data: Dict[str, Any]) -> bool:
    """Validate that subsidy data contains minimum required fields."""
    required_fields = ['codigo_bdns', 'bdns_code', 'source_url']
    return any(field in data for field in required_fields)


def format_territorial_distribution(distribution: Dict[str, str]) -> str:
    """Format territorial distribution data for display."""
    if not distribution:
        return "No hay distribución territorial especificada"
    
    lines = ["Distribución territorial:"]
    for territory, amount in distribution.items():
        lines.append(f"  - {territory}: {amount}")
    
    return "\n".join(lines)


def summarize_pdf_content(pdf_texts: List[Dict[str, str]], max_chars: int = 1000) -> str:
    """Create a summary of PDF content for logging."""
    if not pdf_texts:
        return "No PDF content available"
    
    summary_parts = []
    for pdf in pdf_texts[:3]:  # First 3 PDFs
        filename = pdf.get('filename', 'Unknown')
        text = pdf.get('text', '')
        preview = text[:max_chars] + "..." if len(text) > max_chars else text
        summary_parts.append(f"[{filename}]: {preview}")
    
    if len(pdf_texts) > 3:
        summary_parts.append(f"... and {len(pdf_texts) - 3} more PDFs")
    
    return "\n\n".join(summary_parts)


def get_api_headers() -> Dict[str, str]:
    """Get standard headers for API requests."""
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache'
    }


def validate_pdf_content(content: bytes) -> bool:
    """Validate that content is actually a PDF."""
    # Check PDF magic number
    return content.startswith(b'%PDF')


def merge_analysis_results(primary: Dict[str, Any], secondary: Dict[str, Any]) -> Dict[str, Any]:
    """Merge two analysis results, preferring primary values when available."""
    merged = primary.copy()
    
    for key, value in secondary.items():
        if key not in merged or merged[key] is None or merged[key] == "No especificado":
            merged[key] = value
        elif isinstance(value, dict) and isinstance(merged[key], dict):
            merged[key] = merge_analysis_results(merged[key], value)
        elif isinstance(value, list) and isinstance(merged[key], list):
            # Combine lists and remove duplicates
            combined = merged[key] + value
            merged[key] = list(dict.fromkeys(combined))  # Remove duplicates while preserving order
    
    return merged