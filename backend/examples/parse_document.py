#!/usr/bin/env python3
"""
PolarisLex Legal Document Parser — Example Runner.

Parses a document file and prints a structured summary.
Usage:
    python -m backend.examples.parse_document path/to/document.pdf
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.document_processing import DocumentProcessor, configure_logging, get_logger


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    filepath = Path(sys.argv[1])
    if not filepath.exists():
        print(f"Error: file not found — {filepath}")
        sys.exit(1)

    configure_logging(log_level="INFO")
    log = get_logger("example")

    processor = DocumentProcessor.create_default()
    log.info("starting", file=str(filepath))

    start = time.time()
    result = processor.process_file(filepath)
    elapsed = time.time() - start

    stats = result.metadata.statistics
    stages = result.metadata.stages

    print(f"\n{'='*60}")
    print(f"  PolarisLex — Document Analysis Report")
    print(f"{'='*60}")
    print(f"  File:        {stats.filename}")
    print(f"  Format:      {stats.format.value}")
    print(f"  Size:        {stats.file_size_bytes:,} bytes")
    print(f"  Pages:       {stats.page_count or 'N/A'}")
    print(f"  Words:       {stats.word_count:,}")
    print(f"  Language:    {stats.language or 'N/A'}")
    print(f"  Status:      {result.metadata.processing_status}")
    print(f"  Time:        {elapsed*1000:.2f} ms")
    print(f"{'='*60}")

    print(f"\n  Structure: {stats.structural_element_count} elements, {stats.section_count} sections")
    print(f"  Clauses:   {stats.clause_count} total ({stats.root_clause_count} root)")
    print(f"  Cleaning:  {len(stats.cleaning_operations_applied)} operations applied")

    print(f"\n  Stages:")
    for s in stages:
        sym = {"success": "+", "degraded": "~", "skipped": "-", "failed": "x"}.get(s.status, "?")
        print(f"    [{sym}] {s.stage_name:20s} {s.duration_ms:>8.2f}ms")
        if s.error:
            print(f"         {s.error.message[:100]}")

    if result.clause_document:
        print(f"\n  Clauses (top {min(5, result.clause_document.clause_count)}):")
        for cid in result.clause_document.root_clause_ids[:5]:
            clause = result.clause_document.clauses[cid]
            body_preview = clause.body[:80].replace("\n", " ")
            print(f"    [{clause.clause_number or '?'}] {body_preview}...")

    print(f"\n  JSON output: {result.to_json(indent=2, exclude_raw_content=True)[:200]}...")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
