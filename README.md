# LangGraph Subsidy Analyzer

A LangGraph-based analyzer that extracts structured information from Spanish government subsidy announcements.

## 🚀 Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your OPENAI_API_KEY
```

### Usage

#### LangGraph CLI

```bash
# Start development server
langgraph dev

# Run analysis with BDNS code
langgraph run --graph subsidy_analyzer --input '{"bdns_code": "845133"}'

# Run analysis with URL
langgraph run --graph subsidy_analyzer --input '{"source_url": "https://www.subvenciones.gob.es/bdnstrans/GE/es/convocatorias/845133"}'
```

#### Python API

```python
from langgraph_analyzer import SubsidyAnalyzerGraph

# Create analyzer
analyzer = SubsidyAnalyzerGraph()

# Analyze from BDNS code
result = analyzer.analyze_from_bdns("845133")

# Analyze from URL
result = analyzer.analyze_from_url("https://www.subvenciones.gob.es/bdnstrans/GE/es/convocatorias/845133")
```

## 📊 Output Structure

The analyzer extracts:

- **Identificación**: Organismo emisor, título, base reguladora
- **Detalles**: Beneficiarios, finalidad de la ayuda
- **Condiciones Económicas**: Presupuesto, distribución territorial, cuantía
- **Plazos y Procedimiento**: Fechas límite, medio de presentación, enlaces

## 🔧 Environment Variables

```bash
# Required
OPENAI_API_KEY=your_openai_api_key

# Optional - LangSmith tracing
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=subsidy-analyzer
LANGCHAIN_API_KEY=your_langsmith_key

# Optional - Model selection
DEFAULT_MODEL=gpt-4o-mini
```

## 📁 Project Structure

```
langgraph_analyzer/
├── __init__.py          # Package exports
├── schemas.py           # Pydantic models for structured output
├── prompts.py           # LLM prompts for extraction
├── nodes.py             # LangGraph workflow nodes
├── graph.py             # Main workflow definition
├── simple_llms.py       # Simplified LLM interface
└── utils.py             # Helper functions

langgraph.json           # LangGraph CLI configuration
```

## 🎯 Key Features

- **LangGraph Workflow**: Structured multi-step analysis
- **LangSmith Tracing**: Full observability with @traceable decorators
- **PDF Processing**: Automatic download and text extraction
- **Structured Output**: Spanish subsidy analysis schema
- **Multiple Inputs**: BDNS codes, URLs, or raw data
- **Error Handling**: Robust fallback mechanisms

## 🧪 Development

```bash
# Start development server
langgraph dev

# Access Studio UI
open https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024

# View API docs
open http://127.0.0.1:2024/docs
```