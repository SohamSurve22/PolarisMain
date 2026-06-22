import json
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from .clauses import ClauseDocument
from .cleaning import CleanedDocument
from .document import RawDocument
from .errors import PipelineError
from .extraction import ExtractedDocument
from .statistics import DocumentStatistics
from .structure import StructuredDocument


class StageTiming(BaseModel):
    stage_name: str
    status: Literal["success", "degraded", "skipped", "failed"]
    duration_ms: float = Field(ge=0.0)
    error: PipelineError | None = None


class ValidationInfo(BaseModel):
    overall_status: str = "pending"
    stages_valid: list[str] = Field(default_factory=list)
    stages_failed: list[str] = Field(default_factory=list)
    stages_skipped: list[str] = Field(default_factory=list)
    is_complete: bool = False
    is_degraded: bool = False
    warnings_count: int = Field(ge=0)


class IRMetadata(BaseModel):
    pipeline_version: str
    correlation_id: str
    processing_status: str = "pending"
    stages: list[StageTiming] = Field(default_factory=list)
    total_duration_ms: float = Field(default=0.0, ge=0.0)
    warnings: list[str] = Field(default_factory=list)
    errors: list[PipelineError] = Field(default_factory=list)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    statistics: DocumentStatistics | None = None
    validation: ValidationInfo | None = None


class CanonicalIntermediateRepresentation(BaseModel):
    raw_document: RawDocument
    extracted_document: ExtractedDocument | None = None
    cleaned_document: CleanedDocument | None = None
    structured_document: StructuredDocument | None = None
    clause_document: ClauseDocument | None = None
    metadata: IRMetadata

    model_config = {"frozen": True}

    def to_json(self, *, indent: int = 2, exclude_raw_content: bool = False) -> str:
        import base64
        exclude = set()
        if exclude_raw_content:
            exclude.add("raw_document")
        raw = self.model_dump(mode="python", exclude=exclude)
        if not exclude_raw_content:
            raw["raw_document"]["content"] = base64.b64encode(
                raw["raw_document"]["content"]
            ).decode("ascii")
        return json.dumps(raw, indent=indent, ensure_ascii=False, default=str)

    @classmethod
    def from_json(cls, data: str) -> "CanonicalIntermediateRepresentation":
        import base64
        parsed = json.loads(data)
        if "raw_document" in parsed and isinstance(parsed["raw_document"].get("content"), str):
            parsed["raw_document"]["content"] = base64.b64decode(
                parsed["raw_document"]["content"]
            )
        return cls.model_validate(parsed)

    def export_json(self, filepath: str, *, indent: int = 2, exclude_raw_content: bool = False) -> None:
        import pathlib
        json_str = self.to_json(indent=indent, exclude_raw_content=exclude_raw_content)
        pathlib.Path(filepath).write_text(json_str, encoding="utf-8")

    @classmethod
    def import_json(cls, filepath: str) -> "CanonicalIntermediateRepresentation":
        import pathlib
        data = pathlib.Path(filepath).read_text(encoding="utf-8")
        return cls.from_json(data)

    @property
    def statistics(self) -> DocumentStatistics | None:
        return self.metadata.statistics

    @property
    def validation(self) -> ValidationInfo | None:
        return self.metadata.validation
