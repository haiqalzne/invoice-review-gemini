import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field

from app.correction_email.base import CorrectionEmailDraftingError
from app.correction_email.schemas import CorrectionEmailDraft
from app.document_review.base import DocumentReviewError
from app.document_review.schemas import LlmDocumentExtraction
from app.documents.schemas import ReviewData, ReviewLineItem, ValidationIssue
from app.pipeline.classification import DocumentClassification
from app.pipeline.gl_categorization import (
    GL_CATEGORIZATION_INSTRUCTIONS,
    GlSuggestion,
    build_gl_categorization_input,
)
from app.providers.gemini import GeminiClient, GeminiError

EXTRACTION_INSTRUCTIONS = """
Read the original financial document. Classify it as invoice, receipt or unsupported.
An invoice requests payment; a receipt records an expense already paid.
Extract only visible facts. Use null for absent or unreadable fields; never invent values.
For receipts use merchant as vendor_name, transaction date as invoice_date, and total as
invoice_total and amount_due. Classify receipt expenses as fuel/meals/travel/supplies/other.
Return dates as YYYY-MM-DD, ISO currency codes, and amounts as plain decimal strings without
symbols or thousands separators. Preserve the document's totals even when they are wrong.
Do not fix arithmetic, decide approval, or infer missing VAT numbers or purchase orders.
""".strip()


class GeminiLineItem(BaseModel):
    model_config = ConfigDict(extra="forbid")
    description: str | None
    quantity: str | None
    unit_price: str | None
    amount: str | None


class GeminiExtraction(LlmDocumentExtraction):
    line_items: list[GeminiLineItem]
    classification_confidence: float = Field(ge=0, le=1)
    classification_reason: str

    def to_review_data(self) -> ReviewData:
        values = self.model_dump(
            exclude={
                "summary",
                "line_items",
                "classification_confidence",
                "classification_reason",
            }
        )
        values["line_items"] = [
            ReviewLineItem.model_validate(item.model_dump()) for item in self.line_items
        ]
        values["field_sources"] = {
            field: "gemini"
            for field, value in values.items()
            if value is not None and field not in {"document_type", "line_items"}
        }
        # Gemini supplies no calibrated field confidence. Do not fabricate Azure OCR scores.
        return ReviewData.model_validate(values)

    def classification(self) -> DocumentClassification:
        return DocumentClassification(
            document_kind=self.document_type,
            confidence=self.classification_confidence,
            reasoning=self.classification_reason,
        )


class GeminiDocumentReviewer:
    def __init__(self, client: GeminiClient) -> None:
        self.client = client

    def review(self, path: Path, content_type: str) -> LlmDocumentExtraction:
        try:
            return self.client.generate(
                LlmDocumentExtraction,
                instructions=EXTRACTION_INSTRUCTIONS,
                prompt="Read the document afresh. Extract its fields and a one-sentence summary.",
                path=path,
            )
        except GeminiError as error:
            raise DocumentReviewError(str(error)) from None


class GeminiGlCategorizer:
    def __init__(self, client: GeminiClient) -> None:
        self.client = client

    def run(self, extraction: ReviewData) -> GlSuggestion:
        return self.client.generate(
            GlSuggestion,
            instructions=GL_CATEGORIZATION_INSTRUCTIONS,
            prompt=json.dumps(build_gl_categorization_input(extraction)),
        )


class GeminiCorrectionEmailDrafter:
    def __init__(self, client: GeminiClient) -> None:
        self.client = client

    def draft(self, data: ReviewData, issues: list[ValidationIssue]) -> CorrectionEmailDraft:
        try:
            return self.client.generate(
                CorrectionEmailDraft,
                instructions=(
                    "Draft a concise professional correction request from Maya, Finance "
                    "Administration, Northstar Facilities B.V. Mention only the supplied business "
                    "issues and facts. Ask for a corrected document or clarification. "
                    "Do not invent an email address or mention AI, confidence or internal systems."
                ),
                prompt=json.dumps(
                    {
                        "document": data.model_dump(mode="json"),
                        "issues": [issue.model_dump(mode="json") for issue in issues],
                    }
                ),
            )
        except GeminiError as error:
            raise CorrectionEmailDraftingError(str(error)) from None
