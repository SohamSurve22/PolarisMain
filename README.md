# PolarisLex — Legal Document Parser

Deterministic pipeline that extracts text from legal documents (PDF, DOCX, TXT, HTML), cleans it, detects structure, and extracts clauses into a Canonical Intermediate Representation (JSON).

## Quick start

```bash
# 1. Clone
git clone https://github.com/<your-org>/polarislex.git
cd polarislex

# 2. Create venv
python -m venv .venv
.venv\Scripts\activate    # Windows
source .venv/bin/activate # macOS/Linux

# 3. Install
pip install -r requirements.txt
```

## Usage

### CLI

```bash
# Parse a document and print JSON to stdout
python -m backend.app.services.document_processing path/to/document.pdf

# Parse with summary + save to file
python -m backend.app.services.document_processing doc.pdf -o output.json --summary

# Launch web UI
python -m backend.app.services.document_processing --serve
```

### Web UI

The `--serve` flag starts a FastAPI UI at `http://127.0.0.1:8000` where you can paste text or upload files.

### Python

```python
from backend.app.services.document_processing import DocumentProcessor

proc = DocumentProcessor.create_default()
result = proc.process_file("contract.pdf")
print(result.to_json(indent=2))
```

## Tests

```bash
pytest backend/tests/ -v                          # all
pytest backend/tests/ -m unit -v                  # unit only
pytest backend/tests/ -m integration -v           # integration only
pytest backend/tests/ --cov -v                    # with coverage
```

## Project structure

```
backend/
├── app/services/document_processing/   # core library
│   ├── pipeline/                       # orchestration
│   ├── extractors/                     # PDF / DOCX / TXT / HTML
│   ├── cleaners/                       # text cleaning strategies
│   ├── structure_detectors/            # heading detection, hierarchy
│   ├── clause_extractors/              # sentence splitting, clause building
│   ├── models/                         # pydantic data models
│   ├── web/                            # FastAPI UI
│   └── cli.py                          # command-line interface
├── benchmarks/                         # performance benchmarks
├── examples/                           # usage examples
└── tests/                              # test suite
```
