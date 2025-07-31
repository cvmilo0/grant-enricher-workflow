#!/usr/bin/env python3
"""
Enhanced Subsidy Analyzer 2.0 for DocxFormatScript
==================================================

This enhanced analyzer extracts detailed, actionable requirements from subsidy analysis
that will drive the dynamic document generation process in DocxFormatScript 2.0.

The subsidy analysis becomes the "DNA" that shapes every aspect of document generation.

Author: DocxFormatScript 2.0
Version: 2.0
"""

import os
import json
import logging
import time
import requests
import re
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path
from datetime import datetime
import openai
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import PyPDF2
import io

# Load environment variables
load_dotenv()

class EnhancedSubsidyAnalyzer2_0:
    """
    Enhanced Subsidy Analyzer 2.0 - Extracts detailed requirements for dynamic document generation.
    
    This analyzer goes beyond simple analysis to extract actionable requirements that will
    drive the entire document generation process, making it subsidy-specific and compliance-focused.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini", download_dir: str = "downloaded_files"):
        """
        Initialize the enhanced analyzer.
        
        Args:
            api_key: OpenAI API key
            model: ChatGPT model to use
            download_dir: Directory to save downloaded PDFs
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY required in environment variables")
        
        self.model = model
        self.client = openai.OpenAI(api_key=self.api_key)
        self.download_dir = download_dir
        
        # Setup logging
        self.setup_logging()
        
        # Setup requests session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def setup_logging(self):
        """Setup logging system."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('enhanced_subsidy_analyzer_2_0.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def find_and_download_pdfs(self, subsidy_data: Dict[str, Any]) -> Tuple[Optional[str], int]:
        """
        Find and download ALL PDFs from the subsidy announcement.
        
        Args:
            subsidy_data: Subsidy data
            
        Returns:
            Tuple: (Combined text from all PDFs, number of PDFs downloaded)
        """
        try:
            source_url = subsidy_data.get('source_url')
            if not source_url:
                self.logger.warning("No source URL found in subsidy data")
                return None, 0
            
            self.logger.info(f"Searching for PDFs at: {source_url}")
            
            # Setup Selenium to search for PDFs
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            try:
                driver.get(source_url)
                time.sleep(3)  # Wait for page to load
                
                # Extract BDNS code from URL
                bdns_match = re.search(r'/(\d+)$', source_url)
                if bdns_match:
                    bdns_code = bdns_match.group(1)
                    self.logger.info(f"BDNS code extracted: {bdns_code}")
                    
                    # Call API to get document information
                    api_url = f"https://www.subvenciones.gob.es/bdnstrans/api/convocatorias?numConv={bdns_code}&vpd=GE"
                    self.logger.info(f"Calling API: {api_url}")
                    
                    response = self.session.get(api_url)
                    if response.status_code == 200:
                        data = response.json()
                        self.logger.info(f"API response received: {len(response.text)} characters")
                        
                        if 'documentos' in data and data['documentos']:
                            self.logger.info(f"Found {len(data['documentos'])} documents in API")
                            
                            # Download ALL PDF documents
                            pdf_texts = []
                            successful_downloads = 0
                            
                            for doc in data['documentos']:
                                # Check if it's a PDF document - try different field names
                                doc_name = doc.get('nombreFic') or doc.get('nombre') or doc.get('name') or 'Unknown'
                                doc_type = doc.get('tipo') or doc.get('type') or ''
                                
                                if doc_type == 'PDF' or 'pdf' in doc_name.lower():
                                    doc_url = f"https://www.subvenciones.gob.es/bdnstrans/GE/es/convocatoria/{bdns_code}/document/{doc['id']}"
                                    self.logger.info(f"Attempting to download: {doc_name} from {doc_url}")
                                    
                                    pdf_text = self._download_and_extract_pdf(doc_url, doc_name)
                                    if pdf_text:
                                        self.logger.info(f"PDF downloaded successfully: {doc_name}")
                                        pdf_texts.append(f"=== DOCUMENT: {doc_name} ===\n{pdf_text}")
                                        successful_downloads += 1
                                    else:
                                        self.logger.warning(f"Could not download: {doc_name}")
                                else:
                                    self.logger.info(f"Skipping non-PDF document: {doc_name} (type: {doc_type})")
                            
                            if pdf_texts:
                                combined_text = "\n\n".join(pdf_texts)
                                self.logger.info(f"Successfully processed {successful_downloads} PDFs")
                                return combined_text, successful_downloads
                
                # Fallback: try to extract PDF from page
                pdf_text, pdf_count = self._extract_pdf_from_page(driver, source_url)
                if pdf_text:
                    return pdf_text, pdf_count
                else:
                    return None, 0
                
            finally:
                driver.quit()
                
        except Exception as e:
            self.logger.error(f"Error finding/downloading PDFs: {e}")
            return None, 0
    
    def _extract_pdf_from_page(self, driver, url: str) -> Tuple[Optional[str], int]:
        """Extract PDF from webpage."""
        try:
            # Look for PDF links
            pdf_links = driver.find_elements(By.XPATH, "//a[contains(@href, '.pdf')]")
            
            for link in pdf_links:
                pdf_url = link.get_attribute('href')
                if pdf_url:
                    self.logger.info(f"Found PDF link: {pdf_url}")
                    pdf_text = self._download_and_extract_pdf(pdf_url)
                    if pdf_text:
                        return pdf_text, 1
            
            return None, 0
            
        except Exception as e:
            self.logger.error(f"Error extracting PDF from page: {e}")
            return None, 0
    
    def _download_and_extract_pdf(self, pdf_url: str, doc_name: str = None) -> Optional[str]:
        """Download and extract text from PDF."""
        try:
            self.logger.info(f"Downloading PDF: {pdf_url}")
            
            response = self.session.get(pdf_url, stream=True)
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                self.logger.info(f"Content-Type: {content_type}")
                
                # Check if it's actually a PDF
                if 'application/pdf' in content_type or 'application/octet-stream' in content_type:
                    file_size = len(response.content)
                    self.logger.info(f"File size: {file_size} bytes")
                    
                    # Save PDF to project directory with unique name
                    bdns_match = re.search(r'/(\d+)/', pdf_url)
                    if bdns_match:
                        bdns_code = bdns_match.group(1)
                        
                        # Create unique filename using document name
                        if doc_name:
                            # Clean filename: remove special chars and limit length
                            safe_name = re.sub(r'[^\w\s-]', '', doc_name)
                            safe_name = re.sub(r'[-\s]+', '_', safe_name)
                            safe_name = safe_name[:50]  # Limit length
                            pdf_filename = f"{bdns_code}_{safe_name}.pdf"
                        else:
                            # Fallback: use timestamp
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            pdf_filename = f"{bdns_code}_{timestamp}.pdf"
                        
                        pdf_path = Path(self.download_dir) / pdf_filename
                        
                        # Create directory if it doesn't exist
                        pdf_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        with open(pdf_path, 'wb') as f:
                            f.write(response.content)
                        
                        self.logger.info(f"File saved to: {pdf_path}")
                        
                        # Extract text from PDF
                        try:
                            pdf_reader = PyPDF2.PdfReader(io.BytesIO(response.content))
                            text = ""
                            
                            for page in pdf_reader.pages:
                                text += page.extract_text() + "\n"
                            
                            self.logger.info(f"PDF processed successfully. {len(text)} characters extracted")
                            return text
                            
                        except Exception as e:
                            self.logger.error(f"Error extracting text from PDF: {e}")
                            return None
                else:
                    self.logger.info(f"Unexpected Content-Type: {content_type}")
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error downloading PDF: {e}")
            return None
    
    def create_enhanced_analysis_prompt(self, subsidy_data: Dict[str, Any], pdf_text: Optional[str] = None) -> str:
        """
        Create enhanced analysis prompt for DocxFormatScript 2.0.
        
        This prompt is designed to extract detailed, actionable requirements that will drive
        the dynamic document generation process.
        
        Args:
            subsidy_data: Subsidy data
            pdf_text: Extracted PDF text (optional)
            
        Returns:
            Enhanced prompt for ChatGPT
        """
        if pdf_text:
            prompt = f"""
