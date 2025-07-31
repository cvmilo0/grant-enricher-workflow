#!/usr/bin/env python3
"""
Nodes for the Subsidy Analyzer LangGraph
========================================

This module contains all the node functions for the LangGraph workflow.
"""

import json
import time
import requests
import PyPDF2
import io
from typing import Dict, Any
from pathlib import Path
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import sys
from pathlib import Path

# Add the parent directory to the path for absolute imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from langchain_core.messages import HumanMessage, SystemMessage
try:
    from langgraph_analyzer.llms import LanguageModel
except ImportError:
    # Fallback to simplified LLM for CLI testing
    from langgraph_analyzer.simple_llms import SimpleLLM as LanguageModel
from langsmith import traceable

from langgraph_analyzer.schemas import SubsidyState, SubsidyAnalysisResult
from langgraph_analyzer.prompts import SYSTEM_PROMPT, ANALYSIS_PROMPT_WITH_PDF, ANALYSIS_PROMPT_WITHOUT_PDF
from langgraph_analyzer.utils import (
    extract_bdns_from_url, clean_filename, create_download_directory,
    extract_json_from_text, get_api_headers, validate_pdf_content,
    setup_logging
)

# Setup logger
logger = setup_logging()


@traceable(name="extract_bdns_code")
def extract_bdns_node(state: SubsidyState) -> SubsidyState:
    """Extract BDNS code from the URL or subsidy data."""
    try:
        bdns_code = state.get("bdns_code")
        source_url = state.get("source_url")
        
        if not bdns_code and source_url:
            # Extract BDNS code from URL
            bdns_code = extract_bdns_from_url(source_url)
            if bdns_code:
                logger.info(f"BDNS code extracted from URL: {bdns_code}")
                state["bdns_code"] = bdns_code
        
        if not bdns_code:
            # Try to get from subsidy_data
            subsidy_data = state.get("subsidy_data", {})
            bdns_code = subsidy_data.get("codigo_bdns") or subsidy_data.get("bdns_code")
            if bdns_code:
                state["bdns_code"] = bdns_code
        
        if not bdns_code:
            state["error"] = "No BDNS code could be extracted"
            return state
        
        state["logs"] = state.get("logs", []) + [f"BDNS code: {bdns_code}"]
        return state
        
    except Exception as e:
        logger.error(f"Error extracting BDNS: {e}")
        state["error"] = f"Error extracting BDNS: {e}"
        return state


@traceable(name="fetch_subsidy_information")
def fetch_subsidy_info_node(state: SubsidyState) -> SubsidyState:
    """Fetch subsidy information from the government API."""
    try:
        bdns_code = state.get("bdns_code")
        if not bdns_code:
            state["error"] = "No BDNS code available for API call"
            return state
        
        # Construct API URL
        api_url = f"https://www.subvenciones.gob.es/bdnstrans/api/convocatorias?numConv={bdns_code}&vpd=GE"
        logger.info(f"Calling API: {api_url}")
        
        # Make API request
        session = requests.Session()
        session.headers.update(get_api_headers())
        
        response = session.get(api_url, timeout=30)
        if response.status_code == 200:
            data = response.json()
            logger.info(f"API response received: {len(response.text)} characters")
            
            # Merge with existing subsidy data
            existing_data = state.get("subsidy_data", {})
            existing_data.update(data)
            state["subsidy_data"] = existing_data
            
            state["logs"] = state.get("logs", []) + ["API data fetched successfully"]
        else:
            logger.warning(f"API returned status code: {response.status_code}")
            state["logs"] = state.get("logs", []) + [f"API call failed with status: {response.status_code}"]
        
        return state
        
    except Exception as e:
        logger.error(f"Error fetching subsidy info: {e}")
        state["error"] = f"Error fetching subsidy info: {e}"
        return state


