#!/usr/bin/env python3
"""
Schemas for the Subsidy Analyzer
================================

This module defines the data schemas and types used throughout the analyzer.
"""

from typing import Dict, List, Optional, TypedDict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class SubsidyIdentification(BaseModel):
    """Identificación de la Convocatoria"""
    organismo_emisor: str = Field(description="Organismo que publica la ayuda")
    titulo_convocatoria: str = Field(description="Título/objeto de la convocatoria")
    base_reguladora: str = Field(description="Normativa principal que rige la convocatoria")


class SubsidyDetails(BaseModel):
    """Detalles de la Subvención"""
    beneficiarios: List[str] = Field(description="Perfil del solicitante que puede optar a la ayuda")
    finalidad_ayuda: str = Field(description="Concepto específico que se subvenciona")


class EconomicConditions(BaseModel):
    """Condiciones Económicas"""
    presupuesto_total: str = Field(description="Cantidad global de fondos disponibles")
    distribucion_territorial: Optional[Dict[str, str]] = Field(
        default=None, 
        description="Cómo se reparte el presupuesto por territorio"
    )
    cuantia_por_solicitud: str = Field(description="Importe que puede recibir cada beneficiario")


class DeadlinesAndProcedure(BaseModel):
    """Plazos y Procedimiento"""
    plazo_presentacion: str = Field(description="Fechas de inicio y fin para presentar solicitudes")
    plazo_resolucion: str = Field(description="Tiempo máximo para resolver")
    medio_presentacion: str = Field(description="Cómo y dónde presentar la solicitud")
    enlace_tramite: Optional[str] = Field(default=None, description="URL directa para realizar la solicitud")


class SubsidyAnalysisResult(BaseModel):
    """Complete analysis result with all extracted information"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    identificacion: SubsidyIdentification
    detalles: SubsidyDetails
    condiciones_economicas: EconomicConditions
    plazos_procedimiento: DeadlinesAndProcedure
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SubsidyState(TypedDict):
    """State definition for the LangGraph workflow"""
    # Input
    bdns_code: str
    source_url: Optional[str]
    
    # Processing data
    subsidy_data: Dict[str, Any]
    pdf_urls: List[Dict[str, str]]  # List of {url, name, id}
    pdf_texts: List[Dict[str, str]]  # List of {filename, text, path}
    pdf_count: int
    
    # Results
    analysis_result: Optional[SubsidyAnalysisResult]
    raw_analysis: Optional[Dict[str, Any]]  # Raw JSON from LLM
    
    # Tracking
    error: Optional[str]
    logs: List[str]
    processing_time: Optional[float]