# ANÁLISIS MEJORADO DE SUBVENCIONES 2.0 - DOCXFORMATSCRIPT 2.0
# EXTRACCIÓN DE REQUISITOS ACCIONABLES PARA GENERACIÓN DINÁMICA DE DOCUMENTOS

## DATOS DE LA SUBVENCIÓN:
{json.dumps(subsidy_data, indent=2, ensure_ascii=False)}

## DOCUMENTO OFICIAL:
{pdf_text}

## INSTRUCCIONES DE ANÁLISIS:

Eres un analista experto de subvenciones para DocxFormatScript 2.0. Tu tarea es extraer REQUISITOS DETALLADOS Y ACCIONABLES de esta subvención que impulsarán todo el proceso de generación de documentos.

El análisis de la subvención se convierte en el "ADN" que moldea cada aspecto de la generación de documentos. Extrae información que pueda usarse para:

1. **PERSONALIZAR LA ESTRUCTURA DEL DOCUMENTO** - ¿Qué secciones son requeridas?
2. **GENERAR CONTENIDO ESPECÍFICO DE LA SUBVENCIÓN** - ¿Qué debe incluir cada sección?
3. **CREAR PRESUPUESTOS CONFORMES** - ¿Qué categorías y límites aplican?
4. **ESTABLECER CRONOGRAMAS DEL PROYECTO** - ¿Qué fechas límite deben cumplirse?
5. **DEFINIR CRITERIOS DE EVALUACIÓN** - ¿Qué será evaluado?

