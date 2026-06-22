from __future__ import annotations

import pytest

from backend.app.services.document_processing.models import (
    CleanedDocument,
    CleaningStats,
    DocumentFormat,
    ExtractedDocument,
    ExtractedMetadata,
    PageInfo,
    StructureDetectorConfig,
)


@pytest.fixture
def extracted_pdf_legal() -> ExtractedDocument:
    text = (
        "PRIVACY POLICY\n"
        "\n"
        "TABLE OF CONTENTS\n"
        "1. Introduction .................................. 3\n"
        "2. Data Collection .............................. 4\n"
        "3. Purpose of Processing ........................ 5\n"
        "\n"
        "1. Introduction\n"
        "This Privacy Policy describes how we collect, use, and process your personal data.\n"
        "We are committed to protecting your privacy and ensuring transparency.\n"
        "\n"
        "1.1 Information We Collect\n"
        "We collect the following categories of personal data:\n"
        "name, address, email address, phone number, and usage data.\n"
        "\n"
        "1.1.1 Account Information\n"
        "When you create an account, we collect your name and email.\n"
        "\n"
        "1.1.2 Usage Data\n"
        "We automatically collect information about how you use our platform.\n"
        "\n"
        "2. Data Collection\n"
        "We collect data through direct interactions, automated technologies, and third parties.\n"
        "\n"
        "3. Purpose of Processing\n"
        "Your data is processed for service delivery, compliance, and fraud prevention.\n"
        "\n"
        "Article 4: Legal Basis\n"
        "Processing is based on consent, contract performance, and legal obligations.\n"
        "\n"
        "Section 4.1: Consent\n"
        "We obtain your consent before processing your personal data.\n"
        "\n"
        "Section 4.2: Contract Performance\n"
        "Processing is necessary for the performance of a contract with you.\n"
        "\n"
        "Schedule A: Definitions\n"
        "Capitalized terms used in this Policy have the meanings set forth below.\n"
        "\n"
        "I. General Provisions\n"
        "These General Provisions apply to all sections of this Policy.\n"
    )
    return ExtractedDocument(
        raw_id="test-legal-001",
        format=DocumentFormat.TXT,
        text=text,
        pages=[],
        metadata=ExtractedMetadata(
            word_count=len(text.split()),
            char_count=len(text),
            page_count=1,
            extraction_strategy="test",
        ),
    )


@pytest.fixture
def cleaned_legal(extracted_pdf_legal) -> CleanedDocument:
    doc = extracted_pdf_legal
    return CleanedDocument(
        extracted_id=doc.raw_id,
        text=doc.text,
        stats=CleaningStats(
            original_char_count=doc.metadata.char_count,
            cleaned_char_count=doc.metadata.char_count,
            removed_char_count=0,
        ),
    )


@pytest.fixture
def cleaned_empty() -> CleanedDocument:
    return CleanedDocument(
        extracted_id="test-empty",
        text="",
        stats=CleaningStats(
            original_char_count=0,
            cleaned_char_count=0,
            removed_char_count=0,
        ),
    )


@pytest.fixture
def cleaned_flat() -> CleanedDocument:
    text = (
        "This is a plain document with no headings.\n"
        "It contains only paragraph text.\n"
        "\n"
        "There is a second paragraph here.\n"
        "And a third one too.\n"
    )
    return CleanedDocument(
        extracted_id="test-flat",
        text=text,
        stats=CleaningStats(
            original_char_count=len(text),
            cleaned_char_count=len(text),
            removed_char_count=0,
        ),
    )


@pytest.fixture
def cleaned_toc() -> CleanedDocument:
    text = (
        "TABLE OF CONTENTS\n"
        "1. Introduction ............. 1\n"
        "2. Scope .................... 2\n"
        "3. Definitions ............. 3\n"
        "4. Data Processing ......... 4\n"
        "5. Data Retention .......... 5\n"
        "\n"
        "1. Introduction\n"
        "This is the introduction.\n"
        "\n"
        "2. Scope\n"
        "This document applies to all users.\n"
    )
    return CleanedDocument(
        extracted_id="test-toc",
        text=text,
        stats=CleaningStats(
            original_char_count=len(text),
            cleaned_char_count=len(text),
            removed_char_count=0,
        ),
    )


@pytest.fixture
def default_config() -> StructureDetectorConfig:
    return StructureDetectorConfig()
