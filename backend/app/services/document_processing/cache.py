from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from .logging import get_logger
from .models import CanonicalIntermediateRepresentation, DocumentFormat, RawDocument


class DocumentCache:
    def __init__(
        self,
        cache_dir: str | Path,
        ttl_seconds: int = 3600,
        enabled: bool = True,
    ):
        self._cache_dir = Path(cache_dir)
        self._ttl = ttl_seconds
        self._enabled = enabled
        self._log = get_logger("polaris.cache")

    def get(self, document: RawDocument) -> CanonicalIntermediateRepresentation | None:
        if not self._enabled:
            return None

        key = self._cache_key(document)
        cache_path = self._cache_path(key)

        if not cache_path.exists():
            return None

        age = time.time() - cache_path.stat().st_mtime
        if age > self._ttl:
            cache_path.unlink(missing_ok=True)
            self._log.info("cache_expired", key=key, age_seconds=round(age, 1))
            return None

        try:
            data = cache_path.read_text(encoding="utf-8")
            result = CanonicalIntermediateRepresentation.from_json(data)
            self._log.info("cache_hit", key=key, age_seconds=round(age, 1))
            return result
        except Exception as exc:
            self._log.warning("cache_read_failed", key=key, error=str(exc))
            cache_path.unlink(missing_ok=True)
            return None

    def set(self, document: RawDocument, result: CanonicalIntermediateRepresentation) -> None:
        if not self._enabled:
            return

        key = self._cache_key(document)
        cache_path = self._cache_path(key)

        try:
            self._cache_dir.mkdir(parents=True, exist_ok=True)
            json_str = result.to_json(exclude_raw_content=False)
            cache_path.write_text(json_str, encoding="utf-8")
            self._log.info("cache_write", key=key)
        except Exception as exc:
            self._log.warning("cache_write_failed", key=key, error=str(exc))

    def invalidate(self, document: RawDocument) -> None:
        key = self._cache_key(document)
        cache_path = self._cache_path(key)
        cache_path.unlink(missing_ok=True)
        self._log.info("cache_invalidated", key=key)

    def clear(self) -> None:
        if self._cache_dir.exists():
            for p in self._cache_dir.iterdir():
                if p.suffix == ".json":
                    p.unlink()
            self._log.info("cache_cleared", path=str(self._cache_dir))

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value

    def _cache_key(self, document: RawDocument) -> str:
        return document.checksum_sha256

    def _cache_path(self, key: str) -> Path:
        return self._cache_dir / f"{key}.json"


class CachedDocumentProcessor:
    def __init__(self, processor, cache: DocumentCache):
        self._processor = processor
        self._cache = cache
        self._log = get_logger("polaris.cached_processor")

    def process_file(self, filepath: str | Path) -> CanonicalIntermediateRepresentation:
        filepath = Path(filepath)
        content = filepath.read_bytes()
        return self._process(content, filepath.name, fmt=None)

    def process_bytes(
        self,
        content: bytes,
        filename: str,
        fmt: DocumentFormat | None = None,
    ) -> CanonicalIntermediateRepresentation:
        return self._process(content, filename, fmt)

    def _process(
        self,
        content: bytes,
        filename: str,
        fmt: DocumentFormat | None,
    ) -> CanonicalIntermediateRepresentation:
        actual_fmt = fmt
        if actual_fmt is None:
            from pathlib import Path as P
            actual_fmt = self._processor._detect_format(P(filename)) if hasattr(
                self._processor, '_detect_format'
            ) else DocumentFormat.TXT

        dummy = RawDocument(
            id="_cache_",
            filename=filename,
            format=actual_fmt,
            content=content,
            size_bytes=len(content),
            checksum_sha256=hashlib.sha256(content).hexdigest(),
            upload_timestamp=datetime.now(timezone.utc),
        )

        cached = self._cache.get(dummy)
        if cached is not None:
            return cached

        result = self._processor.process_bytes(content, filename, fmt=actual_fmt)
        self._cache.set(dummy, result)
        return result

    def invalidate(self, content: bytes) -> None:
        dummy = RawDocument(
            id="_cache_",
            filename="_invalidate_",
            format=DocumentFormat.TXT,
            content=content,
            size_bytes=len(content),
            checksum_sha256=hashlib.sha256(content).hexdigest(),
            upload_timestamp=datetime.now(timezone.utc),
        )
        self._cache.invalidate(dummy)

    @property
    def processor(self):
        return self._processor

    @property
    def cache(self) -> DocumentCache:
        return self._cache
