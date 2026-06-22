import hashlib
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

from backend.app.services.document_processing.models import (
    CanonicalIntermediateRepresentation,
    ClauseDocument,
    CleanedDocument,
    CleaningOperation,
    DocumentFormat,
    DocumentStatistics,
    PipelineConfig,
    RawDocument,
    StructuredDocument,
    ValidationInfo,
)
from backend.app.services.document_processing.pipeline import DocumentPipeline


def _make_raw_document(content: bytes, filename: str, fmt: DocumentFormat) -> RawDocument:
    return RawDocument(
        id=f"test-{hashlib.md5(content).hexdigest()[:12]}",
        filename=filename,
        format=fmt,
        content=content,
        size_bytes=len(content),
        checksum_sha256=hashlib.sha256(content).hexdigest(),
        upload_timestamp=datetime.now(timezone.utc),
    )


class TestDocumentPipeline:
    def test_pipeline_default_config(self):
        pipeline = DocumentPipeline()
        assert pipeline._config.version == "1.0.0"
        assert pipeline._config.enable_degraded_mode is True

    def test_pipeline_custom_config(self):
        config = PipelineConfig(version="2.0.0", enable_degraded_mode=False)
        pipeline = DocumentPipeline(config=config)
        assert pipeline._config.version == "2.0.0"
        assert pipeline._config.enable_degraded_mode is False

    def test_full_pipeline_pdf(self, sample_pdf_content):
        doc = _make_raw_document(sample_pdf_content, "test.pdf", DocumentFormat.PDF)
        pipeline = DocumentPipeline()
        result = pipeline.run(doc)

        assert isinstance(result, CanonicalIntermediateRepresentation)
        assert result.metadata.processing_status == "complete"
        assert result.metadata.correlation_id is not None
        assert result.metadata.pipeline_version == "1.0.0"
        assert result.metadata.total_duration_ms > 0
        assert result.metadata.started_at is not None
        assert result.metadata.completed_at is not None

        assert result.extracted_document is not None
        assert result.cleaned_document is not None
        assert result.structured_document is not None
        assert result.clause_document is not None

        stage_names = [s.stage_name for s in result.metadata.stages]
        assert stage_names == ["extract", "clean", "structure_detect", "clause_extract"]
        assert all(s.status == "success" for s in result.metadata.stages)

    def test_full_pipeline_docx(self, sample_docx_content):
        doc = _make_raw_document(sample_docx_content, "test.docx", DocumentFormat.DOCX)
        pipeline = DocumentPipeline()
        result = pipeline.run(doc)

        assert result.metadata.processing_status == "complete"
        assert result.extracted_document is not None
        assert result.cleaned_document is not None
        assert result.structured_document is not None
        assert result.clause_document is not None

    def test_full_pipeline_txt(self, sample_txt_content):
        doc = _make_raw_document(sample_txt_content, "test.txt", DocumentFormat.TXT)
        pipeline = DocumentPipeline()
        result = pipeline.run(doc)

        assert result.metadata.processing_status == "complete"
        assert result.extracted_document is not None
        assert result.cleaned_document is not None
        assert result.structured_document is not None
        assert result.clause_document is not None

    def test_full_pipeline_html(self, sample_html_content):
        doc = _make_raw_document(sample_html_content, "test.html", DocumentFormat.HTML)
        pipeline = DocumentPipeline()
        result = pipeline.run(doc)

        assert result.metadata.processing_status == "complete"
        assert result.extracted_document is not None
        assert result.cleaned_document is not None
        assert result.structured_document is not None
        assert result.clause_document is not None

    def test_stats_populated(self, sample_pdf_content):
        doc = _make_raw_document(sample_pdf_content, "test.pdf", DocumentFormat.PDF)
        pipeline = DocumentPipeline()
        result = pipeline.run(doc)

        stats = result.metadata.statistics
        assert stats is not None
        assert stats.format == DocumentFormat.PDF
        assert stats.filename == "test.pdf"
        assert stats.file_size_bytes > 0
        assert len(stats.checksum_sha256) == 64
        assert stats.word_count > 0
        assert stats.char_count > 0
        assert stats.page_count is not None
        assert stats.cleaned_char_count is not None
        assert stats.structural_element_count > 0
        assert stats.clause_count > 0

    def test_stats_without_cleaning(self, sample_pdf_content):
        config = PipelineConfig(enable_degraded_mode=True)
        config.cleaner.enabled_operations = []
        doc = _make_raw_document(sample_pdf_content, "test.pdf", DocumentFormat.PDF)
        pipeline = DocumentPipeline(config=config)
        result = pipeline.run(doc)

        stats = result.metadata.statistics
        assert stats is not None
        assert stats.cleaning_operations_applied == []

    def test_validation_info_populated(self, sample_pdf_content):
        doc = _make_raw_document(sample_pdf_content, "test.pdf", DocumentFormat.PDF)
        pipeline = DocumentPipeline()
        result = pipeline.run(doc)

        validation = result.metadata.validation
        assert validation is not None
        assert validation.overall_status == "complete"
        assert validation.is_complete is True
        assert validation.is_degraded is False
        assert len(validation.stages_valid) == 4
        assert len(validation.stages_failed) == 0
        assert len(validation.stages_skipped) == 0
        assert validation.warnings_count >= 0

    def test_extraction_failure_stages_skipped(self, raw_empty):
        pipeline = DocumentPipeline()
        result = pipeline.run(raw_empty)

        assert result.metadata.processing_status == "failed"
        assert result.extracted_document is None
        assert result.cleaned_document is None
        assert result.structured_document is None
        assert result.clause_document is None

        stage_map = {s.stage_name: s.status for s in result.metadata.stages}
        assert stage_map["extract"] == "failed"
        assert stage_map["clean"] == "skipped"
        assert stage_map["structure_detect"] == "skipped"
        assert stage_map["clause_extract"] == "skipped"

    def test_corrupted_pdf_fails_extraction(self, raw_corrupted_pdf):
        pipeline = DocumentPipeline()
        result = pipeline.run(raw_corrupted_pdf)

        assert result.metadata.processing_status == "failed"
        stage_map = {s.stage_name: s.status for s in result.metadata.stages}
        assert stage_map["extract"] == "failed"

    def test_ir_metadata_fields(self, sample_pdf_content):
        doc = _make_raw_document(sample_pdf_content, "test.pdf", DocumentFormat.PDF)
        pipeline = DocumentPipeline()
        result = pipeline.run(doc)

        meta = result.metadata
        assert meta.pipeline_version == "1.0.0"
        assert len(meta.correlation_id) > 0
        assert meta.processing_status == "complete"
        assert len(meta.stages) == 4
        assert meta.total_duration_ms > 0
        assert isinstance(meta.started_at, datetime)
        assert isinstance(meta.completed_at, datetime)

    def test_stage_timings_recorded(self, sample_pdf_content):
        doc = _make_raw_document(sample_pdf_content, "test.pdf", DocumentFormat.PDF)
        pipeline = DocumentPipeline()
        result = pipeline.run(doc)

        for stage in result.metadata.stages:
            assert stage.duration_ms > 0
            assert stage.status in ("success", "degraded", "skipped", "failed")

    def test_warnings_collected(self, sample_pdf_content):
        doc = _make_raw_document(sample_pdf_content, "test.pdf", DocumentFormat.PDF)
        pipeline = DocumentPipeline()
        result = pipeline.run(doc)

        assert isinstance(result.metadata.warnings, list)

    def test_pipeline_idempotent(self, sample_pdf_content):
        doc = _make_raw_document(sample_pdf_content, "test.pdf", DocumentFormat.PDF)
        pipeline = DocumentPipeline()
        result1 = pipeline.run(doc)
        result2 = pipeline.run(doc)

        comparison_fields = ["format", "word_count", "char_count"]
        s1 = result1.metadata.statistics
        s2 = result2.metadata.statistics
        for field in comparison_fields:
            assert getattr(s1, field) == getattr(s2, field), f"Mismatch in {field}"

    def test_pipeline_with_all_formats_produce_stats(self, sample_pdf_content, sample_docx_content, sample_txt_content, sample_html_content):
        contents = [
            (sample_pdf_content, DocumentFormat.PDF),
            (sample_docx_content, DocumentFormat.DOCX),
            (sample_txt_content, DocumentFormat.TXT),
            (sample_html_content, DocumentFormat.HTML),
        ]
        pipeline = DocumentPipeline()
        for content, fmt in contents:
            doc = _make_raw_document(content, f"test.{fmt.value}", fmt)
            result = pipeline.run(doc)
            assert result.metadata.statistics is not None
            assert result.metadata.statistics.format == fmt

    def test_statistics_model_fields(self, sample_pdf_content):
        doc = _make_raw_document(sample_pdf_content, "test.pdf", DocumentFormat.PDF)
        pipeline = DocumentPipeline()
        result = pipeline.run(doc)
        stats = result.metadata.statistics

        assert isinstance(stats, DocumentStatistics)
        assert isinstance(stats.format, DocumentFormat)
        assert isinstance(stats.filename, str)
        assert isinstance(stats.file_size_bytes, int)
        assert isinstance(stats.checksum_sha256, str)
        assert isinstance(stats.word_count, int)
        assert isinstance(stats.char_count, int)
        assert isinstance(stats.structural_element_count, int)
        assert isinstance(stats.clause_count, int)
        assert isinstance(stats.root_clause_count, int)
        assert isinstance(stats.cleaning_operations_applied, list)

    def test_validation_info_model_fields(self, sample_pdf_content):
        doc = _make_raw_document(sample_pdf_content, "test.pdf", DocumentFormat.PDF)
        pipeline = DocumentPipeline()
        result = pipeline.run(doc)
        validation = result.metadata.validation

        assert isinstance(validation, ValidationInfo)
        assert validation.overall_status in ("complete", "degraded", "failed")
        assert isinstance(validation.stages_valid, list)
        assert isinstance(validation.stages_failed, list)
        assert isinstance(validation.stages_skipped, list)
        assert isinstance(validation.is_complete, bool)
        assert isinstance(validation.is_degraded, bool)
        assert isinstance(validation.warnings_count, int)

    def test_raw_document_preserved_in_ir(self, sample_pdf_content):
        doc = _make_raw_document(sample_pdf_content, "test.pdf", DocumentFormat.PDF)
        pipeline = DocumentPipeline()
        result = pipeline.run(doc)

        assert result.raw_document.id == doc.id
        assert result.raw_document.filename == doc.filename
        assert result.raw_document.format == doc.format
        assert result.raw_document.content == doc.content
        assert result.raw_document.size_bytes == doc.size_bytes
        assert result.raw_document.checksum_sha256 == doc.checksum_sha256

    def test_errors_collected_on_failure(self, raw_empty):
        pipeline = DocumentPipeline()
        result = pipeline.run(raw_empty)

        assert len(result.metadata.errors) > 0
        error = result.metadata.errors[0]
        assert error.stage == "extract"
        assert error.is_fatal is True

    def test_cleaning_produces_valid_document(self, sample_pdf_content):
        doc = _make_raw_document(sample_pdf_content, "test.pdf", DocumentFormat.PDF)
        pipeline = DocumentPipeline()
        result = pipeline.run(doc)

        cleaned = result.cleaned_document
        assert isinstance(cleaned, CleanedDocument)
        assert cleaned.extracted_id == result.extracted_document.raw_id
        assert len(cleaned.text) > 0
        assert cleaned.stats.original_char_count > 0
        assert cleaned.stats.cleaned_char_count > 0

    def test_structure_detection_produces_valid_document(self, sample_pdf_content):
        doc = _make_raw_document(sample_pdf_content, "test.pdf", DocumentFormat.PDF)
        pipeline = DocumentPipeline()
        result = pipeline.run(doc)

        structured = result.structured_document
        assert isinstance(structured, StructuredDocument)
        assert structured.cleaned_id == result.cleaned_document.extracted_id
        assert len(structured.structure.elements) > 0

    def test_clause_extraction_produces_valid_document(self, sample_pdf_content):
        doc = _make_raw_document(sample_pdf_content, "test.pdf", DocumentFormat.PDF)
        pipeline = DocumentPipeline()
        result = pipeline.run(doc)

        clauses = result.clause_document
        assert isinstance(clauses, ClauseDocument)
        assert clauses.clause_count > 0
        assert len(clauses.root_clause_ids) > 0

    def test_clause_extraction_uses_structured_id(self, sample_pdf_content):
        doc = _make_raw_document(sample_pdf_content, "test.pdf", DocumentFormat.PDF)
        pipeline = DocumentPipeline()
        result = pipeline.run(doc)

        assert result.clause_document.structured_id == result.structured_document.cleaned_id

    def test_statistics_cleaning_operations(self, sample_pdf_content):
        doc = _make_raw_document(sample_pdf_content, "test.pdf", DocumentFormat.PDF)
        pipeline = DocumentPipeline()
        result = pipeline.run(doc)

        ops = result.metadata.statistics.cleaning_operations_applied
        assert isinstance(ops, list)
        if ops:
            assert all(isinstance(op, CleaningOperation) for op in ops)

    def test_statistics_page_count_pdf(self, sample_pdf_content):
        doc = _make_raw_document(sample_pdf_content, "test.pdf", DocumentFormat.PDF)
        pipeline = DocumentPipeline()
        result = pipeline.run(doc)

        assert result.metadata.statistics.page_count == 1

    def test_statistics_clause_count_pdf(self, sample_pdf_content):
        doc = _make_raw_document(sample_pdf_content, "test.pdf", DocumentFormat.PDF)
        pipeline = DocumentPipeline()
        result = pipeline.run(doc)

        assert result.metadata.statistics.clause_count >= 5

    def test_statistics_language_detected(self, sample_pdf_content):
        doc = _make_raw_document(sample_pdf_content, "test.pdf", DocumentFormat.PDF)
        pipeline = DocumentPipeline()
        result = pipeline.run(doc)

        lang = result.metadata.statistics.language
        assert lang is not None
        assert len(lang) >= 2

    def test_statistics_checksum_matches(self, sample_pdf_content):
        doc = _make_raw_document(sample_pdf_content, "test.pdf", DocumentFormat.PDF)
        pipeline = DocumentPipeline()
        result = pipeline.run(doc)

        expected_checksum = hashlib.sha256(sample_pdf_content).hexdigest()
        assert result.metadata.statistics.checksum_sha256 == expected_checksum

    def test_multiple_pipeline_runs_independent(self, sample_pdf_content):
        doc = _make_raw_document(sample_pdf_content, "test.pdf", DocumentFormat.PDF)
        pipeline = DocumentPipeline()
        result1 = pipeline.run(doc)
        result2 = pipeline.run(doc)

        assert result1.metadata.correlation_id != result2.metadata.correlation_id

    def test_to_json_serialization(self, sample_pdf_content):
        doc = _make_raw_document(sample_pdf_content, "test.pdf", DocumentFormat.PDF)
        pipeline = DocumentPipeline()
        result = pipeline.run(doc)

        json_str = result.to_json()
        parsed = json.loads(json_str)
        assert parsed["metadata"]["correlation_id"] == result.metadata.correlation_id
        assert parsed["metadata"]["pipeline_version"] == "1.0.0"
        assert parsed["metadata"]["processing_status"] == "complete"
        assert "raw_document" in parsed
        assert "extracted_document" in parsed
        assert "cleaned_document" in parsed
        assert "structured_document" in parsed
        assert "clause_document" in parsed

    def test_to_json_exclude_raw_content(self, sample_pdf_content):
        doc = _make_raw_document(sample_pdf_content, "test.pdf", DocumentFormat.PDF)
        pipeline = DocumentPipeline()
        result = pipeline.run(doc)

        json_str = result.to_json(exclude_raw_content=True)
        parsed = json.loads(json_str)
        assert "raw_document" not in parsed

    def test_from_json_deserialization(self, sample_pdf_content):
        doc = _make_raw_document(sample_pdf_content, "test.pdf", DocumentFormat.PDF)
        pipeline = DocumentPipeline()
        original = pipeline.run(doc)

        json_str = original.to_json()
        restored = CanonicalIntermediateRepresentation.from_json(json_str)

        assert restored.metadata.correlation_id == original.metadata.correlation_id
        assert restored.metadata.processing_status == original.metadata.processing_status
        assert restored.metadata.total_duration_ms == original.metadata.total_duration_ms
        assert restored.raw_document.id == original.raw_document.id

    @pytest.mark.slow
    def test_export_json_file(self, sample_pdf_content):
        doc = _make_raw_document(sample_pdf_content, "test.pdf", DocumentFormat.PDF)
        pipeline = DocumentPipeline()
        result = pipeline.run(doc)

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w", encoding="utf-8") as f:
            tmp_path = f.name

        try:
            result.export_json(tmp_path)
            assert Path(tmp_path).exists()
            assert Path(tmp_path).stat().st_size > 0

            restored = CanonicalIntermediateRepresentation.import_json(tmp_path)
            assert restored.metadata.correlation_id == result.metadata.correlation_id
            assert restored.metadata.processing_status == result.metadata.processing_status
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def test_round_trip_json_preserves_statistics(self, sample_pdf_content):
        doc = _make_raw_document(sample_pdf_content, "test.pdf", DocumentFormat.PDF)
        pipeline = DocumentPipeline()
        original = pipeline.run(doc)

        json_str = original.to_json()
        restored = CanonicalIntermediateRepresentation.from_json(json_str)

        orig_stats = original.metadata.statistics
        rest_stats = restored.metadata.statistics
        assert rest_stats.word_count == orig_stats.word_count
        assert rest_stats.char_count == orig_stats.char_count
        assert rest_stats.clause_count == orig_stats.clause_count
        assert rest_stats.filename == orig_stats.filename

    def test_round_trip_json_preserves_validation(self, sample_pdf_content):
        doc = _make_raw_document(sample_pdf_content, "test.pdf", DocumentFormat.PDF)
        pipeline = DocumentPipeline()
        original = pipeline.run(doc)

        json_str = original.to_json()
        restored = CanonicalIntermediateRepresentation.from_json(json_str)

        orig_val = original.metadata.validation
        rest_val = restored.metadata.validation
        assert rest_val.overall_status == orig_val.overall_status
        assert rest_val.is_complete == orig_val.is_complete
        assert rest_val.is_degraded == orig_val.is_degraded
        assert rest_val.warnings_count == orig_val.warnings_count

    def test_round_trip_json_preserves_stages(self, sample_pdf_content):
        doc = _make_raw_document(sample_pdf_content, "test.pdf", DocumentFormat.PDF)
        pipeline = DocumentPipeline()
        original = pipeline.run(doc)

        json_str = original.to_json()
        restored = CanonicalIntermediateRepresentation.from_json(json_str)

        assert len(restored.metadata.stages) == len(original.metadata.stages)
        for rs, os in zip(restored.metadata.stages, original.metadata.stages):
            assert rs.stage_name == os.stage_name
            assert rs.status == os.status
            assert rs.duration_ms == os.duration_ms

    def test_round_trip_json_preserves_clauses(self, sample_pdf_content):
        doc = _make_raw_document(sample_pdf_content, "test.pdf", DocumentFormat.PDF)
        pipeline = DocumentPipeline()
        original = pipeline.run(doc)

        json_str = original.to_json()
        restored = CanonicalIntermediateRepresentation.from_json(json_str)

        assert restored.clause_document.clause_count == original.clause_document.clause_count
        assert len(restored.clause_document.root_clause_ids) == len(original.clause_document.root_clause_ids)

    def test_json_indent_parameter(self, sample_pdf_content):
        doc = _make_raw_document(sample_pdf_content, "test.pdf", DocumentFormat.PDF)
        pipeline = DocumentPipeline()
        result = pipeline.run(doc)

        compact = result.to_json(indent=0)
        pretty = result.to_json(indent=4)
        assert len(pretty) >= len(compact)
        assert "\n" in pretty

    def test_pipeline_with_config_disabling_degraded(self, raw_empty):
        config = PipelineConfig(enable_degraded_mode=False)
        pipeline = DocumentPipeline(config=config)
        result = pipeline.run(raw_empty)

        assert result.metadata.processing_status == "failed"
        stage_map = {s.stage_name: s.status for s in result.metadata.stages}
        assert stage_map["extract"] == "failed"

    def test_statistics_property(self, sample_pdf_content):
        doc = _make_raw_document(sample_pdf_content, "test.pdf", DocumentFormat.PDF)
        pipeline = DocumentPipeline()
        result = pipeline.run(doc)

        assert result.statistics is result.metadata.statistics

    def test_validation_property(self, sample_pdf_content):
        doc = _make_raw_document(sample_pdf_content, "test.pdf", DocumentFormat.PDF)
        pipeline = DocumentPipeline()
        result = pipeline.run(doc)

        assert result.validation is result.metadata.validation

    def test_statistics_for_empty_extraction(self, raw_empty):
        pipeline = DocumentPipeline()
        result = pipeline.run(raw_empty)

        stats = result.metadata.statistics
        assert stats.word_count == 0
        assert stats.char_count == 0
        assert stats.clause_count == 0
        assert stats.structural_element_count == 0
        assert stats.cleaned_char_count is None

    def test_validation_for_empty_extraction(self, raw_empty):
        pipeline = DocumentPipeline()
        result = pipeline.run(raw_empty)

        validation = result.metadata.validation
        assert validation.overall_status != "complete"
        assert len(validation.stages_failed) > 0

    def test_pipeline_returns_frozen_models(self, sample_pdf_content):
        doc = _make_raw_document(sample_pdf_content, "test.pdf", DocumentFormat.PDF)
        pipeline = DocumentPipeline()
        result = pipeline.run(doc)

        import pydantic
        with pytest.raises(pydantic.ValidationError):
            result.raw_document.filename = "new_name.pdf"

    def test_statistics_structural_element_count_positive(self, sample_pdf_content):
        doc = _make_raw_document(sample_pdf_content, "test.pdf", DocumentFormat.PDF)
        pipeline = DocumentPipeline()
        result = pipeline.run(doc)

        assert result.metadata.statistics.structural_element_count >= 4

    def test_statistics_section_count(self, sample_pdf_content):
        doc = _make_raw_document(sample_pdf_content, "test.pdf", DocumentFormat.PDF)
        pipeline = DocumentPipeline()
        result = pipeline.run(doc)

        assert result.metadata.statistics.section_count >= 1

    def test_pipeline_with_no_clauses_empty_document(self):
        content = b"Just a simple text with no legal structure whatsoever."
        doc = _make_raw_document(content, "simple.txt", DocumentFormat.TXT)
        pipeline = DocumentPipeline()
        result = pipeline.run(doc)

        assert result.metadata.processing_status in ("complete", "degraded")
        assert result.clause_document is not None
        assert result.metadata.statistics.clause_count >= 0

    def test_extraction_error_has_details(self, raw_empty):
        pipeline = DocumentPipeline()
        result = pipeline.run(raw_empty)

        for err in result.metadata.errors:
            assert err.error_code is not None
            assert err.stage is not None
            assert err.message is not None

    def test_json_deserialize_from_string(self, sample_pdf_content):
        doc = _make_raw_document(sample_pdf_content, "test.pdf", DocumentFormat.PDF)
        pipeline = DocumentPipeline()
        original = pipeline.run(doc)

        json_str = original.to_json()
        restored = CanonicalIntermediateRepresentation.model_validate_json(json_str)

        assert restored.metadata.correlation_id == original.metadata.correlation_id
