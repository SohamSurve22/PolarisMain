from pydantic import BaseModel, Field, model_validator

from .enums import CleaningOperation


class CleaningStats(BaseModel):
    original_char_count: int = Field(ge=0)
    cleaned_char_count: int = Field(ge=0)
    removed_char_count: int = Field(ge=0)
    operations_applied: list[CleaningOperation] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_counts(self) -> "CleaningStats":
        expected = self.original_char_count - self.cleaned_char_count
        if self.removed_char_count != max(0, expected):
            raise ValueError(
                f"removed_char_count ({self.removed_char_count}) must equal "
                f"max(0, original - cleaned) = max(0, {expected}) = {max(0, expected)}"
            )
        return self


class CleanedDocument(BaseModel):
    extracted_id: str
    text: str
    stats: CleaningStats
    warnings: list[str] = Field(default_factory=list)

    model_config = {"frozen": True}