## FORMATO DE SALIDA REQUERIDO:

Devuelve un objeto JSON con la siguiente estructura:

{{
    "subsidy_metadata": {{
        "code": "Código BDNS",
        "title": "Título oficial",
        "sector": "Sector objetivo",
        "region": "Alcance geográfico",
        "total_budget": "Presupuesto total disponible",
        "max_per_beneficiary": "Máximo por beneficiario",
        "cofinancing_percentage": "Porcentaje de cofinanciación requerido"
    }},
    
    "document_requirements": {{
        "required_sections": ["Lista de secciones requeridas del documento"],
        "optional_sections": ["Lista de secciones opcionales"],
        "section_priorities": {{"section_name": "alta/media/baja"}},
        "page_limits": {{"section_name": "páginas_máximas"}},
        "format_requirements": ["Requisitos específicos de formato"]
    }},
    
    "content_requirements": {{
        "objectives_criteria": ["Qué deben abordar los objetivos"],
        "methodology_requirements": ["Qué debe incluir la metodología"],
        "budget_categories": ["Categorías de presupuesto requeridas"],
        "timeline_constraints": ["Requisitos de cronograma"],
        "evaluation_criteria": ["Qué buscan los evaluadores"],
        "key_phrases": ["Términos/frases importantes a usar"],
        "avoid_phrases": ["Términos/frases a evitar"]
    }},
    
    "budget_requirements": {{
        "eligible_expenses": ["Lista de tipos de gastos elegibles"],
        "ineligible_expenses": ["Lista de tipos de gastos no elegibles"],
        "category_limits": {{"category": "límite_porcentaje"}},
        "justification_requirements": ["Requisitos de justificación presupuestaria"],
        "supporting_docs": ["Documentación presupuestaria requerida"]
    }},
    
    "timeline_requirements": {{
        "application_deadline": "YYYY-MM-DD",
        "project_start_date": "Fecha de inicio más temprana permitida",
        "project_end_date": "Fecha de finalización más tardía permitida",
        "duration_constraints": "Duración mínima/máxima del proyecto",
        "milestone_requirements": ["Hitos requeridos del proyecto"],
        "reporting_deadlines": ["Requisitos de reportes"]
    }},
    
    "evaluation_criteria": {{
        "scoring_system": "Cómo se puntúan los proyectos",
        "weight_factors": {{"criterion": "porcentaje_peso"}},
        "elimination_criteria": ["Razones de rechazo automático"],
        "bonus_factors": ["Oportunidades de puntuación adicional"],
        "documentation_impact": "Cómo la documentación afecta la puntuación"
    }},
    
    "compliance_requirements": {{
        "eligibility_criteria": ["Quién puede aplicar"],
        "exclusion_criteria": ["Quién no puede aplicar"],
        "documentation_checklist": ["Documentos requeridos"],
        "certification_requirements": ["Certificaciones requeridas"],
        "legal_requirements": ["Legal compliance needs"]
    }},
    
    "strategic_recommendations": {{
        "key_success_factors": ["What makes applications successful"],
        "common_mistakes": ["What to avoid"],
        "competitive_advantages": ["How to stand out"],
        "risk_factors": ["Potential risks"],
        "preparation_timeline": "Recommended preparation time"
    }},
    
    "documentation_templates": {{
        "required_forms": ["Official forms to use"],
        "template_sources": ["Where to get templates"],
        "formatting_standards": ["Document formatting requirements"],
        "submission_format": "How to submit (digital/paper)"
    }}
}}

## EXTRACTION GUIDELINES:

