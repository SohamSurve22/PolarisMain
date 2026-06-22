import pytest

from backend.app.services.document_processing.models import (
    DocumentFormat,
    ExtractedDocument,
    ExtractedMetadata,
    PageInfo,
)


@pytest.fixture
def extracted_pdf() -> ExtractedDocument:
    text = (
        "Privacy Policy\n\n"
        "1. Introduction\n"
        "This Privacy Policy describes how we collect, use, and process your personal data.\n\n"
        "2. Data Collection\n"
        "We collect the following categories of personal data: name, address, email, phone.\n\n"
        "3. Purpose of Processing\n"
        "Your data is processed for service delivery, compliance, and fraud prevention.\n\n"
        "4. Data Retention\n"
        "We retain personal data as long as necessary to fulfill the purposes described.\n\n"
        "5. Your Rights\n"
        "Under the Digital Personal Data Protection Act 2023, you have the right to access and correction.\n"
    )
    return ExtractedDocument(
        raw_id="test-pdf-001",
        format=DocumentFormat.PDF,
        text=text,
        pages=[
            PageInfo(page_number=1, text=text, char_count=len(text)),
        ],
        metadata=ExtractedMetadata(
            word_count=len(text.split()), char_count=len(text), page_count=1,
            extraction_strategy="pymupdf",
        ),
    )


@pytest.fixture
def simple_text() -> str:
    return (
        "This is a test document.\n"
        "It has multiple lines.\n"
        "  \n"
        "And paragraphs separated by blank lines.\n"
        "\n\n\n"
        "Too many blank lines here.\n"
    )


@pytest.fixture
def ligature_text() -> str:
    return "This ﬁle contains ﬁ ligatures like ﬁ, ﬂ, ﬃ.\n"


@pytest.fixture
def smart_quote_text() -> str:
    return 'He said \u201cHello world\u201d and left.\n'


@pytest.fixture
def hyphenated_text() -> str:
    return (
        "This is a long word that is hyphen-\n"
        "ated across two lines.\n"
        "Another comp-\n"
        "liance issue arises here.\n"
    )


@pytest.fixture
def continuation_text() -> str:
    return (
        "The Data Protection Officer is responsible for\n"
        "overseeing compliance with this policy and\n"
        "any related data protection laws.\n"
    )
