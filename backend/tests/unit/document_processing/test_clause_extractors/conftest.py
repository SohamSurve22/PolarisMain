import pytest

from backend.app.services.document_processing.models import (
    CleanedDocument,
    CleaningStats,
    DocumentStructure,
    StructuralElement,
    StructuralElementType,
    StructuredDocument,
)
from backend.app.services.document_processing.structure_detectors import StructureDetector


@pytest.fixture
def cleaned_doc() -> CleanedDocument:
    text = (
        "1. Introduction\n"
        "This Privacy Policy describes how we collect, use, and process your personal data.\n"
        "\n"
        "2. Data Collection\n"
        "We collect the following categories of personal data:\n"
        "(a) Name and contact information\n"
        "(b) Financial information\n"
        "(c) Usage data\n"
        "\n"
        "3. Rights\n"
        "You have the right to access your data. You have the right to correct your data. "
        "You have the right to erasure.\n"
    )
    return CleanedDocument(
        extracted_id="test-cl-001",
        text=text,
        stats=CleaningStats(
            original_char_count=len(text),
            cleaned_char_count=len(text),
            removed_char_count=0,
        ),
    )


@pytest.fixture
def structured_doc(cleaned_doc) -> StructuredDocument:
    text = cleaned_doc.text
    lines = text.split("\n")
    offsets = []
    o = 0
    for ln in lines:
        offsets.append(o)
        o += len(ln) + 1

    h1 = StructuralElement(
        element_id="h_1",
        type=StructuralElementType.HEADING,
        text="1. Introduction",
        level=1,
        metadata={"char_start": offsets[0], "char_end": offsets[0] + len(lines[0]), "line_number": 1, "confidence": 0.95, "pattern_type": "decimal_1"},
    )
    p1 = StructuralElement(
        element_id="p_1",
        type=StructuralElementType.PARAGRAPH,
        text="This Privacy Policy describes how we collect, use, and process your personal data.",
        level=0,
        parent_id="h_1",
        metadata={"char_start": offsets[1], "char_end": offsets[1] + len(lines[1]), "line_number": 2},
    )
    h2 = StructuralElement(
        element_id="h_2",
        type=StructuralElementType.HEADING,
        text="2. Data Collection",
        level=1,
        metadata={"char_start": offsets[3], "char_end": offsets[3] + len(lines[3]), "line_number": 4, "confidence": 0.95, "pattern_type": "decimal_1"},
    )
    p2 = StructuralElement(
        element_id="p_2",
        type=StructuralElementType.PARAGRAPH,
        text="We collect the following categories of personal data:\n(a) Name and contact information\n(b) Financial information\n(c) Usage data",
        level=0,
        parent_id="h_2",
        metadata={"char_start": offsets[4], "char_end": offsets[4] + len(lines[4]) + 1 + len(lines[5]) + 1 + len(lines[6]) + 1 + len(lines[7]), "line_number": 5},
    )
    h3 = StructuralElement(
        element_id="h_3",
        type=StructuralElementType.HEADING,
        text="3. Rights",
        level=1,
        metadata={"char_start": offsets[8], "char_end": offsets[8] + len(lines[8]), "line_number": 9, "confidence": 0.95, "pattern_type": "decimal_1"},
    )
    p3 = StructuralElement(
        element_id="p_3",
        type=StructuralElementType.PARAGRAPH,
        text="You have the right to access your data. You have the right to correct your data. You have the right to erasure.",
        level=0,
        parent_id="h_3",
        metadata={"char_start": offsets[9], "char_end": offsets[9] + len(lines[9]), "line_number": 10},
    )

    h1.child_ids = ["p_1"]
    h2.child_ids = ["p_2"]
    h3.child_ids = ["p_3"]

    structure = DocumentStructure(
        elements={"h_1": h1, "p_1": p1, "h_2": h2, "p_2": p2, "h_3": h3, "p_3": p3},
        root_element_ids=["h_1", "h_2", "h_3"],
        detection_strategy="hierarchy_building",
    )
    return StructuredDocument(cleaned_id=cleaned_doc.extracted_id, structure=structure)


