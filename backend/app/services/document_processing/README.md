# PolarisLex — Legal Document Parser

A production-grade, deterministic legal document parsing pipeline for the PolarisLex Legal Knowledge Graph.

## Architecture

```
RawDocument
    │
    ▼
┌─────────────┐
│  Extractor  │  PDF (PyMuPDF → pdfplumber), DOCX, TXT, HTML
└──────┬──────┘
       │ ExtractedDocument
       ▼
┌─────────────┐
│   Cleaner   │  7 pluggable strategies (unicode, whitespace, headers, etc.)
└──────┬──────┘
       │ CleanedDocument
       ▼
┌─────────────┐
│  Structure  │  10 deterministic heading matchers, hierarchy builder, TOC
│  Detector   │
└──────┬──────┘
       │ StructuredDocument
       ▼
┌─────────────┐
│   Clause    │  Sentence splitter (40+ abbreviations), list-item detector
│  Extractor  │  (7 patterns), clause tree builder
└──────┬──────┘
       │ ClauseDocument
       ▼
┌─────────────┐
│  Canonical  │  IRMetadata (timing, warnings, errors, statistics, validation)
│     IR      │  JSON serialization with base64-encoded binary content
└─────────────┘
```

## Quick Start

```python
from app.services.document_processing import DocumentProcessor

processor = DocumentProcessor.create_default()

# From file
result = processor.process_file("contract.pdf")

# From bytes
with open("contract.pdf", "rb") as f:
    result = processor.process_bytes(f.read(), "contract.pdf")

print(result.to_json(indent=2))
print(f"Clauses found: {result.metadata.statistics.clause_count}")
```

## CLI

```bash
# Parse a document and print JSON to stdout
python -m app.services.document_processing contract.pdf

# Save JSON output to file
python -m app.services.document_processing contract.pdf -o output.json

# With summary
python -m app.services.document_processing contract.pdf --summary

# Custom config
python -m app.services.document_processing contract.pdf -c config.json

# Verbose logging
python -m app.services.document_processing contract.pdf -v
```

## Example Runner

```bash
python -m backend.examples.parse_document contract.pdf
```

## Benchmarking

```bash
# Default benchmark (PDF medium, 5 iterations)
python -m backend.benchmarks.benchmark_pipeline

# Customize
python -m backend.benchmarks.benchmark_pipeline --format pdf --size large --iterations 10
```

## Configuration

Load config from JSON file or environment variables:

```json
{
  "version": "1.0.0",
  "enable_degraded_mode": true,
  "cleaner": {
    "enabled_operations": ["normalize_whitespace", "merge_lines"]
  },
  "structure_detector": {
    "enable_toc_detection": true,
    "min_heading_confidence": 0.5
  }
}
```

Load via:

```python
# From file
config = PipelineConfig.from_json_file("config.json")

# From env (prefix POLARIS_PIPELINE_)
# POLARIS_PIPELINE_ENABLE_DEGRADED_MODE=false
config = PipelineConfig.from_env()

# Direct
processor = DocumentProcessor(config=config)
```

## Modules

| Module | Responsibility |
|--------|---------------|
| `models/` | 36+ Pydantic models — document, extraction, cleaning, structure, clauses, IR, config, errors |
| `interfaces/` | ABCs for extractor, cleaner, structure detector, clause extractor |
| `extractors/` | PDF (dual-path), DOCX, TXT (chardet), HTML (BS4 → trafilatura) |
| `cleaners/` | 7 strategies + `LegalCleaner` orchestrator |
| `structure_detectors/` | 3 strategies + `StructureDetector` orchestrator |
| `clause_extractors/` | Sentence splitter, list-item detector, clause builder + `ClauseExtractor` |
| `pipeline/` | `DocumentPipeline` — sequential orchestration with error boundaries |
| `logging/` | structlog-based structured logging |
| `container.py` | `DocumentProcessor` — DI convenience wrapper |

## Design Principles

- **No AI / No LegalBERT** — Fully deterministic, regex-based extraction
- **Frozen Models** — Every pipeline data model is immutable (Pydantic `frozen=True`)
- **Error Boundaries** — Each stage is wrapped; extraction failure is fatal, downstream failures are degraded/skipped
- **Strategy Pattern** — Cleaners, structure detectors, and clause extractors use pluggable strategies
- **JSON Serialization** — Full round-trip support with base64-encoded binary content

## Running Tests

```bash
# All unit tests (245+)
pytest backend/tests/unit/document_processing/ -v

# Integration tests
pytest backend/tests/integration/document_processing/ -v

# All tests
pytest backend/tests/ -v
```

## Requirements

- Python ≥ 3.13
- PyMuPDF, pdfplumber, python-docx, beautifulsoup4, chardet, langdetect, trafilatura, lxml
- structlog
