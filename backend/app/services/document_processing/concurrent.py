from __future__ import annotations

import concurrent.futures
import os
import time
from pathlib import Path
from typing import Any, Callable, Iterator

from .logging import get_logger
from .models import CanonicalIntermediateRepresentation


class BatchProcessor:
    def __init__(
        self,
        max_workers: int | None = None,
        show_progress: bool = True,
    ):
        self._max_workers = max_workers or min(32, (os.cpu_count() or 1) + 4)
        self._show_progress = show_progress
        self._log = get_logger("polaris.batch")

    def process_files(
        self,
        filepaths: list[str | Path],
        process_fn: Callable[[str | Path], CanonicalIntermediateRepresentation],
    ) -> list[tuple[str, CanonicalIntermediateRepresentation | None, float, str | None]]:
        results: list[tuple[str, CanonicalIntermediateRepresentation | None, float, str | None]] = []
        total = len(filepaths)
        completed = 0
        failed = 0

        self._log.info("batch_start", total=total, workers=self._max_workers)

        with concurrent.futures.ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            future_map = {
                executor.submit(self._safe_process, fp, process_fn): fp
                for fp in filepaths
            }

            for future in concurrent.futures.as_completed(future_map):
                fp = future_map[future]
                try:
                    result, elapsed, error = future.result()
                    if error:
                        failed += 1
                    else:
                        completed += 1
                    results.append((str(fp), result, elapsed, error))
                except Exception as exc:
                    failed += 1
                    results.append((str(fp), None, 0.0, str(exc)))

                if self._show_progress:
                    done = completed + failed
                    self._log.info(
                        "batch_progress",
                        completed=completed,
                        failed=failed,
                        total=total,
                        remaining=total - done,
                    )

        self._log.info(
            "batch_complete",
            completed=completed,
            failed=failed,
            total=total,
        )
        return results

    def process_bytes_batch(
        self,
        items: list[tuple[bytes, str]],
        process_fn: Callable[[bytes, str], CanonicalIntermediateRepresentation],
    ) -> list[tuple[str, CanonicalIntermediateRepresentation | None, float, str | None]]:
        results: list[tuple[str, CanonicalIntermediateRepresentation | None, float, str | None]] = []
        total = len(items)

        with concurrent.futures.ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            future_map = {
                executor.submit(self._safe_process_bytes, content, name, process_fn): name
                for content, name in items
            }

            for future in concurrent.futures.as_completed(future_map):
                name = future_map[future]
                try:
                    result, elapsed, error = future.result()
                    results.append((name, result, elapsed, error))
                except Exception as exc:
                    results.append((name, None, 0.0, str(exc)))

        return results

    @staticmethod
    def _safe_process(
        filepath: str | Path,
        fn: Callable[[str | Path], CanonicalIntermediateRepresentation],
    ) -> tuple[CanonicalIntermediateRepresentation | None, float, str | None]:
        start = time.time()
        try:
            result = fn(filepath)
            elapsed = (time.time() - start) * 1000
            return result, elapsed, None
        except Exception as exc:
            elapsed = (time.time() - start) * 1000
            return None, elapsed, str(exc)

    @staticmethod
    def _safe_process_bytes(
        content: bytes,
        name: str,
        fn: Callable[[bytes, str], CanonicalIntermediateRepresentation],
    ) -> tuple[CanonicalIntermediateRepresentation | None, float, str | None]:
        start = time.time()
        try:
            result = fn(content, name)
            elapsed = (time.time() - start) * 1000
            return result, elapsed, None
        except Exception as exc:
            elapsed = (time.time() - start) * 1000
            return None, elapsed, str(exc)


class PipelineProgress:
    def __init__(self, total_stages: int = 4):
        self._total = total_stages
        self._current = 0
        self._log = get_logger("polaris.pipeline.progress")

    def advance(self, stage_name: str) -> None:
        self._current += 1
        self._log.info(
            "pipeline_progress",
            stage=stage_name,
            current=self._current,
            total=self._total,
            remaining=self._total - self._current,
        )

    @property
    def progress(self) -> float:
        return self._current / self._total if self._total else 1.0
