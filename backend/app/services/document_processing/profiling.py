from __future__ import annotations

import cProfile
import io
import pstats
import time
from functools import wraps
from pathlib import Path
from typing import Any, Callable

from .logging import get_logger


class Profiler:
    def __init__(self, enabled: bool = True, output_dir: str | Path | None = None):
        self._enabled = enabled
        self._output_dir = Path(output_dir) if output_dir else None
        self._log = get_logger("polaris.profiling")

    def profile(
        self,
        name: str = "pipeline",
        sort_by: str = "cumtime",
        lines: int = 30,
    ) -> Callable:
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                if not self._enabled:
                    return func(*args, **kwargs)

                profiler = cProfile.Profile()
                try:
                    profiler.enable()
                    result = func(*args, **kwargs)
                    profiler.disable()
                    return result
                finally:
                    self._write_report(profiler, name, sort_by, lines)

            return wrapper
        return decorator

    def profile_sync(self, func: Callable, *args: Any, **kwargs: Any) -> Any:
        if not self._enabled:
            return func(*args, **kwargs)

        profiler = cProfile.Profile()
        try:
            profiler.enable()
            result = func(*args, **kwargs)
            profiler.disable()
            return result
        finally:
            self._write_report(profiler, func.__name__, "cumtime", 30)

    def _write_report(
        self,
        profiler: cProfile.Profile,
        name: str,
        sort_by: str,
        lines: int,
    ) -> None:
        stream = io.StringIO()
        stats = pstats.Stats(profiler, stream=stream).sort_stats(sort_by)
        stats.print_stats(lines)

        report = stream.getvalue()
        self._log.info("profile_report", name=name, sort_by=sort_by)

        if self._output_dir:
            self._output_dir.mkdir(parents=True, exist_ok=True)
            report_path = self._output_dir / f"profile_{name}_{int(time.time())}.txt"
            report_path.write_text(report, encoding="utf-8")
            self._log.info("profile_report_saved", path=str(report_path))
        else:
            self._log.info("profile_report_data", report=report)


class Timer:
    def __init__(self, name: str = "block", logger=None):
        self._name = name
        self._log = logger or get_logger("polaris.timing")
        self._start: float | None = None

    def __enter__(self) -> "Timer":
        self._start = time.perf_counter()
        return self

    def __exit__(self, *args: Any) -> None:
        elapsed = (time.perf_counter() - self._start) * 1000
        self._log.info("timing", block=self._name, duration_ms=round(elapsed, 2))

    @property
    def elapsed_ms(self) -> float:
        if self._start is None:
            return 0.0
        return (time.perf_counter() - self._start) * 1000


def timed(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        log = get_logger(f"polaris.timing.{func.__name__}")
        start = time.perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            elapsed = (time.perf_counter() - start) * 1000
            log.info("timing", function=func.__name__, duration_ms=round(elapsed, 2))
    return wrapper
