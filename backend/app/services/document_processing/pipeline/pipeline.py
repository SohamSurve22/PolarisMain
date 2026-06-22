import time
import uuid
from datetime import datetime, timezone

from ..cleaners import LegalCleaner
from ..clause_extractors import ClauseExtractor
from ..extractors import ExtractorRegistry
from ..models import (
    CanonicalIntermediateRepresentation,
    ClauseDocument,
    CleanedDocument,
    DocumentStatistics,
    IRMetadata,
    PipelineConfig,
    PipelineError,
    RawDocument,
    StageTiming,
    StructuredDocument,
    ValidationInfo,
)
from ..structure_detectors import StructureDetector


class DocumentPipeline:
    def __init__(self, config: PipelineConfig | None = None):
        self._config = config or PipelineConfig()
        self._extractor_registry = ExtractorRegistry()
        self._cleaner = LegalCleaner(config=self._config.cleaner if config else None)
        self._structure_detector = StructureDetector(
            config=self._config.structure_detector if config else None
        )
        self._clause_extractor = ClauseExtractor(
            config=self._config.clause_extractor if config else None
        )

    def run(self, document: RawDocument) -> CanonicalIntermediateRepresentation:
        correlation_id = str(uuid.uuid4())
        started_at = datetime.now(timezone.utc)
        stages: list[StageTiming] = []
        all_warnings: list[str] = []
        all_errors: list[PipelineError] = []

        extracted_doc = self._run_extraction(
            document, stages, all_warnings, all_errors
        )
        cleaned_doc = None
        structured_doc = None
        clause_doc = None

        if extracted_doc is not None:
            cleaned_doc = self._run_cleaning(
                extracted_doc, stages, all_warnings, all_errors
            )
        elif not any(s.stage_name == "clean" for s in stages):
            stages.append(StageTiming(
                stage_name="clean", status="skipped", duration_ms=0.0,
            ))

        if cleaned_doc is not None:
            structured_doc = self._run_structure_detection(
                cleaned_doc, stages, all_warnings, all_errors
            )
        elif not any(s.stage_name == "structure_detect" for s in stages):
            stages.append(StageTiming(
                stage_name="structure_detect", status="skipped", duration_ms=0.0,
            ))

        if cleaned_doc is not None and structured_doc is not None:
            clause_doc = self._run_clause_extraction(
                cleaned_doc, structured_doc, stages, all_warnings, all_errors
            )
        elif not any(s.stage_name == "clause_extract" for s in stages):
            stages.append(StageTiming(
                stage_name="clause_extract", status="skipped", duration_ms=0.0,
            ))

        completed_at = datetime.now(timezone.utc)
        total_duration = (completed_at - started_at).total_seconds() * 1000

        processing_status = self._compute_processing_status(stages)

        stages_valid = [s.stage_name for s in stages if s.status == "success"]
        stages_failed = [s.stage_name for s in stages if s.status in ("failed", "degraded")]
        stages_skipped = [s.stage_name for s in stages if s.status == "skipped"]

        validation = ValidationInfo(
            overall_status=processing_status,
            stages_valid=stages_valid,
            stages_failed=stages_failed,
            stages_skipped=stages_skipped,
            is_complete=processing_status == "complete",
            is_degraded=processing_status == "degraded",
            warnings_count=len(all_warnings),
        )

        statistics = self._build_statistics(
            document, extracted_doc, cleaned_doc, structured_doc, clause_doc,
        )

        metadata = IRMetadata(
            pipeline_version=self._config.version,
            correlation_id=correlation_id,
            processing_status=processing_status,
            stages=stages,
            total_duration_ms=round(total_duration, 2),
            warnings=all_warnings,
            errors=all_errors,
            started_at=started_at,
            completed_at=completed_at,
            statistics=statistics,
            validation=validation,
        )

        return CanonicalIntermediateRepresentation(
            raw_document=document,
            extracted_document=extracted_doc,
            cleaned_document=cleaned_doc,
            structured_document=structured_doc,
            clause_document=clause_doc,
            metadata=metadata,
        )

    def _compute_processing_status(self, stages: list[StageTiming]) -> str:
        if not stages:
            return "failed"
        any_failed = any(s.status == "failed" for s in stages)
        any_degraded = any(s.status == "degraded" for s in stages)
        all_success = all(s.status == "success" for s in stages)
        if any_failed:
            return "failed"
        if any_degraded:
            return "degraded"
        if all_success:
            return "complete"
        return "failed"

    def _run_extraction(
        self, document: RawDocument, stages: list, warnings: list, errors: list
    ):
        if len(document.content) > self._config.max_file_size_bytes:
            pipe_err = PipelineError(
                error_code="FILE_TOO_LARGE", stage="extract",
                message=f"File size {len(document.content)} exceeds max {self._config.max_file_size_bytes}",
                is_fatal=True, recoverable=False,
            )
            stages.append(StageTiming(
                stage_name="extract", status="failed", duration_ms=0.0, error=pipe_err,
            ))
            errors.append(pipe_err)
            return None

        start = time.time()
        try:
            extractor = self._extractor_registry.get_extractor(document.format)
            result = extractor.extract(document)
            duration = (time.time() - start) * 1000
            if result.success:
                stages.append(StageTiming(
                    stage_name="extract", status="success", duration_ms=round(duration, 2),
                ))
                warnings.extend(
                    f"Extraction warning: {w.message}" for w in result.document.warnings
                )
                return result.document
            else:
                err_msg = result.error.message if result.error else "Extraction returned no result"
                pipe_err = PipelineError(
                    error_code="EXTRACTION_FAILED", stage="extract",
                    message=err_msg, is_fatal=True, recoverable=False,
                )
                stages.append(StageTiming(
                    stage_name="extract", status="failed",
                    duration_ms=round(duration, 2), error=pipe_err,
                ))
                errors.append(pipe_err)
                return None
        except Exception as exc:
            duration = (time.time() - start) * 1000
            pipe_err = PipelineError(
                error_code="EXTRACTION_FAILED", stage="extract",
                message=str(exc), is_fatal=True, recoverable=False,
            )
            stages.append(StageTiming(
                stage_name="extract", status="failed",
                duration_ms=round(duration, 2), error=pipe_err,
            ))
            errors.append(pipe_err)
            return None

    def _run_cleaning(
        self, extracted, stages: list, warnings: list, errors: list
    ):
        start = time.time()
        try:
            cleaned = self._cleaner.clean(extracted)
            duration = (time.time() - start) * 1000
            stages.append(StageTiming(
                stage_name="clean", status="success", duration_ms=round(duration, 2),
            ))
            warnings.extend(cleaned.warnings)
            return cleaned
        except Exception as exc:
            duration = (time.time() - start) * 1000
            pipe_err = PipelineError(
                error_code="CLEANING_FAILED", stage="clean",
                message=str(exc), is_fatal=False, recoverable=True,
            )
            status = "degraded" if self._config.enable_degraded_mode else "failed"
            stages.append(StageTiming(
                stage_name="clean", status=status,
                duration_ms=round(duration, 2), error=pipe_err,
            ))
            errors.append(pipe_err)
            if status == "failed":
                return None
            return None

    def _run_structure_detection(
        self, cleaned, stages: list, warnings: list, errors: list
    ):
        start = time.time()
        try:
            structured = self._structure_detector.detect(cleaned)
            duration = (time.time() - start) * 1000
            stages.append(StageTiming(
                stage_name="structure_detect", status="success",
                duration_ms=round(duration, 2),
            ))
            return structured
        except Exception as exc:
            duration = (time.time() - start) * 1000
            pipe_err = PipelineError(
                error_code="STRUCTURE_DETECTION_FAILED", stage="structure_detect",
                message=str(exc), is_fatal=False, recoverable=True,
            )
            status = "degraded" if self._config.enable_degraded_mode else "failed"
            stages.append(StageTiming(
                stage_name="structure_detect", status=status,
                duration_ms=round(duration, 2), error=pipe_err,
            ))
            errors.append(pipe_err)
            return None

    def _run_clause_extraction(
        self, cleaned, structured, stages: list, warnings: list, errors: list
    ):
        start = time.time()
        try:
            clause_doc = self._clause_extractor.extract(cleaned, structured)
            duration = (time.time() - start) * 1000
            stages.append(StageTiming(
                stage_name="clause_extract", status="success",
                duration_ms=round(duration, 2),
            ))
            return clause_doc
        except Exception as exc:
            duration = (time.time() - start) * 1000
            pipe_err = PipelineError(
                error_code="CLAUSE_EXTRACTION_FAILED", stage="clause_extract",
                message=str(exc), is_fatal=False, recoverable=True,
            )
            status = "degraded" if self._config.enable_degraded_mode else "failed"
            stages.append(StageTiming(
                stage_name="clause_extract", status=status,
                duration_ms=round(duration, 2), error=pipe_err,
            ))
            errors.append(pipe_err)
            return None

    def _build_statistics(
        self,
        raw: RawDocument,
        extracted: "ExtractedDocument | None",
        cleaned: "CleanedDocument | None",
        structured: "StructuredDocument | None",
        clauses: "ClauseDocument | None",
    ) -> DocumentStatistics:
        meta = extracted.metadata if extracted else None
        word_count = meta.word_count if meta else 0
        char_count = meta.char_count if meta else 0
        page_count = meta.page_count if meta else None
        language = meta.language if meta else None
        lang_conf = meta.language_confidence if meta else None
        has_images = meta.has_images if meta else False
        has_tables = meta.has_tables if meta else False
        is_scanned = meta.is_scanned if meta else False

        cstats = cleaned.stats if cleaned else None
        cleaned_char_count = cstats.cleaned_char_count if cstats else None
        removed_char_count = cstats.removed_char_count if cstats else None
        cleaning_ops = cstats.operations_applied if cstats else []

        elements = list(structured.structure.elements.values()) if structured else []
        element_count = len(elements)
        section_count = len([
            e for e in elements
            if e.type.value in ("heading", "subheading", "schedule")
        ])

        clause_count = clauses.clause_count if clauses else 0
        root_clause_count = len(clauses.root_clause_ids) if clauses else 0

        return DocumentStatistics(
            format=raw.format,
            filename=raw.filename,
            file_size_bytes=raw.size_bytes,
            checksum_sha256=raw.checksum_sha256,
            word_count=word_count,
            char_count=char_count,
            cleaned_char_count=cleaned_char_count,
            removed_char_count=removed_char_count,
            page_count=page_count,
            language=language,
            language_confidence=lang_conf,
            has_images=has_images,
            has_tables=has_tables,
            is_scanned=is_scanned,
            structural_element_count=element_count,
            section_count=section_count,
            clause_count=clause_count,
            root_clause_count=root_clause_count,
            cleaning_operations_applied=cleaning_ops,
        )
