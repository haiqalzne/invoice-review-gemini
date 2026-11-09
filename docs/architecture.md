# Target architecture

> **Local Gemini adaptation — 9 November 2026:** This workspace now supports `AI_PROVIDER=gemini` (the default). One Gemini request classifies and extracts into provider-independent `ReviewData`; a second source reading fills missing fields and exposes differences; a third request suggests a catalog account. Both readings use the same model, not independent Azure services. Python validation, human decisions and SQLite remain unchanged. Field provenance records `gemini`, `gemini_review`, or `human`; unavailable field confidence stays empty. `DocumentReview.primary_provider` and `review_provider` select truthful labels for saved records. The legacy comparison key `document_intelligence_value` is retained for record compatibility and represents the first reading; its displayed label follows provider metadata. The sections below describe the preserved original Azure architecture.

Invoice Review is a small local full-stack application. Maya uploads a multilingual invoice or receipt, reviews a prepared extraction with policy findings and a GL suggestion, corrects fields when needed, then approves or rejects.

## Intended boundaries

- Provider adapters normalize Azure responses before data reaches the domain (`providers/` and thin `services/` clients).
- Deterministic invoice and receipt rules remain separate from model extraction (`documents/validation.py`).
- Routes own HTTP concerns, a service owns orchestration, and a repository owns SQLite access under `documents/`.
- The ordered Azure workflow lives in `pipeline/` steps (classify → extract → LLM review/merge → validate → GL).
- Environment values are read through one backend settings module and one frontend environment module.
- A person approves, rejects, or requests a supplier correction after seeing evidence and uncertainty.

## Target flow

```mermaid
flowchart LR
    user[Finance administrator] --> ui[React review UI]
    ui --> api[FastAPI]
    api --> pipeline[Pipeline steps]
    pipeline --> providers[Azure provider adapters]
    providers --> reviewData[ReviewData projection]
    reviewData --> rules[Deterministic finance rules]
    rules --> db[(SQLite)]
    db --> ui
```

## Persistence shape

Stage columns keep the teaching story visible (`classification`, `extraction`, `validation`, `gl_suggestion`). The editable review projection is stored as `review_data`, with `document_review`, `accounting_coding`, and `issues` for Maya’s decision loop.
