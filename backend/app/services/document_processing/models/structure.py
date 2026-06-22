from typing import Any

from pydantic import BaseModel, Field

from .enums import StructuralElementType


class BoundingBox(BaseModel):
    page: int = Field(ge=1)
    x0: float
    y0: float
    x1: float
    y1: float

    model_config = {"frozen": True}


class StructuralElement(BaseModel):
    element_id: str
    type: StructuralElementType
    text: str
    level: int = Field(ge=0)
    parent_id: str | None = None
    child_ids: list[str] = Field(default_factory=list)
    bounding_box: BoundingBox | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class TableOfContentsEntry(BaseModel):
    title: str
    level: int = Field(ge=0)
    page_number: int | None = Field(default=None, ge=1)
    target_element_id: str | None = None


class TableOfContents(BaseModel):
    entries: list[TableOfContentsEntry] = Field(default_factory=list)


class DocumentStructure(BaseModel):
    elements: dict[str, StructuralElement] = Field(default_factory=dict)
    root_element_ids: list[str] = Field(default_factory=list)
    toc: TableOfContents | None = None
    detection_strategy: str = "unknown"


class StructuredDocument(BaseModel):
    cleaned_id: str
    structure: DocumentStructure

    model_config = {"frozen": True}
