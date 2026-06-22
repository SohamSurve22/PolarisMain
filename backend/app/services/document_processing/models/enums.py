from enum import Enum


class DocumentFormat(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    HTML = "html"


class DocumentType(str, Enum):
    PRIVACY_POLICY = "privacy_policy"
    TERMS_AND_CONDITIONS = "terms_and_conditions"
    COOKIE_POLICY = "cookie_policy"
    DATA_RETENTION_POLICY = "data_retention_policy"
    INFORMATION_SECURITY_POLICY = "information_security_policy"
    USER_AGREEMENT = "user_agreement"


class ProcessingStatus(str, Enum):
    PENDING = "pending"
    EXTRACTING = "extracting"
    CLEANING = "cleaning"
    DETECTING_STRUCTURE = "detecting_structure"
    EXTRACTING_CLAUSES = "extracting_clauses"
    COMPLETE = "complete"
    FAILED = "failed"
    DEGRADED = "degraded"


class CleaningOperation(str, Enum):
    NORMALIZE_WHITESPACE = "normalize_whitespace"
    NORMALIZE_UNICODE = "normalize_unicode"
    FIX_LIGATURES = "fix_ligatures"
    REMOVE_HEADERS = "remove_headers"
    REMOVE_FOOTERS = "remove_footers"
    REMOVE_PAGE_NUMBERS = "remove_page_numbers"
    REMOVE_NON_TEXTUAL_ARTIFACTS = "remove_non_textual_artifacts"
    COLLAPSE_BLANK_LINES = "collapse_blank_lines"
    STRIP_HTML_TAGS = "strip_html_tags"
    NORMALIZE_QUOTES = "normalize_quotes"
    MERGE_LINES = "merge_lines"
    RECONSTRUCT_PARAGRAPHS = "reconstruct_paragraphs"


class StructuralElementType(str, Enum):
    DOCUMENT_TITLE = "document_title"
    HEADING = "heading"
    SUBHEADING = "subheading"
    PARAGRAPH = "paragraph"
    LIST_ITEM = "list_item"
    TABLE = "table"
    HEADER = "header"
    FOOTER = "footer"
    PAGE_NUMBER = "page_number"
    CLAUSE_NUMBER = "clause_number"
    DEFINITION = "definition"
    SCHEDULE = "schedule"
    ANNEXURE = "annexure"
