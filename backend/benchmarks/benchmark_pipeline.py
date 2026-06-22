#!/usr/bin/env python3
"""
Pipeline benchmarking utility.

Measures throughput, per-stage timing, and memory usage for the full parsing pipeline.
"""
import sys
import time
import statistics
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services.document_processing import DocumentProcessor, DocumentFormat, configure_logging, get_logger


def generate_test_document(fmt: DocumentFormat, size: str = "medium") -> tuple[bytes, str]:
    import fitz
    from docx import Document
    import io

    texts = {
        "small": "1. Clause one.\n2. Clause two.\n3. Clause three.\n",
        "medium": (
            "1. Introduction\nThis is a medium legal document with multiple sections.\n\n"
            "2. Definitions\n(a) Term one means X.\n(b) Term two means Y.\n\n"
            "3. Obligations\n(a) Party shall deliver.\n(b) Party shall pay.\n\n"
            "4. Termination\nThis agreement terminates on the earlier of.\n\n"
            "5. Governing Law\nThe laws of India govern this agreement.\n"
        ),
        "large": (
            "\n".join(
                f"{i}. Section {i}\nThis is paragraph text for section {i}.\n"
                f"  (a) Sub-clause a of section {i}\n"
                f"  (b) Sub-clause b of section {i}\n"
                for i in range(1, 51)
            )
        ),
    }
    text = texts.get(size, texts["medium"])

    if fmt == DocumentFormat.PDF:
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), text, fontsize=11)
        data = doc.tobytes()
        doc.close()
        return data, f"bench_{size}.pdf"
    elif fmt == DocumentFormat.DOCX:
        doc = Document()
        for line in text.split("\n"):
            if line.strip():
                doc.add_paragraph(line)
        buf = io.BytesIO()
        doc.save(buf)
        return buf.getvalue(), f"bench_{size}.docx"
    else:
        return text.encode("utf-8"), f"bench_{size}.txt"


def run_benchmark(
    fmt: DocumentFormat,
    size: str = "medium",
    iterations: int = 5,
) -> dict:
    processor = DocumentProcessor.create_default()
    content, filename = generate_test_document(fmt, size)

    timings: list[float] = []
    stage_breakdown: dict[str, list[float]] = {}

    for i in range(iterations):
        start = time.perf_counter()
        result = processor.process_bytes(content, filename, fmt=fmt)
        elapsed = (time.perf_counter() - start) * 1000
        timings.append(elapsed)

        for stage in result.metadata.stages:
            if stage.stage_name not in stage_breakdown:
                stage_breakdown[stage.stage_name] = []
            stage_breakdown[stage.stage_name].append(stage.duration_ms)

    stats = result.metadata.statistics

    return {
        "format": fmt.value,
        "size": size,
        "iterations": iterations,
        "total_ms": {
            "mean": statistics.mean(timings),
            "median": statistics.median(timings),
            "min": min(timings),
            "max": max(timings),
            "stdev": statistics.stdev(timings) if len(timings) > 1 else 0,
        },
        "stages": {
            name: {
                "mean": statistics.mean(times),
                "total": sum(times),
            }
            for name, times in stage_breakdown.items()
        },
        "document": {
            "words": stats.word_count,
            "chars": stats.char_count,
            "clauses": stats.clause_count,
            "elements": stats.structural_element_count,
        },
    }


def print_report(results: list[dict]):
    print(f"\n{'='*70}")
    print(f"  PolarisLex Pipeline Benchmark Report")
    print(f"{'='*70}")
    for r in results:
        print(f"\n  [{r['format']:5s}] {r['size']:8s} x{r['iterations']} iterations")
        t = r["total_ms"]
        print(f"    Total:   {t['mean']:>8.2f} ms avg  (min={t['min']:.2f}, max={t['max']:.2f}, ±{t['stdev']:.2f})")
        for sname, stiming in r["stages"].items():
            pct = stiming["mean"] / t["mean"] * 100 if t["mean"] else 0
            print(f"    {sname:20s}: {stiming['mean']:>8.2f} ms  ({pct:5.1f}%)")
        d = r["document"]
        print(f"    Output:  {d['words']} words, {d['chars']} chars, {d['clauses']} clauses, {d['elements']} elements")
    print(f"\n{'='*70}\n")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Benchmark the document parsing pipeline")
    parser.add_argument("--iterations", type=int, default=5, help="Number of iterations per test")
    parser.add_argument("--size", choices=["small", "medium", "large"], default="medium")
    parser.add_argument("--format", choices=["pdf", "docx", "txt"], default=None,
                        help="Format to test (default: all)")
    args = parser.parse_args()

    configure_logging(log_level="WARNING")

    formats = [DocumentFormat(args.format)] if args.format else [DocumentFormat.PDF, DocumentFormat.DOCX, DocumentFormat.TXT]

    results = []
    for fmt in formats:
        result = run_benchmark(fmt, size=args.size, iterations=args.iterations)
        results.append(result)

    print_report(results)
    return 0


if __name__ == "__main__":
    sys.exit(main())
