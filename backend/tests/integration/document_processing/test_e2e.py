"""End-to-end integration tests for the full document parsing pipeline."""

import json
import tempfile
from pathlib import Path

import pytest

from backend.app.services.document_processing import (
    DocumentFormat,
    DocumentProcessor,
    PipelineConfig,
)


class TestEndToEnd:
    def test_full_pipeline_pdf_file(self, sample_pdf_content):
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(sample_pdf_content)
            tmp = f.name

        try:
            processor = DocumentProcessor.create_default()
            result = processor.process_file(tmp)

            assert result.metadata.processing_status == "complete"
            assert result.extracted_document is not None
            assert result.cleaned_document is not None
            assert result.structured_document is not None
            assert result.clause_document is not None
            assert result.metadata.statistics.clause_count >= 5
        finally:
            Path(tmp).unlink(missing_ok=True)

    def test_full_pipeline_docx_file(self, sample_docx_content):
        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
            f.write(sample_docx_content)
            tmp = f.name

        try:
            processor = DocumentProcessor.create_default()
            result = processor.process_file(tmp)

            assert result.metadata.processing_status in ("complete", "degraded")
            assert result.extracted_document is not None
        finally:
            Path(tmp).unlink(missing_ok=True)

    def test_full_pipeline_txt_file(self, sample_txt_content):
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            f.write(sample_txt_content)
            tmp = f.name

        try:
            processor = DocumentProcessor.create_default()
            result = processor.process_file(tmp)

            assert result.metadata.processing_status == "complete"
            assert result.extracted_document is not None
        finally:
            Path(tmp).unlink(missing_ok=True)

    def test_full_pipeline_html_file(self, sample_html_content):
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
            f.write(sample_html_content)
            tmp = f.name

        try:
            processor = DocumentProcessor.create_default()
            result = processor.process_file(tmp)

            assert result.metadata.processing_status == "complete"
            assert result.extracted_document is not None
        finally:
            Path(tmp).unlink(missing_ok=True)

    def test_process_bytes_api(self, sample_pdf_content):
        processor = DocumentProcessor.create_default()
        result = processor.process_bytes(
            sample_pdf_content,
            filename="test.pdf",
            fmt=DocumentFormat.PDF,
        )
        assert result.metadata.processing_status == "complete"

    def test_process_bytes_auto_detect_format(self, sample_pdf_content):
        processor = DocumentProcessor.create_default()
        result = processor.process_bytes(
            sample_pdf_content,
            filename="test.pdf",
        )
        assert result.metadata.processing_status == "complete"

    def test_process_invalid_format_raises(self):
        processor = DocumentProcessor.create_default()
        with pytest.raises(ValueError, match="Unsupported file format"):
            processor.process_bytes(b"data", "test.xyz", fmt=None)

    def test_file_not_found_raises(self):
        processor = DocumentProcessor.create_default()
        with pytest.raises(FileNotFoundError):
            processor.process_file("/nonexistent/file.pdf")

    def test_json_config_loading(self, sample_pdf_content):
        config_json = json.dumps({
            "version": "test-1.0",
            "enable_degraded_mode": False,
        })
        config = PipelineConfig.from_json_string(config_json)
        assert config.version == "test-1.0"
        assert config.enable_degraded_mode is False

        processor = DocumentProcessor(config=config)
        result = processor.process_bytes(sample_pdf_content, "test.pdf")
        assert result.metadata.pipeline_version == "test-1.0"

    def test_json_config_from_file(self, sample_pdf_content):
        config = {
            "version": "file-1.0",
            "extractor": {"pdf_strategy": "pymupdf"},
        }
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False, encoding="utf-8") as f:
            json.dump(config, f)
            tmp = f.name

        try:
            processor = DocumentProcessor.from_json_config(tmp)
            result = processor.process_bytes(sample_pdf_content, "test.pdf")
            assert result.metadata.pipeline_version == "file-1.0"
        finally:
            Path(tmp).unlink(missing_ok=True)

    def test_full_ir_json_roundtrip(self, sample_pdf_content):
        processor = DocumentProcessor.create_default()
        result = processor.process_bytes(sample_pdf_content, "test.pdf")

        json_str = result.to_json()
        from backend.app.services.document_processing import CanonicalIntermediateRepresentation
        restored = CanonicalIntermediateRepresentation.from_json(json_str)

        assert restored.metadata.correlation_id == result.metadata.correlation_id
        assert restored.metadata.statistics.clause_count == result.metadata.statistics.clause_count

    def test_process_raw_document(self, sample_pdf_content, raw_pdf):
        processor = DocumentProcessor.create_default()
        result = processor.process_raw(raw_pdf)

        assert result.metadata.processing_status == "complete"
        assert result.raw_document.id == raw_pdf.id

    def test_processor_config_property(self):
        config = PipelineConfig(version="custom-1.0")
        processor = DocumentProcessor(config=config)
        assert processor.config.version == "custom-1.0"

    def test_unsupported_format_error(self):
        processor = DocumentProcessor.create_default()
        with pytest.raises(ValueError, match="Unsupported file format"):
            processor.process_bytes(b"data", "test.xyz")

    def test_processor_default_creates_valid_instance(self):
        processor = DocumentProcessor.create_default()
        assert processor.config.version == "1.0.0"
        assert processor.config.enable_degraded_mode is True

    def test_e2e_clause_content_non_empty(self, sample_pdf_content):
        processor = DocumentProcessor.create_default()
        result = processor.process_bytes(sample_pdf_content, "test.pdf")

        for clause in result.clause_document.clauses.values():
            assert len(clause.body) > 0

    def test_e2e_all_stages_have_timing(self, sample_pdf_content):
        processor = DocumentProcessor.create_default()
        result = processor.process_bytes(sample_pdf_content, "test.pdf")

        for stage in result.metadata.stages:
            assert stage.duration_ms > 0 or stage.status == "skipped"

    def test_e2e_metadata_has_correlation_id(self, sample_pdf_content):
        processor = DocumentProcessor.create_default()
        result = processor.process_bytes(sample_pdf_content, "test.pdf")
        assert len(result.metadata.correlation_id) > 0

    def test_e2e_statistics_checksum_matches(self, sample_pdf_content):
        import hashlib
        processor = DocumentProcessor.create_default()
        result = processor.process_bytes(sample_pdf_content, "test.pdf")
        expected = hashlib.sha256(sample_pdf_content).hexdigest()
        assert result.metadata.statistics.checksum_sha256 == expected

    def test_e2e_with_config_disabling_degraded(self, sample_pdf_content):
        config = PipelineConfig(enable_degraded_mode=False)
        processor = DocumentProcessor(config=config)
        result = processor.process_bytes(sample_pdf_content, "test.pdf")
        assert result.metadata.processing_status == "complete"

    def test_e2e_json_output_contains_all_sections(self, sample_pdf_content):
        processor = DocumentProcessor.create_default()
        result = processor.process_bytes(sample_pdf_content, "test.pdf")
        parsed = json.loads(result.to_json())
        assert "raw_document" in parsed
        assert "extracted_document" in parsed
        assert "cleaned_document" in parsed
        assert "structured_document" in parsed
        assert "clause_document" in parsed
        assert "metadata" in parsed