1. **BE SPECIFIC**: Extract exact numbers, dates, percentages, and requirements
2. **BE ACTIONABLE**: Provide information that can directly guide document generation
3. **BE COMPLETE**: Cover all aspects that affect document creation
4. **BE ACCURATE**: Base everything on the official document
5. **BE STRUCTURED**: Organize information for easy processing

## IMPORTANT:
- Extract information that can be used to customize document generation prompts
- Identify requirements that will shape budget categories and amounts
- Find timeline constraints that will determine project scheduling
- Discover evaluation criteria that will guide content focus
- Extract compliance requirements that will ensure eligibility

Generate a comprehensive, structured analysis that can serve as the foundation for dynamic, subsidy-specific document generation.
"""
        else:
            # Fallback prompt without PDF
            prompt = f"""
# ENHANCED SUBSIDY ANALYSIS 2.0 - DOCXFORMATSCRIPT 2.0
# EXTRACTING ACTIONABLE REQUIREMENTS FOR DYNAMIC DOCUMENT GENERATION

## SUBSIDY DATA:
{json.dumps(subsidy_data, indent=2, ensure_ascii=False)}

## ANALYSIS INSTRUCTIONS:

You are an expert subsidy analyst for DocxFormatScript 2.0. Your task is to extract DETAILED, ACTIONABLE REQUIREMENTS from this subsidy that will drive the entire document generation process.

Based on your expert knowledge of Spanish subsidies and the provided data, extract information that can be used to customize document generation.

## REQUIRED OUTPUT FORMAT:

Return a JSON object with the same structure as specified above, but based on your expert knowledge rather than official document text.

## EXTRACTION GUIDELINES:

1. **BE SPECIFIC**: Provide concrete, actionable information
2. **BE REALISTIC**: Base recommendations on typical subsidy requirements
3. **BE COMPLETE**: Cover all aspects that affect document creation
4. **BE STRUCTURED**: Organize information for easy processing