@traceable(name="find_pdf_urls")
def find_pdf_urls_node(state: SubsidyState) -> SubsidyState:
    """Find all PDF URLs from the subsidy data."""
    try:
        subsidy_data = state.get("subsidy_data", {})
        bdns_code = state.get("bdns_code")
        pdf_urls = []
        
        # Check for documents in API response
        if 'documentos' in subsidy_data and subsidy_data['documentos']:
            logger.info(f"Found {len(subsidy_data['documentos'])} documents in API")
            
            for doc in subsidy_data['documentos']:
                doc_name = doc.get('nombreFic') or doc.get('nombre') or doc.get('name') or 'Unknown'
                doc_type = doc.get('tipo') or doc.get('type') or ''
                doc_id = doc.get('id')
                
                if (doc_type == 'PDF' or 'pdf' in doc_name.lower()) and doc_id:
                    doc_url = f"https://www.subvenciones.gob.es/bdnstrans/GE/es/convocatoria/{bdns_code}/document/{doc_id}"
                    pdf_urls.append({
                        'url': doc_url,
                        'name': doc_name,
                        'id': doc_id
                    })
                    logger.info(f"Found PDF: {doc_name}")
        else:
            logger.info("No documents found in API response")
        
        state["pdf_urls"] = pdf_urls
        state["logs"] = state.get("logs", []) + [f"Found {len(pdf_urls)} PDFs"]
        return state
        
    except Exception as e:
        logger.error(f"Error finding PDFs: {e}")
        state["error"] = f"Error finding PDFs: {e}"
        return state


@traceable(name="download_and_extract_pdfs")
def download_pdfs_node(state: SubsidyState) -> SubsidyState:
    """Download all PDFs and extract text content."""
    try:
        pdf_urls = state.get("pdf_urls", [])
        bdns_code = state.get("bdns_code")
        pdf_texts = []
        successful_downloads = 0
        
        if not pdf_urls:
            logger.info("No PDFs to download")
            state["pdf_texts"] = []
            state["pdf_count"] = 0
            state["logs"] = state.get("logs", []) + ["No PDFs to download"]
            return state
        
        # Create download directory
        download_dir = create_download_directory()
        
        # Setup session
        session = requests.Session()
        session.headers.update(get_api_headers())
        
        for pdf_info in pdf_urls:
            pdf_url = pdf_info['url']
            doc_name = pdf_info['name']
            
            try:
                logger.info(f"Downloading: {doc_name} from {pdf_url}")
                
                response = session.get(pdf_url, stream=True, timeout=60)
                if response.status_code == 200:
                    content_type = response.headers.get('content-type', '')
                    
                    # Validate it's a PDF
                    if validate_pdf_content(response.content):
                        # Save PDF
                        safe_name = clean_filename(doc_name)
                        pdf_filename = f"{bdns_code}_{safe_name}.pdf"
                        pdf_path = download_dir / pdf_filename
                        
                        with open(pdf_path, 'wb') as f:
                            f.write(response.content)
                        
                        logger.info(f"Saved PDF to: {pdf_path}")
                        
                        # Extract text
                        try:
                            pdf_reader = PyPDF2.PdfReader(io.BytesIO(response.content))
                            text = ""
                            
                            for page in pdf_reader.pages:
                                text += page.extract_text() + "\n"
                            
                            if text.strip():  # Only add if we extracted text
                                pdf_texts.append({
                                    'filename': doc_name,
                                    'text': text,
                                    'path': str(pdf_path)
                                })
                                successful_downloads += 1
                                logger.info(f"Extracted {len(text)} characters from {doc_name}")
                            else:
                                logger.warning(f"No text extracted from {doc_name}")
                                
                        except Exception as e:
                            logger.error(f"Error extracting text from {doc_name}: {e}")
                    else:
                        logger.warning(f"Downloaded content is not a valid PDF: {doc_name}")
                else:
                    logger.warning(f"Failed to download {doc_name}: HTTP {response.status_code}")
                    
            except Exception as e:
                logger.error(f"Error downloading {doc_name}: {e}")
        
        state["pdf_texts"] = pdf_texts
        state["pdf_count"] = successful_downloads
        state["logs"] = state.get("logs", []) + [f"Downloaded and processed {successful_downloads} PDFs"]
        return state
        
    except Exception as e:
        logger.error(f"Error in download process: {e}")
        state["error"] = f"Error in download process: {e}"
        return state


