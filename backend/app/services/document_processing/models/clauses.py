from typing import Any

from pydantic import BaseModel, Field, field_validator


class Clause(BaseModel):
    clause_id: str
    clause_number: str | None = None
    heading: str | None = None
    body: str
    level: int = Field(ge=0)
    parent_clause_id: str | None = None
    child_clause_ids: list[str] = Field(default_factory=list)
    structural_path: list[str] = Field(default_factory=list)
    page_range: tuple[int, int] | None = Field(default=None)
    element_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("page_range")
    @classmethod
    def valid_page_range(cls, v: tuple[int, int] | None) -> tuple[int, int] | None:
        if v is not None:
            start, end = v
            if start < 1:
                raise ValueError("Page range start must be >= 1")
            if end < start:
                raise ValueError("Page range end must be >= start")
        return v


class ClauseDocument(BaseModel):
    structured_id: str
    root_clause_ids: list[str] = Field(default_factory=list)
    clauses: dict[str, Clause] = Field(default_factory=dict)
    extraction_strategy: str = "unknown"

    @property
    def clause_count(self) -> int:
        return len(self.clauses)

    model_config = {"frozen": True}