@pytest.fixture
def structured_doc_nested() -> StructuredDocument:
    text = (
        "1. General\n"
        "These are general terms.\n"
        "1.1 Scope\n"
        "This applies to:\n"
        "(a) Users\n"
        "(b) Partners\n"
        "1.2 Definitions\n"
        "Key terms are defined below.\n"
    )
    lines = text.split("\n")
    offsets = []
    o = 0
    for ln in lines:
        offsets.append(o)
        o += len(ln) + 1

    h1 = StructuralElement(element_id="h_1", type=StructuralElementType.HEADING, text="1. General", level=1,
        metadata={"char_start": offsets[0], "char_end": offsets[0] + len(lines[0]), "line_number": 1, "confidence": 0.95, "pattern_type": "decimal_1"})
    p1 = StructuralElement(element_id="p_1", type=StructuralElementType.PARAGRAPH, text="These are general terms.", level=0, parent_id="h_1",
        metadata={"char_start": offsets[1], "char_end": offsets[1] + len(lines[1]), "line_number": 2})
    h11 = StructuralElement(element_id="h_1_1", type=StructuralElementType.SUBHEADING, text="1.1 Scope", level=2, parent_id="h_1",
        metadata={"char_start": offsets[2], "char_end": offsets[2] + len(lines[2]), "line_number": 3, "confidence": 0.95, "pattern_type": "decimal_2"})
    p2_text = "This applies to:\n(a) Users\n(b) Partners"
    p2 = StructuralElement(element_id="p_2", type=StructuralElementType.PARAGRAPH, text=p2_text, level=0, parent_id="h_1_1",
        metadata={"char_start": offsets[3], "char_end": offsets[3] + len(lines[3]) + 1 + len(lines[4]) + 1 + len(lines[5]), "line_number": 4})
    h12 = StructuralElement(element_id="h_1_2", type=StructuralElementType.SUBHEADING, text="1.2 Definitions", level=2, parent_id="h_1",
        metadata={"char_start": offsets[6], "char_end": offsets[6] + len(lines[6]), "line_number": 7, "confidence": 0.95, "pattern_type": "decimal_2"})
    p3 = StructuralElement(element_id="p_3", type=StructuralElementType.PARAGRAPH, text="Key terms are defined below.", level=0, parent_id="h_1_2",
        metadata={"char_start": offsets[7], "char_end": offsets[7] + len(lines[7]), "line_number": 8})

    h1.child_ids = ["p_1", "h_1_1", "h_1_2"]
    h11.child_ids = ["p_2"]
    h12.child_ids = ["p_3"]

    structure = DocumentStructure(
        elements={"h_1": h1, "p_1": p1, "h_1_1": h11, "p_2": p2, "h_1_2": h12, "p_3": p3},
        root_element_ids=["h_1"],
        detection_strategy="hierarchy_building",
    )
    return StructuredDocument(cleaned_id="test-nested", structure=structure)


@pytest.fixture
def cleaned_nested(structured_doc_nested) -> CleanedDocument:
    text = (
        "1. General\n"
        "These are general terms.\n"
        "1.1 Scope\n"
        "This applies to:\n"
        "(a) Users\n"
        "(b) Partners\n"
        "1.2 Definitions\n"
        "Key terms are defined below.\n"
    )
    return CleanedDocument(
        extracted_id="test-nested",
        text=text,
        stats=CleaningStats(original_char_count=len(text), cleaned_char_count=len(text), removed_char_count=0),
    )


@pytest.fixture
def empty_cleaned() -> CleanedDocument:
    return CleanedDocument(
        extracted_id="test-empty",
        text="",
        stats=CleaningStats(original_char_count=0, cleaned_char_count=0, removed_char_count=0),
    )


@pytest.fixture
def empty_structured() -> StructuredDocument:
    return StructuredDocument(
        cleaned_id="test-empty",
        structure=DocumentStructure(detection_strategy="empty"),
    )
