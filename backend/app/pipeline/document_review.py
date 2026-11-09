from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from app.document_review.base import DocumentReviewer, DocumentReviewError
from app.document_review.reconciliation import merge_document_extractions
from app.document_review.schemas import DocumentReview
from app.documents.projection import project_extraction
from app.documents.schemas import ReviewData

if TYPE_CHECKING:
    from app.pipeline.base import PipelineContext

logger = logging.getLogger(__name__)


class UnsupportedDocumentError(RuntimeError):
    """Raised when the independent LLM review classifies the file as unsupported."""


class DocumentReviewStep:
    """Project DI extraction, run independent LLM review, and merge gaps."""

    name = "document_review"

    def __init__(
        self,
        *,
        reviewer: DocumentReviewer | None = None,
        content_type: str | None = None,
    ) -> None:
        self._reviewer = reviewer
        self._content_type = content_type

    def run(self, ctx: PipelineContext) -> PipelineContext:
        if ctx.extraction is None:
            raise ValueError("DocumentReviewStep requires ctx.extraction from ExtractionStep.")

        is_gemini = isinstance(ctx.extraction, ReviewData)
        review_data = ctx.extraction if is_gemini else project_extraction(ctx.extraction)
        provider_info = (
            {"primary_provider": "gemini", "review_provider": "gemini"} if is_gemini else {}
        )
        content_type = self._content_type or ctx.content_type
        if self._reviewer is None or content_type is None:
            logger.info("Skipping AI cross-check; using primary extraction only")
            return ctx.model_copy(
                update={
                    "review_data": review_data,
                    "document_review": DocumentReview(
                        **provider_info,
                        error_message="AI cross-check was not configured."
                    ),
                }
            )

        try:
            llm_extraction = self._reviewer.review(ctx.document_path, content_type)
        except DocumentReviewError as error:
            logger.warning("LLM document review failed: %s", error)
            return ctx.model_copy(
                update={
                    "review_data": review_data,
                    "document_review": DocumentReview(**provider_info, error_message=str(error)),
                }
            )

        if llm_extraction.document_type == "unsupported":
            raise UnsupportedDocumentError(
                "The uploaded file is not a supported invoice or receipt."
            )

        merged, document_review = merge_document_extractions(
            review_data, llm_extraction,
            primary_source="gemini" if is_gemini else "document_intelligence",
            fallback_source="gemini_review" if is_gemini else "llm_fallback",
        )
        document_review = document_review.model_copy(update=provider_info)
        logger.info(
            "Merged primary and review extractions (%d fallback field(s))",
            len(document_review.fallback_fields),
        )
        return ctx.model_copy(
            update={"review_data": merged, "document_review": document_review}
        )
