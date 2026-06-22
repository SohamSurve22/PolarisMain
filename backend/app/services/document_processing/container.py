from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import structlog

from .cache import CachedDocumentProcessor, DocumentCache
from .cleaners import LegalCleaner
from .clause_extractors import ClauseExtractor
from .extractors import ExtractorRegistry
from .logging import get_logger
from .models import (
    CanonicalIntermediateRepresentation,
    DocumentFormat,
    PipelineConfig,
    RawDocument,
)
from .pipeline import DocumentPipeline
from .profiling import Profiler, Timer
from .settings import Settings
from .structure_detectors import StructureDetector


class DocumentProcessor:
    def __init__(
        self,
        config: PipelineConfig | None = None,
        settings: Settings | None = None,
    ):
        self._settings = settings or Settings.from_env()
        self._config = config or self._settings.pipeline_config
        self._pipeline = DocumentPipeline(config=self._config)
        self._log = get_logger("polaris.processor")
        self._profiler = Profiler(
            enabled=self._settings.profiling_enabled,
        )

    @classmethod
    def create_default(cls) -> "DocumentProcessor":
        return cls()

    @classmethod
    def from_json_config(cls, path: str | Path) -> "DocumentProcessor":
        config = PipelineConfig.from_json_file(path)
        return cls(config=config)

    @classmethod
    def from_env(cls, prefix: str = "POLARIS_PIPELINE_") -> "DocumentProcessor":
        config = PipelineConfig.from_env(prefix=prefix)
        return cls(config=config)

    @classmethod
    def from_settings(cls, settings: Settings) -> "DocumentProcessor":
        return cls(config=settings.pipeline_config, settings=settings)

    def with_cache(self, cache_dir: str | Path | None = None) -> CachedDocumentProcessor:
        cache = DocumentCache(
            cache_dir=cache_dir or self._settings.cache_dir,
            ttl_seconds=self._settings.cache_ttl_seconds,
        )
        return CachedDocumentProcessor(self, cache)

    def process_file(self, filepath: str | Path) -> CanonicalIntermediateRepresentation:
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        fmt = self._detect_format(filepath)
        content = filepath.read_bytes()

        self._validate_file_size(content)
        raw = self._build_raw_document(content, filepath.name, fmt)

        with Timer(f"process_file:{filepath.name}", self._log) as timer:
            result = self._profiler.profile_sync(self._pipeline.run, raw)

        self._log.info(
            "file_processed",
            filename=filepath.name,
            status=result.metadata.processing_status,
            duration_ms=round(timer.elapsed_ms, 2),
            clauses=result.metadata.statistics.clause_count if result.metadata.statistics else 0,
        )
        return result

    def process_bytes(
        self,
        content: bytes,
        filename: str,
        fmt: DocumentFormat | None = None,
    ) -> CanonicalIntermediateRepresentation:
        if fmt is None:
            fmt = self._detect_format(Path(filename))

        self._validate_file_size(content)
        raw = self._build_raw_document(content, filename, fmt)

        with Timer(f"process_bytes:{filename}", self._log):
            return self._pipeline.run(raw)

    def process_raw(self, document: RawDocument) -> CanonicalIntermediateRepresentation:
        return self._pipeline.run(document)

    @property
    def config(self) -> PipelineConfig:
        return self._config

    @property
    def settings(self) -> Settings:
        return self._settings

    def _validate_file_size(self, content: bytes) -> None:
        if len(content) > self._config.max_file_size_bytes:
            from .models import FileTooLargeError
            raise FileTooLargeError(
                message=f"File size {len(content)} bytes exceeds limit of {self._config.max_file_size_bytes} bytes",
                context={"size": len(content), "limit": self._config.max_file_size_bytes},
            )

    def _build_raw_document(
        self, content: bytes, filename: str, fmt: DocumentFormat,
    ) -> RawDocument:
        return RawDocument(
            id=f"doc-{hashlib.md5(content).hexdigest()[:12]}",
            filename=filename,
            format=fmt,
            content=content,
            size_bytes=len(content),
            checksum_sha256=hashlib.sha256(content).hexdigest(),
            upload_timestamp=datetime.now(timezone.utc),
        )

    @staticmethod
    def _detect_format(path: Path) -> DocumentFormat:
        suffix = path.suffix.lower()
        mapping: dict[str, DocumentFormat] = {
            ".pdf": DocumentFormat.PDF,
            ".docx": DocumentFormat.DOCX,
            ".txt": DocumentFormat.TXT,
            ".html": DocumentFormat.HTML,
            ".htm": DocumentFormat.HTML,
        }
        ext = mapping.get(suffix)
        if ext is None:
            raise ValueError(
                f"Unsupported file format '{suffix}'. Supported: {list(mapping)}"
            )
        return ext
