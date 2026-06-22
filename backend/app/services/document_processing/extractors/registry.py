from ..models import DocumentFormat
from ..interfaces import BaseExtractor
from .pdf_extractor import PDFExtractor
from .docx_extractor import DOCXExtractor
from .txt_extractor import TxtExtractor
from .html_extractor import HtmlExtractor


class ExtractorRegistry:
    _extractors: dict[DocumentFormat, BaseExtractor] | None = None

    @classmethod
    def _build_defaults(cls) -> dict[DocumentFormat, BaseExtractor]:
        return {
            DocumentFormat.PDF: PDFExtractor(),
            DocumentFormat.DOCX: DOCXExtractor(),
            DocumentFormat.TXT: TxtExtractor(),
            DocumentFormat.HTML: HtmlExtractor(),
        }

    @classmethod
    def get_extractor(cls, format: DocumentFormat) -> BaseExtractor:
        if cls._extractors is None:
            cls._extractors = cls._build_defaults()
        extractor = cls._extractors.get(format)
        if extractor is None:
            raise ValueError(
                f"No extractor registered for format '{format.value}'. "
                f"Available formats: {[f.value for f in cls._extractors]}"
            )
        return extractor

    @classmethod
    def register(cls, format: DocumentFormat, extractor: BaseExtractor) -> None:
        if cls._extractors is None:
            cls._extractors = cls._build_defaults()
        cls._extractors[format] = extractor

    @classmethod
    def supported_formats(cls) -> list[DocumentFormat]:
        if cls._extractors is None:
            cls._extractors = cls._build_defaults()
        return list(cls._extractors.keys())

    @classmethod
    def reset(cls) -> None:
        cls._extractors = None
