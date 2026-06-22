from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from ...models import CleaningOperation, PageInfo


@dataclass
class CleansedResult:
    text: str
    was_modified: bool = False
    stats: dict[str, int] = field(default_factory=dict)


class CleaningStrategy(ABC):
    @property
    @abstractmethod
    def operation(self) -> CleaningOperation:
        ...

    @abstractmethod
    def clean(self, text: str, pages: list[PageInfo] | None = None) -> CleansedResult:
        ...
