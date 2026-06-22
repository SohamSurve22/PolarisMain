import json
import traceback
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, UploadFile, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from backend.app.services.document_processing.container import DocumentProcessor
from backend.app.services.document_processing.models import (
    CanonicalIntermediateRepresentation,
    DocumentFormat,
    PipelineError,
    UnsupportedFormatError,
)

HERE = Path(__file__).resolve().parent

app = FastAPI(title="Polaris Parser Tester", version="0.1.0")
templates = Jinja2Templates(directory=str(HERE / "templates"))
app.mount("/static", StaticFiles(directory=str(HERE / "static")), name="static")

_processor: Optional[DocumentProcessor] = None


def get_processor() -> DocumentProcessor:
    global _processor
    if _processor is None:
        _processor = DocumentProcessor.create_default()
    return _processor


@app.on_event("startup")
def startup():
    get_processor()


def _format_enum(v):
    return v.value if hasattr(v, "value") else str(v)


def _simplify(obj):
    if obj is None:
        return None
    if isinstance(obj, list):
        return [_simplify(i) for i in obj]
    if hasattr(obj, "model_dump"):
        obj = obj.model_dump(mode="python")
    if isinstance(obj, dict):
        return {k: _simplify(v) for k, v in obj.items() if not k.startswith("_")}
    if isinstance(obj, bytes):
        return obj.decode("utf-8", errors="replace")[:500]
    return _format_enum(obj)


def _build_metadata_summary(ir: CanonicalIntermediateRepresentation):
    stats = ir.metadata.statistics
    sd = ir.structured_document
    section_count = len(sd.structure.elements) if sd and sd.structure else 0
    return {
        "status": ir.metadata.processing_status,
        "filename": ir.raw_document.filename,
        "format": _format_enum(ir.raw_document.format),
        "word_count": stats.word_count if stats else 0,
        "char_count": stats.char_count if stats else 0,
        "page_count": stats.page_count if stats else 0,
        "section_count": section_count,
        "clause_count": stats.clause_count if stats else 0,
        "language": "unknown",
        "processing_time_ms": round(ir.metadata.total_duration_ms, 2) if ir.metadata.total_duration_ms else 0,
    }


def _build_section_hierarchy(ir: CanonicalIntermediateRepresentation):
    sections = []
    sd = ir.structured_document
    if not sd or not sd.structure:
        return sections
    for elem in sd.structure.elements.values():
        sections.append({
            "level": elem.level,
            "heading": elem.text,
            "type": _format_enum(elem.type),
            "page_number": None,
        })
    return sections


def _run_pipeline(content: bytes, filename: str) -> dict:
    proc = get_processor()
    fmt = _detect_format(filename)
    ir = proc.process_bytes(content, filename, fmt)

    simplified = _simplify(ir.model_dump(mode="python"))
    summary = _build_metadata_summary(ir)
    hierarchy = _build_section_hierarchy(ir)

    return {
        "ir": simplified,
        "summary": summary,
        "sections": hierarchy,
        "json": ir.model_dump_json(indent=2),
    }


def _detect_format(filename: str) -> DocumentFormat:
    suffix = Path(filename).suffix.lower()
    mapping = {
        ".txt": DocumentFormat.TXT,
        ".pdf": DocumentFormat.PDF,
        ".docx": DocumentFormat.DOCX,
        ".html": DocumentFormat.HTML,
        ".htm": DocumentFormat.HTML,
    }
    if suffix not in mapping:
        raise UnsupportedFormatError(f"Unsupported format: {suffix}")
    return mapping[suffix]


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/parse")
async def parse(
    request: Request,
    text: str = Form(""),
    file: UploadFile = File(None),
):
    try:
        if file and file.filename:
            content = await file.read()
            filename = file.filename
        elif text.strip():
            content = text.encode("utf-8")
            filename = "input.txt"
        else:
            return JSONResponse(
                {"error": "Provide text or upload a file."},
                status_code=400,
            )

        result = _run_pipeline(content, filename)
        return JSONResponse(result)

    except UnsupportedFormatError as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    except PipelineError as e:
        return JSONResponse({"error": f"Pipeline error: {e}"}, status_code=422)
    except Exception:
        return JSONResponse(
            {"error": traceback.format_exc()},
            status_code=500,
        )


def run():
    import uvicorn
    uvicorn.run("backend.app.services.document_processing.web.main:app", host="127.0.0.1", port=8000, reload=False)


if __name__ == "__main__":
    run()