@traceable(name="analyze_subsidy_with_llm")
def analyze_subsidy_node(state: SubsidyState, llm: LanguageModel) -> SubsidyState:
    """Analyze the subsidy using the LLM."""
    try:
        subsidy_data = state.get("subsidy_data", {})
        pdf_texts = state.get("pdf_texts", [])
        
        # Combine all PDF texts
        combined_pdf_text = ""
        if pdf_texts:
            pdf_sections = []
            for pdf in pdf_texts:
                pdf_sections.append(f"=== DOCUMENT: {pdf['filename']} ===\n{pdf['text']}")
            combined_pdf_text = "\n\n".join(pdf_sections)
        
        # Choose prompt based on whether we have PDF content
        if combined_pdf_text:
            prompt = ANALYSIS_PROMPT_WITH_PDF.format(
                subsidy_data=json.dumps(subsidy_data, indent=2, ensure_ascii=False),
                pdf_text=combined_pdf_text
            )
        else:
            prompt = ANALYSIS_PROMPT_WITHOUT_PDF.format(
                subsidy_data=json.dumps(subsidy_data, indent=2, ensure_ascii=False)
            )
        
        # Call LLM
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=prompt)
        ]
        
        logger.info("Calling LLM for analysis...")
        response, token_usage = llm.invoke(messages)
        analysis_text = response.content
        
        # Log token usage
        if token_usage:
            usage = token_usage[0]
            logger.info(f"Token usage - Model: {usage['model_name']}, Input: {usage['input_tokens']}, Output: {usage['output_tokens']}")
        
        # Extract JSON from response
        analysis_json = extract_json_from_text(analysis_text)
        
        if analysis_json:
            # Try to parse into structured format
            try:
                analysis_result = SubsidyAnalysisResult(**analysis_json)
                state["analysis_result"] = analysis_result
                logger.info("Successfully parsed analysis into structured format")
            except Exception as e:
                logger.warning(f"Could not parse into structured format: {e}")
                # Store raw JSON
                state["raw_analysis"] = analysis_json
        else:
            logger.error("Could not extract JSON from LLM response")
            state["error"] = "Could not extract valid JSON from LLM response"
            # Store raw response for debugging
            state["raw_analysis"] = {"raw_response": analysis_text}
        
        # Add metadata
        metadata = {
            'analysis_date': datetime.now().isoformat(),
            'subsidy_code': state.get("bdns_code"),
            'used_pdf': bool(pdf_texts),
            'pdf_count': len(pdf_texts),
            'model_used': llm.model_name,
            'version': '3.0-langgraph',
            'token_usage': token_usage[0] if token_usage else None
        }
        
        if state.get("analysis_result"):
            state["analysis_result"].metadata = metadata
        elif state.get("raw_analysis"):
            state["raw_analysis"]["metadata"] = metadata
        
        state["logs"] = state.get("logs", []) + ["LLM analysis completed"]
        return state
        
    except Exception as e:
        logger.error(f"Error in LLM analysis: {e}")
        state["error"] = f"Error in LLM analysis: {e}"
        return state


@traceable(name="save_analysis_results")
def save_results_node(state: SubsidyState) -> SubsidyState:
    """Save the analysis results to file."""
    try:
        analysis_result = state.get("analysis_result")
        raw_analysis = state.get("raw_analysis")
        bdns_code = state.get("bdns_code")
        pdf_count = state.get("pdf_count", 0)
        
        if not (analysis_result or raw_analysis) or not bdns_code:
            logger.warning("No analysis result or BDNS code to save")
            return state
        
        # Create download directory
        download_dir = create_download_directory()
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_indicator = f"_with_{pdf_count}_PDFs" if pdf_count > 0 else "_JSON_only"
        filename = f"LangGraph_Analysis_{bdns_code}_{timestamp}{pdf_indicator}.json"
        filepath = download_dir / filename
        
        # Prepare data for saving
        if analysis_result:
            # Convert Pydantic model to dict
            save_data = analysis_result.model_dump()
        else:
            save_data = raw_analysis
        
        # Save analysis
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Analysis saved to: {filepath}")
        state["logs"] = state.get("logs", []) + [f"Results saved to {filepath}"]
        
        return state
        
    except Exception as e:
        logger.error(f"Error saving results: {e}")
        state["error"] = f"Error saving results: {e}"
        return state