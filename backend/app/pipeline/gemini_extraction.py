from pydantic import ValidationError

from app.pipeline.base import PipelineContext
from app.pipeline.document_review import UnsupportedDocumentError
from app.providers.gemini import GeminiClient, GeminiError
from app.providers.gemini_documents import EXTRACTION_INSTRUCTIONS, GeminiExtraction


class GeminiExtractionStep:
    """Classify and extract together to use one free-tier request instead of two."""

    name = "classification_and_extraction"

    def __init__(self, client: GeminiClient) -> None:
        self.client = client

    def run(self, ctx: PipelineContext) -> PipelineContext:
        extraction = self.client.generate(
            GeminiExtraction,
            instructions=EXTRACTION_INSTRUCTIONS,
            prompt=(
                "Read this document, including its line items. Give a brief classification "
                "reason and a self-assessed classification confidence from 0 to 1; "
                "this is not a calibrated accuracy measurement."
            ),
            path=ctx.document_path,
        )
        if extraction.document_type == "unsupported":
            raise UnsupportedDocumentError("The uploaded file is not an invoice or receipt.")
        try:
            review_data = extraction.to_review_data()
        except (ValidationError, ValueError):
            raise GeminiError(
                "Gemini returned invalid dates or amounts. Check the source document."
            ) from None
        return ctx.model_copy(
            update={
                "classification": extraction.classification(),
                "extraction": review_data,
            }
        )
