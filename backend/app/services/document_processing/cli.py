from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from .container import DocumentProcessor
from .logging import configure_logging, get_logger


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="polaris-parse",
        description="PolarisLex Legal Document Parser — extract, clean, structure, and extract clauses from legal documents.",
    )
    parser.add_argument(
        "file",
        type=str,
        nargs="?",
        help="Path to the document file (PDF, DOCX, TXT, HTML)",
    )
    parser.add_argument(
        "-c", "--config",
        type=str,
        default=None,
        help="Path to JSON configuration file",
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="Output path for JSON result (default: stdout)",
    )
    parser.add_argument(
        "--exclude-raw",
        action="store_true",
        default=False,
        help="Exclude raw document content from JSON output",
    )
    parser.add_argument(
        "--json-log",
        action="store_true",
        default=False,
        help="Output logs in JSON format",
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default=None,
        help="Write logs to file instead of stderr",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        default=False,
        help="Enable debug-level logging",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        default=False,
        help="Print a summary of the parsed document",
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        default=False,
        help="Start the web-based parser testing UI",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    log_level = "DEBUG" if args.verbose else "INFO"
    configure_logging(
        log_level=log_level,
        json_format=args.json_log,
        log_file=args.log_file,
    )
    log = get_logger("polaris.cli")

    if args.config:
        log.info("loading_config", path=args.config)
        processor = DocumentProcessor.from_json_config(args.config)
    else:
        processor = DocumentProcessor.create_default()

    if args.serve:
        from backend.app.services.document_processing.web import run
        run()
        return 0

    if args.file:
        filepath = Path(args.file)
        if not filepath.exists():
            log.error("file_not_found", path=str(filepath))
            return 1

        log.info("processing_file", path=str(filepath), size=filepath.stat().st_size)
        start = time.time()

        try:
            result = processor.process_file(filepath)
        except Exception as exc:
            log.error("processing_failed", error=str(exc))
            return 1

        elapsed = time.time() - start
        log.info(
            "processing_complete",
            status=result.metadata.processing_status,
            duration_ms=round(elapsed * 1000, 2),
            clauses=result.metadata.statistics.clause_count if result.metadata.statistics else 0,
        )

        if args.output:
            result.export_json(args.output, exclude_raw_content=args.exclude_raw)
            log.info("output_written", path=args.output)
        else:
            print(result.to_json(indent=2, exclude_raw_content=args.exclude_raw))

        if args.summary:
            print_summary(result)

        return 0 if result.metadata.processing_status != "failed" else 1

    parser.print_help()
    return 0


def print_summary(result):
    stats = result.metadata.statistics
    validation = result.metadata.validation

    sep = "-" * 50
    print(f"\n{sep}")
    print("  Document Summary")
    print(f"{sep}")
    if stats:
        print(f"  File:                {stats.filename}")
        print(f"  Format:              {stats.format.value}")
        print(f"  Size:                {stats.file_size_bytes:,} bytes")
        print(f"  Pages:               {stats.page_count or 'N/A'}")
        print(f"  Words:               {stats.word_count:,}")
        print(f"  Characters:          {stats.char_count:,}")
        print(f"  Language:            {stats.language or 'N/A'}")
        print(f"  Structural elements: {stats.structural_element_count}")
        print(f"  Sections:            {stats.section_count}")
        print(f"  Clauses:             {stats.clause_count}")
        print(f"  Root clauses:        {stats.root_clause_count}")

    print(f"\n  Processing status:   {result.metadata.processing_status}")
    print(f"  Total time:          {result.metadata.total_duration_ms:.2f} ms")
    if validation:
        print(f"  Stages:              {len(validation.stages_valid)} OK / {len(validation.stages_failed)} failed / {len(validation.stages_skipped)} skipped")

    print(f"\n  Stage Details:")
    for stage in result.metadata.stages:
        status_symbol = {"success": "+", "degraded": "~", "skipped": "-", "failed": "x"}
        sym = status_symbol.get(stage.status, "?")
        print(f"    [{sym}] {stage.stage_name:20s} {stage.duration_ms:>8.2f}ms  ({stage.status})")
        if stage.error:
            print(f"         error: {stage.error.message[:120]}")

    print()


if __name__ == "__main__":
    sys.exit(main())