Generate a comprehensive, structured analysis that can serve as the foundation for dynamic, subsidy-specific document generation.
"""
        
        return prompt
    
    def analyze_subsidy_enhanced(self, subsidy_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhanced subsidy analysis that returns structured, actionable requirements.
        
        Args:
            subsidy_data: Subsidy data
            
        Returns:
            Structured analysis with actionable requirements
        """
        try:
            self.logger.info(f"Starting enhanced analysis for subsidy: {subsidy_data.get('codigo_bdns', 'N/A')}")
            
            # Try to download and process PDFs
            pdf_text, pdf_count = self.find_and_download_pdfs(subsidy_data)
            
            if pdf_text:
                if pdf_count == 1:
                    self.logger.info(f"Using 1 PDF document for enhanced analysis")
                else:
                    self.logger.info(f"Using {pdf_count} PDF documents for enhanced analysis")
                prompt = self.create_enhanced_analysis_prompt(subsidy_data, pdf_text)
            else:
                self.logger.info("No PDFs found, using JSON data for enhanced analysis")
                prompt = self.create_enhanced_analysis_prompt(subsidy_data)
            
            # Call ChatGPT for enhanced analysis
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un analista experto de subvenciones para DocxFormatScript 2.0. Tu tarea es extraer requisitos detallados y accionables de los datos de la subvención que impulsarán la generación dinámica de documentos. Siempre responde con JSON válido en el formato exacto especificado."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=6000,
                temperature=0.2
            )
            
            # Extract and parse response
            analysis_text = response.choices[0].message.content
            
            # Try to extract JSON from response
            try:
                # Find JSON in the response
                json_match = re.search(r'\{.*\}', analysis_text, re.DOTALL)
                if json_match:
                    analysis_json = json.loads(json_match.group())
                else:
                    # If no JSON found, create a basic structure
                    analysis_json = self._create_fallback_analysis(subsidy_data)
                
                # Add metadata
                analysis_json['analysis_metadata'] = {
                    'analysis_date': datetime.now().isoformat(),
                    'subsidy_code': subsidy_data.get('codigo_bdns', subsidy_data.get('bdns_code', 'unknown')),
                    'used_pdf': bool(pdf_text),
                    'model_used': self.model,
                    'version': '2.0'
                }
                
                # Save structured analysis
                subsidy_code = subsidy_data.get('codigo_bdns', subsidy_data.get('bdns_code', 'unknown'))
                analysis_file_path = self.save_enhanced_analysis(analysis_json, subsidy_code, used_pdf=bool(pdf_text))
                
                self.logger.info("Enhanced analysis completed successfully")
                return analysis_json
                
            except json.JSONDecodeError as e:
                self.logger.error(f"Error parsing JSON response: {e}")
                # Create fallback analysis
                fallback_analysis = self._create_fallback_analysis(subsidy_data)
                return fallback_analysis
            
        except Exception as e:
            self.logger.error(f"Error in enhanced analysis: {e}")
            # Return fallback analysis
            return self._create_fallback_analysis(subsidy_data)
    
    def _create_fallback_analysis(self, subsidy_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a fallback analysis when the main analysis fails."""
        return {
            "subsidy_metadata": {
                "code": subsidy_data.get('codigo_bdns', subsidy_data.get('bdns_code', 'unknown')),
                "title": subsidy_data.get('title', 'Unknown'),
                "sector": "General",
                "region": "Spain",
                "total_budget": "Unknown",
                "max_per_beneficiary": "Unknown",
                "cofinancing_percentage": "Unknown"
            },
            "document_requirements": {
                "required_sections": ["INTRODUCCIÓN", "OBJETIVOS", "METODOLOGÍA", "PRESUPUESTO", "CRONOGRAMA"],
                "optional_sections": ["ANEXOS"],
                "section_priorities": {"INTRODUCCIÓN": "high", "OBJETIVOS": "high", "PRESUPUESTO": "high"},
                "page_limits": {},
                "format_requirements": ["Professional format", "Clear structure"]
            },
            "content_requirements": {
                "objectives_criteria": ["Clear, measurable objectives"],
                "methodology_requirements": ["Detailed project methodology"],
                "budget_categories": ["Personnel", "Equipment", "Materials", "Services"],
                "timeline_constraints": ["Realistic project timeline"],
                "evaluation_criteria": ["Project feasibility", "Economic impact"],
                "key_phrases": ["Innovation", "Sustainability", "Economic impact"],
                "avoid_phrases": ["Generic terms", "Vague descriptions"]
            },
            "budget_requirements": {
                "eligible_expenses": ["Personnel costs", "Equipment", "Materials", "External services"],
                "ineligible_expenses": ["Overhead costs", "Administrative expenses"],
                "category_limits": {},
                "justification_requirements": ["Detailed cost breakdown"],
                "supporting_docs": ["Quotes", "Invoices"]
            },
            "timeline_requirements": {
                "application_deadline": "Unknown",
                "project_start_date": "Unknown",
                "project_end_date": "Unknown",
                "duration_constraints": "6-12 months",
                "milestone_requirements": ["Project milestones"],
                "reporting_deadlines": ["Progress reports"]
            },
            "evaluation_criteria": {
                "scoring_system": "Points-based evaluation",
                "weight_factors": {"Technical quality": 40, "Economic impact": 30, "Feasibility": 30},
                "elimination_criteria": ["Incomplete applications"],
                "bonus_factors": ["Innovation", "Sustainability"],
                "documentation_impact": "High"
            },
            "compliance_requirements": {
                "eligibility_criteria": ["Spanish companies", "Sector alignment"],
                "exclusion_criteria": ["Non-compliant companies"],
                "documentation_checklist": ["Company documents", "Project description"],
                "certification_requirements": ["Legal compliance"],
                "legal_requirements": ["Spanish law compliance"]
            },
            "strategic_recommendations": {
                "key_success_factors": ["Clear objectives", "Detailed methodology", "Realistic budget"],
                "common_mistakes": ["Vague descriptions", "Unrealistic budgets"],
                "competitive_advantages": ["Innovation", "Sustainability focus"],
                "risk_factors": ["Incomplete documentation"],
                "preparation_timeline": "2-3 months"
            },
            "documentation_templates": {
                "required_forms": ["Application form"],
                "template_sources": ["Official website"],
                "formatting_standards": ["Professional format"],
                "submission_format": "Digital"
            },
            "analysis_metadata": {
                "analysis_date": datetime.now().isoformat(),
                "subsidy_code": subsidy_data.get('codigo_bdns', subsidy_data.get('bdns_code', 'unknown')),
                "used_pdf": False,
                "model_used": self.model,
                "version": "2.0",
                "fallback_analysis": True
            }
        }
    
    def save_enhanced_analysis(self, analysis_json: Dict[str, Any], subsidy_code: str, used_pdf: bool = False) -> str:
        """
        Save enhanced analysis as JSON file.
        
        Args:
            analysis_json: Structured analysis data
            subsidy_code: Subsidy code
            used_pdf: Whether PDF was used for analysis
            
        Returns:
            Path to saved file
        """
        # Use the same directory where PDF was saved
        output_dir = self.download_dir
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pdf_indicator = "_with_PDF" if used_pdf else "_JSON_only"
        filename = f"Enhanced_Analysis_{subsidy_code}_{timestamp}{pdf_indicator}.json"
        filepath = Path(output_dir) / filename
        
        # Save analysis
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(analysis_json, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Enhanced analysis saved to: {filepath}")
        return str(filepath)
    
    def get_document_generation_requirements(self, analysis_json: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract document generation requirements from enhanced analysis.
        
        This method transforms the subsidy analysis into specific requirements
        that will drive the document generation process.
        
        Args:
            analysis_json: Enhanced analysis data
            
        Returns:
            Document generation requirements
        """
        requirements = {
            "document_structure": {
                "required_sections": analysis_json.get("document_requirements", {}).get("required_sections", []),
                "optional_sections": analysis_json.get("document_requirements", {}).get("optional_sections", []),
                "section_priorities": analysis_json.get("document_requirements", {}).get("section_priorities", {}),
                "page_limits": analysis_json.get("document_requirements", {}).get("page_limits", {})
            },
            
            "content_guidelines": {
                "objectives_criteria": analysis_json.get("content_requirements", {}).get("objectives_criteria", []),
                "methodology_requirements": analysis_json.get("content_requirements", {}).get("methodology_requirements", []),
                "evaluation_criteria": analysis_json.get("content_requirements", {}).get("evaluation_criteria", []),
                "key_phrases": analysis_json.get("content_requirements", {}).get("key_phrases", []),
                "avoid_phrases": analysis_json.get("content_requirements", {}).get("avoid_phrases", [])
            },
            
            "budget_guidelines": {
                "eligible_expenses": analysis_json.get("budget_requirements", {}).get("eligible_expenses", []),
                "ineligible_expenses": analysis_json.get("budget_requirements", {}).get("ineligible_expenses", []),
                "category_limits": analysis_json.get("budget_requirements", {}).get("category_limits", {}),
                "max_per_beneficiary": analysis_json.get("subsidy_metadata", {}).get("max_per_beneficiary", "Unknown"),
                "cofinancing_percentage": analysis_json.get("subsidy_metadata", {}).get("cofinancing_percentage", "Unknown")
            },
            
            "timeline_guidelines": {
                "application_deadline": analysis_json.get("timeline_requirements", {}).get("application_deadline", "Unknown"),
                "project_duration": analysis_json.get("timeline_requirements", {}).get("duration_constraints", "Unknown"),
                "milestone_requirements": analysis_json.get("timeline_requirements", {}).get("milestone_requirements", [])
            },
            
            "compliance_requirements": {
                "eligibility_criteria": analysis_json.get("compliance_requirements", {}).get("eligibility_criteria", []),
                "documentation_checklist": analysis_json.get("compliance_requirements", {}).get("documentation_checklist", []),
                "certification_requirements": analysis_json.get("compliance_requirements", {}).get("certification_requirements", [])
            },
            
            "strategic_focus": {
                "key_success_factors": analysis_json.get("strategic_recommendations", {}).get("key_success_factors", []),
                "competitive_advantages": analysis_json.get("strategic_recommendations", {}).get("competitive_advantages", []),
                "risk_factors": analysis_json.get("strategic_recommendations", {}).get("risk_factors", [])
            }
        }
        
        return requirements

def main():
    """Main function for testing the enhanced analyzer."""
    analyzer = EnhancedSubsidyAnalyzer2_0()
    
    # Example subsidy data
    test_subsidy = {
        "codigo_bdns": "845133",
        "title": "Test Subsidy",
        "source_url": "https://www.subvenciones.gob.es/bdnstrans/GE/es/convocatorias/845133"
    }
    
    # Run enhanced analysis
    analysis = analyzer.analyze_subsidy_enhanced(test_subsidy)
    
    # Extract document generation requirements
    requirements = analyzer.get_document_generation_requirements(analysis)
    
    print("Enhanced Analysis Complete!")
    print(f"Analysis saved for subsidy: {test_subsidy['codigo_bdns']}")
    print(f"Document generation requirements extracted: {len(requirements)} categories")

if __name__ == "__main__":
    main() 