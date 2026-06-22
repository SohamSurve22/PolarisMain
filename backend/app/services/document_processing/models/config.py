import json
import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator

from .enums import CleaningOperation, DocumentFormat


class ExtractorConfig(BaseModel):
    pdf_strategy: str = "pymupdf"
    pdf_fallback_strategy: str = "pdfplumber"
    html_parser: str = "beautifulsoup"
    extract_tables: bool = False
    extract_images: bool = False


class CleanerConfig(BaseModel):
    enabled_operations: list[CleaningOperation] = Field(default_factory=lambda: [op for op in CleaningOperation])
    max_consecutive_blank_lines: int = Field(default=2, ge=1)
    min_heading_length: int = Field(default=2, ge=1)
    header_footer_min_pages: int = Field(default=3, ge=2)
    header_footer_match_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    merge_hyphenated_words: bool = True
    merge_continuation_lines: bool = True
    preserve_list_indentation: bool = True


class StructureDetectorConfig(BaseModel):
    heading_patterns: list[str] = Field(default_factory=list)
    enable_toc_detection: bool = True
    min_heading_confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class ClauseExtractorConfig(BaseModel):
    strategy: str = "hierarchical"
    min_clause_confidence: float = Field(default=0.3, ge=0.0, le=1.0)
    max_clause_depth: int = Field(default=10, ge=1)


class PipelineConfig(BaseModel):
    version: str = "1.0.0"
    max_file_size_bytes: int = Field(default=26214400, ge=1)
    max_page_count: int = Field(default=200, ge=1)
    allowed_formats: list[DocumentFormat] = Field(default_factory=lambda: [f for f in DocumentFormat])
    supported_languages: list[str] = Field(default_factory=lambda: ["en"])
    enable_degraded_mode: bool = True
    extractor: ExtractorConfig = Field(default_factory=ExtractorConfig)
    cleaner: CleanerConfig = Field(default_factory=CleanerConfig)
    structure_detector: StructureDetectorConfig = Field(default_factory=StructureDetectorConfig)
    clause_extractor: ClauseExtractorConfig = Field(default_factory=ClauseExtractorConfig)

    @field_validator("max_file_size_bytes")
    @classmethod
    def validate_file_size(cls, v: int) -> int:
        if v > 524288000:
            raise ValueError("max_file_size_bytes must not exceed 500MB")
        return v

    @classmethod
    def from_json_file(cls, path: str | Path) -> "PipelineConfig":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(**data)

    @classmethod
    def from_json_string(cls, json_str: str) -> "PipelineConfig":
        data = json.loads(json_str)
        return cls(**data)

    @classmethod
    def from_env(cls, prefix: str = "POLARIS_PIPELINE_") -> "PipelineConfig":
        env_map: dict[str, Any] = {}
        for key, val in os.environ.items():
            if not key.startswith(prefix):
                continue
            config_key = key[len(prefix):].lower()
            parts = config_key.split("__", 1)
            if len(parts) == 2:
                section, field = parts
                if section not in env_map:
                    env_map[section] = {}
                env_map[section][field] = cls._coerce_env(val)
            else:
                env_map[config_key] = cls._coerce_env(val)
        return cls(**env_map)

    @staticmethod
    def _coerce_env(val: str) -> Any:
        lower = val.lower()
        if lower in ("true", "1", "yes"):
            return True
        if lower in ("false", "0", "no"):
            return False
        if lower == "null":
            return None
        try:
            return int(val)
        except ValueError:
            pass
        try:
            return float(val)
        except ValueError:
            pass
        return val

    model_config = {"frozen": True, "extra": "forbid"}
