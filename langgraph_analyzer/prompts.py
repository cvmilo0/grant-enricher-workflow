#!/usr/bin/env python3
"""
Prompts for the Subsidy Analyzer
================================

This module contains all the prompts used for LLM interactions.
"""

SYSTEM_PROMPT = """Eres un analista experto en convocatorias de subvenciones españolas. Tu tarea es extraer información estructurada y relevante de los documentos oficiales de convocatorias.

Debes extraer EXACTAMENTE la información solicitada en el formato JSON especificado. Sé preciso y usa las palabras exactas del documento cuando sea posible."""


ANALYSIS_PROMPT_WITH_PDF = """# ANÁLISIS DE CONVOCATORIA DE SUBVENCIÓN

## DATOS DE LA CONVOCATORIA:
{subsidy_data}

## DOCUMENTOS OFICIALES:
{pdf_text}

## INSTRUCCIONES:

Extrae la siguiente información de la convocatoria y devuélvela en formato JSON:

```json
{{
    "identificacion": {{
        "organismo_emisor": "Organismo que publica la ayuda (ej: Consejería, Dirección General, etc.)",
        "titulo_convocatoria": "Título completo o objeto de la convocatoria",
        "base_reguladora": "Normativa principal (Orden, Real Decreto, etc. con fecha)"
    }},
    
    "detalles": {{
        "beneficiarios": ["Lista de tipos de beneficiarios que pueden solicitar"],
        "finalidad_ayuda": "Descripción del concepto específico que se subvenciona"
    }},
    
    "condiciones_economicas": {{
        "presupuesto_total": "Cantidad total disponible (incluir moneda y detalles)",
        "distribucion_territorial": {{
            "provincia/territorio": "cantidad asignada"
        }},
        "cuantia_por_solicitud": "Importe máximo por beneficiario o método de cálculo"
    }},
    
    "plazos_procedimiento": {{
        "plazo_presentacion": "Fechas de inicio y fin (formato: 'Del DD/MM/AAAA al DD/MM/AAAA' o descripción)",
        "plazo_resolucion": "Tiempo máximo para resolver (ej: 'Tres meses', 'Seis meses')",
        "medio_presentacion": "Cómo presentar (ej: 'Electrónica exclusivamente', plataforma específica)",
        "enlace_tramite": "URL completa si está disponible"
    }}
}}
```

## REGLAS DE EXTRACCIÓN:

1. **PRECISIÓN**: Usa las palabras exactas del documento cuando sea posible
2. **COMPLETITUD**: Si no encuentras algún dato, indica "No especificado" 
3. **FORMATO**: Respeta exactamente la estructura JSON solicitada
4. **DISTRIBUCIÓN TERRITORIAL**: Si hay tablas de distribución por provincias o municipios, extrae los datos principales
5. **CUANTÍAS**: Incluye todos los detalles sobre importes, porcentajes, módulos o sistemas de cálculo
6. **FECHAS**: Mantén el formato original de las fechas tal como aparecen en el documento

IMPORTANTE: Devuelve ÚNICAMENTE el JSON, sin explicaciones adicionales."""


ANALYSIS_PROMPT_WITHOUT_PDF = """# ANÁLISIS DE CONVOCATORIA DE SUBVENCIÓN

## DATOS DE LA CONVOCATORIA:
{subsidy_data}

## INSTRUCCIONES:

Basándote en los datos disponibles y tu conocimiento sobre convocatorias de subvenciones españolas, genera una estructura JSON con la información típica de este tipo de convocatoria.

Devuelve la información en el siguiente formato JSON:

```json
{{
    "identificacion": {{
        "organismo_emisor": "Organismo que probablemente publica esta ayuda",
        "titulo_convocatoria": "Título o descripción de la convocatoria",
        "base_reguladora": "Normativa que probablemente la regula"
    }},
    
    "detalles": {{
        "beneficiarios": ["Tipos típicos de beneficiarios para este tipo de ayuda"],
        "finalidad_ayuda": "Propósito general de la subvención"
    }},
    
    "condiciones_economicas": {{
        "presupuesto_total": "Información no disponible - Requiere documento oficial",
        "distribucion_territorial": {{}},
        "cuantia_por_solicitud": "Información no disponible - Requiere documento oficial"
    }},
    
    "plazos_procedimiento": {{
        "plazo_presentacion": "Información no disponible - Consultar convocatoria oficial",
        "plazo_resolucion": "Típicamente entre 3-6 meses",
        "medio_presentacion": "Generalmente electrónica",
        "enlace_tramite": null
    }}
}}
```

NOTA: Esta es una aproximación basada en datos limitados. Para información precisa, es necesario acceder a los documentos oficiales de la convocatoria."""


EXTRACTION_VALIDATION_PROMPT = """Valida que la siguiente extracción de datos sea correcta y completa:

EXTRACCIÓN:
{extraction}

TEXTO ORIGINAL (fragmento):
{original_text}

Si encuentras errores o información faltante que sí está en el texto original, devuelve un JSON con las correcciones necesarias. Si todo está correcto, devuelve {"valid": true}."""