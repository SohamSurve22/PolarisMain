from __future__ import annotations

import os
from enum import Enum
from pathlib import Path
from typing import Any

from .models import PipelineConfig


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TEST = "test"


_ENV_PROFILES: dict[Environment, dict[str, Any]] = {
    Environment.DEVELOPMENT: {
        "enable_degraded_mode": True,
        "extractor": {"pdf_strategy": "pymupdf", "pdf_fallback_strategy": "pdfplumber"},
    },
    Environment.STAGING: {
        "enable_degraded_mode": True,
        "extractor": {"pdf_strategy": "pymupdf", "pdf_fallback_strategy": "pdfplumber"},
    },
    Environment.PRODUCTION: {
        "enable_degraded_mode": False,
        "extractor": {"pdf_strategy": "pymupdf", "pdf_fallback_strategy": "pdfplumber"},
    },
    Environment.TEST: {
        "enable_degraded_mode": True,
    },
}


class Settings:
    def __init__(
        self,
        env: Environment | str | None = None,
        config_file: str | Path | None = None,
        env_prefix: str = "POLARIS_",
    ):
        self._env_prefix = env_prefix
        raw_env = os.environ.get(f"{env_prefix}ENV", "development").lower()
        self._environment = Environment(env) if env else Environment(raw_env)

        self._pipeline_config = self._build_pipeline_config(config_file)

    def _build_pipeline_config(self, config_file: str | Path | None) -> PipelineConfig:
        if config_file:
            return PipelineConfig.from_json_file(config_file)

        env_overrides: dict[str, Any] = {}

        profile = _ENV_PROFILES.get(self._environment, {})
        self._deep_merge(env_overrides, profile)

        env_config = PipelineConfig.from_env(prefix=f"{self._env_prefix}PIPELINE_")
        self._deep_merge(env_overrides, env_config.model_dump())

        return PipelineConfig(**env_overrides)

    @property
    def environment(self) -> Environment:
        return self._environment

    @property
    def pipeline_config(self) -> PipelineConfig:
        return self._pipeline_config

    @property
    def cache_dir(self) -> Path:
        default = Path.home() / ".polaris" / "cache"
        return Path(os.environ.get(f"{self._env_prefix}CACHE_DIR", str(default)))

    @property
    def cache_ttl_seconds(self) -> int:
        return int(os.environ.get(f"{self._env_prefix}CACHE_TTL", "3600"))

    @property
    def max_workers(self) -> int:
        return int(os.environ.get(f"{self._env_prefix}MAX_WORKERS", "4"))

    @property
    def log_level(self) -> str:
        return os.environ.get(f"{self._env_prefix}LOG_LEVEL", "INFO").upper()

    @property
    def log_json(self) -> bool:
        return os.environ.get(f"{self._env_prefix}LOG_JSON", "false").lower() in ("true", "1", "yes")

    @property
    def profiling_enabled(self) -> bool:
        return os.environ.get(f"{self._env_prefix}PROFILING_ENABLED", "false").lower() in ("true", "1", "yes")

    @property
    def max_file_size_bytes(self) -> int:
        return self._pipeline_config.max_file_size_bytes

    @property
    def max_page_count(self) -> int:
        return self._pipeline_config.max_page_count

    @staticmethod
    def _deep_merge(base: dict, override: dict) -> None:
        for key, val in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(val, dict):
                Settings._deep_merge(base[key], val)
            else:
                base[key] = val

    @classmethod
    def from_env(cls) -> "Settings":
        return cls()

    def to_dict(self) -> dict[str, Any]:
        return {
            "environment": self.environment.value,
            "cache_dir": str(self.cache_dir),
            "cache_ttl_seconds": self.cache_ttl_seconds,
            "max_workers": self.max_workers,
            "log_level": self.log_level,
            "log_json": self.log_json,
            "profiling_enabled": self.profiling_enabled,
            "max_file_size_bytes": self.max_file_size_bytes,
            "max_page_count": self.max_page_count,
        }
