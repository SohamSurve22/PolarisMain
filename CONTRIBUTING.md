# Contributing to PolarisLex Document Parser

## Development Setup

```bash
# Clone and enter project
cd backend/

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install pymupdf pdfplumber python-docx beautifulsoup4 chardet langdetect trafilatura lxml structlog

# Install dev dependencies
pip install pytest pytest-cov ruff mypy
```

## Project Structure

```
backend/
├── app/services/document_processing/
│   ├── __init__.py          # Public API exports
│   ├── __main__.py          # CLI entry point
│   ├── cli.py               # argparse CLI
│   ├── container.py         # DocumentProcessor DI container
│   ├── settings.py          # Environment-specific settings
│   ├── cache.py             # Checksum-based result caching
│   ├── profiling.py         # cProfile + timing utilities
│   ├── concurrent.py        # ThreadPoolExecutor batch processing
│   ├── logging/             # structlog configuration
│   ├── models/              # 36+ Pydantic models (frozen)
│   ├── interfaces/          # ABCs for all processing stages
│   ├── extractors/          # PDF, DOCX, TXT, HTML extractors
│   ├── cleaners/            # 7 strategy cleaners + orchestrator
│   ├── structure_detectors/ # 3 strategy detectors + orchestrator
│   ├── clause_extractors/   # Sentence splitter, list-item, builder
│   └── pipeline/            # Sequential orchestration
├── tests/
│   ├── unit/                # 245+ unit tests
│   ├── integration/         # 21+ end-to-end tests
│   └── conftest.py          # Shared fixtures
├── benchmarks/              # Pipeline benchmark utility
└── examples/                # Example runner scripts
```

## Code Style

- **Python 3.13+** — use `str | None` syntax, not `Optional[str]`
- **Ruff** for linting — run `ruff check backend/` before committing
- **Line length**: 100 characters
- **Imports**: stdlib → third-party → local (separated by blank lines)
- **Type hints**: always annotate public methods and function signatures
- **Docstrings**: only where behavior isn't obvious from the name/types

## Testing

```bash
# Run all tests
pytest backend/tests/ -v

# Run only unit tests
pytest backend/tests/unit/ -v -m "not slow"

# Run integration tests
pytest backend/tests/integration/ -v

# Run with coverage
pytest --cov=backend/app/services/document_processing --cov-report=term-missing

# Run slow tests
pytest backend/tests/ -v -m "slow"
```

### Test Markers

| Marker | Description |
|--------|-------------|
| `slow` | Tests that take > 5 seconds |
| `integration` | Full pipeline end-to-end tests |
| `unit` | Isolated component tests (default) |
| `benchmark` | Performance benchmark tests |

## Pull Request Checklist

- [ ] All existing tests pass (`pytest backend/tests/ -q`)
- [ ] New code has tests covering success and failure paths
- [ ] Ruff linting passes (`ruff check backend/`)
- [ ] No `print()` statements — use `structlog` logger instead
- [ ] Frozen models for any new pipeline data types
- [ ] JSON serializable models (handle `bytes` via base64)

## Architecture Decisions

See the `anchored summary` in the project documentation for a running log of Architecture Decision Records (ADRs) covering:

- Pipeline pattern with Context Object
- ExtractionResult wrapper pattern
- Dual-path PDF/HTML extraction
- Cleaning strategy chain pattern
- Deterministic heading detection (10 matchers)
- Skip-chain degraded mode
- Base64 JSON encoding for binary content

## Production Checklist

Before deploying:

1. Set `POLARIS_ENV=production` to disable degraded mode
2. Configure `POLARIS_CACHE_DIR` for persistent result caching
3. Set `POLARIS_LOG_JSON=true` for structured JSON log output
4. Tune `POLARIS_MAX_WORKERS` for batch processing throughput
5. Set `POLARIS_PIPELINE_MAX_FILE_SIZE_BYTES` for your infrastructure
6. Verify `POLARIS_PIPELINE_ALLOWED_FORMATS` restricts to expected types
