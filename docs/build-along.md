# Build-along guide

## Gemini learning path

Use the [README quick start](../README.md#quick-start) to install and run this fork. The `gemini` branch contains working application code. The original Azure tutorial sequence is preserved later in this document as historical reference; its provider scripts require Azure credentials and are not the Gemini setup path.

### Pass 1 — see the complete flow

1. Start the backend and frontend, open `http://localhost:5173`, and upload the fictional `02-nl-happy-compact.pdf` from `samples/generated/`.
2. Check the source preview. Processing sends the file to Gemini and consumes up to three requests.
3. Inspect supplier, invoice number, totals, validation issues and the suggested general-ledger (GL) account. GL means the bookkeeping category; the catalog is ordinary application data.
4. Before approving, change invoice total to `999.00` and save. Expect `invoice_total_mismatch` and approval to be blocked. Restore `290.40`; expect the issue to clear and the value to be marked as a human correction.
5. Approve the review, open History and reload the page. The decision should remain stored. A decided document cannot be edited.

Expected arithmetic for this sample: subtotal `240.00` + tax `50.40` = total `290.40`, all EUR. Cleaning services (`6100`) is the expected category suggestion, but model output still needs review. To repeat a clean run of the identical invoice, delete only your disposable example through History or select a different sample; duplicate detection is intentional.

**Checkpoint:** describe where AI contributes, which rules Python enforces, which decision a human makes and what survives a page reload.

### Pass 2 — follow one record through the code

| Question | Inspect |
| --- | --- |
| What does the user send? | `frontend/src/lib/api.ts` and `backend/app/documents/routes.py` |
| Where are secrets and provider choices read? | `backend/app/config.py` |
| What shape must extracted data have? | `backend/app/documents/schemas.py` and `backend/app/providers/gemini_documents.py` |
| What order does processing follow? | `backend/app/pipeline/__init__.py` and `base.py` |
| Where does the external request happen? | `backend/app/providers/gemini.py` |
| How are differences and missing fields handled? | `backend/app/document_review/reconciliation.py` |
| Who checks VAT and arithmetic? | `backend/app/documents/validation.py` |
| Where is the decision saved? | `backend/app/documents/service.py`, `repository.py` and `models.py` |
| How does it reach the screen? | `frontend/src/components/DocumentReview.tsx` |

The API uses JSON (structured data), Python validates it with Pydantic schemas, and SQLite retains local records. `Decimal` represents amounts without ordinary binary floating-point rounding. `field_sources` distinguishes the first Gemini reading, a fallback from its second reading and a human edit.

The legacy comparison property `document_intelligence_value` means the primary reading for stored-record compatibility. Provider metadata determines the visible label. Neither two agreeing readings nor a model's self-rated category confidence proves correctness.

**Checkpoint:** trace `invoice_total` from source → Gemini output → `ReviewData` → reconciliation → Python check → SQLite → screen. Explain why changing the AI provider does not change the arithmetic rule.

### Pass 3 — predict, change and debug

Use these cases one at a time; each new processed document consumes quota.

| Exercise | Expected learning |
| --- | --- |
| `05-nl-missing-vendor-vat.pdf` | A required value can be missing even when JSON is valid. |
| `08-en-total-mismatch.pdf` | Extract the wrong source total faithfully; flag it instead of silently repairing it. |
| Process the same invoice twice | The service/repository supplies duplicate evidence that a standalone model cannot know. |
| Correct a field and rerun checks | A human edit changes provenance and revalidates without another model call. |
| Select a different valid GL account | The model suggests; the catalog constrains choices; the human decides. |

For errors that the supplier can fix, generate an optional correction draft and inspect its wording. This adds one Gemini request. Copying a draft does not send it; the application contains no email-sending integration.

**Checkpoint:** explain a failure using evidence from the source, normalized data and rule code. Distinguish extraction mistakes from policy failures and provider outages.

### Pass 4 — make and explain one independent change

Choose one small change, such as clarifying an issue message or adding a well-specified local policy rule. Write an acceptance example first. Identify the responsible module, implement the change, run the documented checks, then exercise both the changed case and an unaffected case. Keep the fixed GL catalog and the model prompt consistent if you change categories.

Do not treat a successful demonstration as mastery. The goal is being able to explain, modify, verify and troubleshoot the system independently.

## Configuration, usage and troubleshooting

- **Missing key:** set your own `GEMINI_API_KEY` in `backend/.env`. Never paste it into the frontend, README, logs or an issue.
- **403/access blocked:** inspect the key's project and any free-tier verification requirement in AI Studio.
- **429/rate limit:** wait and retry manually after checking project limits. The app has no automatic retries or billing upgrades.
- **Model unavailable:** check current model availability and free-tier eligibility, then update `GEMINI_MODEL` deliberately.
- **Wrong local URL:** use `http://localhost:5173` for the UI and port `8000` for the API. A different origin may require updating `ALLOWED_ORIGIN`.
- **Port in use:** close the earlier instance before starting another; do not run two backends against the same learning database.
- **Cloud-only project files:** if imports/builds hang in a synced folder, ensure dependencies are downloaded locally. Restore only the existing locked versions; do not mistake a cloud-only Git file for damaged history.
- **Azure-specific examples:** the older provider checks and corpus evaluators below still use Azure. Use the README's Gemini app flow or `playground/run_pipeline.py` for this fork.

Normal processing uses three requests (combined classification/extraction, fresh source reading, GL suggestion); the optional email draft adds one. Output is capped at 8,192 tokens per request and requests time out after 90 seconds. Failed calls can still consume quota. Current pricing and quotas belong to Google, not this repository.

## Verification evidence and limits

Verified on 9 November 2026: backend Ruff; frontend TypeScript, ESLint and production build; one live fictional PDF extracted to EUR `290.40` and GL `6100`; local corrections; invalid-total approval rejection (HTTP 409); one unsent Gemini correction draft; and browser approval/history. Offline checks covered missing keys, safe quota errors, malformed structured output, receipt mapping/arithmetic, unavailable confidence, conflict preservation and fallback provenance.

The browser automation file-chooser check timed out; direct multipart upload and the saved-review UI were verified. Confirm the native file picker manually on your machine. The complete multilingual corpus has not been benchmarked against Gemini. No independent learner assessment is implied by these setup checks.

Publication preparation on 10 November 2026: added the public quick start, diagram, screenshot and learning exercises; adapted `playground/run_pipeline.py` to Gemini ReviewData and explicit document MIME types; and removed three legacy playground lint findings. Backend/playground Ruff and an offline command-line check passed. The offline check verifies the default fixture, JSON output and full-review MIME configuration without calling a model. No key, runtime database, uploaded user file, virtual environment or dependency directory is distributed. See the repository history for the changes.

## Historical Azure build sequence

The sections below preserve upstream's original build stages. Their starter descriptions and unchecked boxes describe that tutorial's progression, not the state of this completed Gemini fork. For current installation and startup, use the README above.

## Starter outcome

The repository installs reproducibly, starts a minimal FastAPI service and React interface, and includes the business brief plus fictional source documents.

## Why this boundary exists

The starter removes the completed workflow while preserving every prerequisite needed to build it. You begin with the user, the source documents, and explicit service boundaries instead of reverse-engineering a finished application.

## Commands

```bash
cd backend
uv sync --locked

cd ../frontend
pnpm install --frozen-lockfile

cd ..
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
# Historical starter checkpoint; current dev.sh has no --check mode.
./scripts/dev.sh
```

## Important locations

- `docs/client-brief.md`: the recurring finance problem and definition of done
- `docs/architecture.md`: the intended boundaries and data flow
- `samples/`: the fictional evaluation corpus and manifest
- `backend/app/main.py`: the initial API boundary
- `frontend/src/App.tsx`: the initial interface boundary

## What you should observe

- `GET http://localhost:8000/health` returns `{"status":"ok"}`.
- `http://localhost:5173` shows the Invoice Review starter screen.
- No Azure request occurs at this checkpoint.

## Checkpoint

- [ ] Locked backend and frontend installs succeed.
- [ ] Backend lint passes.
- [ ] Frontend type-check, lint, and production build pass.
- [ ] `# Historical starter checkpoint; current dev.sh has no --check mode.` reports that Invoice Review is ready to start.
- [ ] The health endpoint and starter screen load locally.

Continue with the [online tutorial](https://learn.datalumina.com/docs/invoice-review).

## Classify uploads before extraction

### Outcome

A pipeline step classifies an unknown PDF or image as `invoice` or `receipt` using Azure OpenAI structured output through Pydantic AI. The result is a typed `DocumentClassification` model you can use to route to `prebuilt-invoice` or `prebuilt-receipt`.

### Why this boundary exists

Document Intelligence has separate extraction models but no reliable prebuilt classifier for invoice vs receipt. Classification happens first with Azure OpenAI on the original document bytes; extraction stays in Document Intelligence afterward.

### Commands

```bash
cd backend
uv sync --locked
uv run --locked --no-sync ruff check app/pipeline

cd ../playground
uv run --project ../backend --locked --no-sync python classify_sample_document.py
uv run --project ../backend --locked --no-sync python classify_sample_document.py ../samples/generated/13-nl-fuel-receipt.png
```

### Important locations

- `backend/app/pipeline/classification.py`: `DocumentClassification` schema and `DocumentClassifier.run()`
- `backend/app/services/azure_openai_service.py`: shared Azure OpenAI settings and deployment name
- `playground/classify_sample_document.py`: manual classifier check against sample documents

### What you should observe

- The sample invoice PDF returns `"document_kind": "invoice"`.
- The Dutch fuel receipt PNG returns `"document_kind": "receipt"`.
- Each response includes a confidence score and short reasoning string.
- This step consumes one Azure OpenAI Responses API call per document.

### Checkpoint

- [ ] `pydantic-ai-slim[openai]` is pinned in `backend/pyproject.toml` and `backend/uv.lock`.
- [ ] Backend lint passes for `app/pipeline`.
- [ ] The playground script classifies the invoice PDF and receipt PNG correctly.
- [ ] You can explain why classification precedes Document Intelligence extraction.

## Chain classify → extract → validate

### Outcome

A typed pipeline chains three steps: classify the upload, call the matching Document Intelligence model (`prebuilt-invoice` or `prebuilt-receipt`), map into Pydantic extraction models, then run offline EU VAT format checks and totals reconciliation. Each step reads and writes a shared `PipelineContext`.

### Why this boundary exists

Azure calls and deterministic finance rules must stay separable. The pipeline only sequences steps; Document Intelligence SDK types are converted to domain models inside the extraction step; VAT and totals live in pure functions under `app/documents/validation.py` so later approval policy can reuse them without calling Azure.

### Commands

```bash
cd backend
uv run --locked --no-sync ruff check app/pipeline app/documents

cd ../playground
uv run --project ../backend --locked --no-sync python run_pipeline.py
uv run --project ../backend --locked --no-sync python run_pipeline.py ../samples/generated/13-nl-fuel-receipt.png
```

### Important locations

- `backend/app/pipeline/base.py`: `PipelineContext`, `PipelineStep`, and `Pipeline`
- `backend/app/pipeline/classification.py`: `ClassificationStep`
- `backend/app/pipeline/extraction.py`: routes invoice vs receipt and maps to Pydantic models
- `backend/app/pipeline/validation.py`: attaches VAT and totals findings to the context
- `backend/app/documents/validation.py`: pure `validate_eu_vat` and `reconcile_totals` helpers
- `playground/run_pipeline.py`: end-to-end manual check

### What you should observe

- The sample invoice classifies as `invoice`, extracts supplier/customer/VAT/dates/PO/totals/line items, and reports VAT/totals findings.
- The Dutch fuel receipt classifies as `receipt`, extracts merchant/transaction/totals via `prebuilt-receipt`, and reconciles receipt totals when amounts are present.
- Invalid present VAT IDs become `vat_invalid` errors; missing amounts become `totals_incomplete` info findings, not silent failures.
- This flow consumes one Azure OpenAI classification call plus one Document Intelligence analyze call per document.

### Checkpoint

- [ ] Backend lint passes for `app/pipeline` and `app/documents`.
- [ ] `run_pipeline.py` routes the invoice PDF and receipt PNG to the correct DI model.
- [ ] Extraction summaries show the core financial fields needed for downstream review.
- [ ] You can explain why validation is pure Python and not part of the Azure adapters.

## Suggest a Northstar GL account

### Outcome

A fourth pipeline step suggests one GL account from a fixed 10-account Northstar catalog using Azure OpenAI structured output through Pydantic AI. The categorizer receives normalized extraction fields for both invoices and receipts and writes a typed `GlSuggestion` onto the shared `PipelineContext`.

### Why this boundary exists

The model may suggest an account, but the catalog owns business policy. Keeping the fixed GL list in `app/accounting/` and the Azure call in `app/pipeline/gl_categorization.py` makes that separation explicit. The categorizer reads extracted fields only, not the original document bytes, so it stays independent from classification and Document Intelligence.

### Commands

```bash
cd backend
uv run --locked --no-sync ruff check app/pipeline app/accounting app/documents

cd ../playground
uv run --project ../backend --locked --no-sync python run_pipeline.py
uv run --project ../backend --locked --no-sync python run_pipeline.py ../samples/generated/13-nl-fuel-receipt.png
```

### Important locations

- `backend/app/accounting/catalog.py`: `GlAccountCode`, `NORTHSTAR_GL_CATALOG`, and prompt formatting
- `backend/app/pipeline/gl_categorization.py`: `GlSuggestion`, `GlCategorizer.run()`, and `GlCategorizationStep`
- `backend/app/pipeline/base.py`: `gl_suggestion` on `PipelineContext`
- `backend/app/pipeline/__init__.py`: registers the step in `build_default_pipeline()`
- `playground/run_pipeline.py`: includes `gl_suggestion` in the JSON output

### What you should observe

- The sample invoice JSON includes `"gl_suggestion"` with `account_code`, `confidence`, and `reasoning`.
- A cleaning-services invoice should suggest `6100`; a fuel receipt should suggest `6170`.
- The suggested code is always one of the ten catalog values (`6100`–`6190`).
- This flow consumes two Azure OpenAI Responses API calls per document: classification and GL suggestion.

### Checkpoint

- [ ] Backend lint passes for `app/pipeline`, `app/accounting`, and `app/documents`.
- [ ] `run_pipeline.py` prints `gl_suggestion` for the invoice PDF and receipt PNG.
- [ ] You can explain why the catalog lives outside the model adapter and why receipts are included.
- [ ] You can explain why GL suggestion runs after extraction and uses normalized fields only.

## Expose the pipeline through FastAPI

### Outcome

A thin HTTP and SQLite layer wraps the proven `build_default_pipeline()` flow. Upload a PDF or image, persist classification, extraction, validation, and GL suggestion, list saved reviews, delete a review, and read the fixed Northstar GL catalog — without corrections, decisions, or correction-email drafts yet.

### Why this boundary exists

Routes own HTTP parsing and status codes. The service owns orchestration (save file → run pipeline → map status). The repository owns SQLite. Persistence and HTTP now wrap known pipeline behavior instead of becoming the place where extraction and policy are invented.

### Commands

```bash
cd backend
uv run --locked --no-sync ruff check app
uv run --locked --no-sync uvicorn app.main:create_app --factory --reload
```

In a second terminal from the repo root:

```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/accounting/gl-accounts
curl -F \
  "file=@samples/generated/02-nl-happy-compact.pdf;type=application/pdf" \
  http://localhost:8000/api/documents
curl http://localhost:8000/api/documents
```

### Important locations

- `backend/app/main.py`: FastAPI factory, CORS, `/health`
- `backend/app/config.py`: fixed upload/DB/CORS application config
- `backend/app/database.py`: SQLAlchemy engine and session factory
- `backend/app/documents/routes.py`: upload, list, and delete
- `backend/app/documents/service.py`: calls `build_default_pipeline()`
- `backend/app/documents/repository.py` and `models.py`: SQLite persistence
- `backend/app/accounting/routes.py`: `GET /api/accounting/gl-accounts`

### What you should observe

- `GET /health` returns `{"status":"ok"}`.
- `GET /api/accounting/gl-accounts` returns the ten Northstar accounts (`6100`–`6190`).
- One multipart upload returns a persisted review with `classification`, `extraction`, `validation`, and `gl_suggestion`.
- Status is `needs_review` when validation has errors, otherwise `ready`; pipeline failures become `failed` with `502`.
- Oversized (>4 MB) or non-PDF/JPEG/PNG uploads are rejected before Azure is called.
- `DELETE /api/documents/{id}` removes the SQLite row and the local upload file.

### Checkpoint

- [ ] Backend lint passes for `app`.
- [ ] Health, GL catalog, upload, and list work with curl against a running uvicorn process.
- [ ] You can explain why routes, service, and repository stay separate from the pipeline steps.
- [ ] You can explain why corrections, decisions, and correction-email are deferred until later.

## Scaffold the welcome → upload → pipeline UI

### Outcome

The React app boots with a Northstar welcome screen. Maya can choose a PDF/JPEG/PNG, preview it locally, start processing, and see the development pipeline result (`classification`, `extraction`, `validation`, `gl_suggestion`). History lists and deletes saved reviews through the existing FastAPI routes. Field editing, approve/reject, and correction-email remain deferred.

### Why this boundary exists

The frontend stays a thin workflow shell: `env.ts` owns `VITE_API_BASE_URL`, `api.ts` owns `fetch`/`FormData`, and components consume application types that mirror the current `DocumentResponse`. Processing progress is local UI only; the real work is one blocking `POST /api/documents` that already runs `build_default_pipeline()`.

### Commands

```bash
cd frontend
cp .env.example .env
pnpm install --frozen-lockfile
pnpm exec tsc -b --pretty false
pnpm lint
pnpm build
pnpm dev
```

In a second terminal, keep the API running:

```bash
cd backend
uv run --locked --no-sync uvicorn app.main:create_app --factory --reload
```

Open `http://localhost:5173`, choose a sample under `samples/generated/`, and click **Process document**.

### Important locations

- `frontend/index.html`, `frontend/src/main.tsx`, `frontend/src/App.tsx`: Vite entry and view machine (`welcome` → `upload` → `processing` → `result` / `history`)
- `frontend/src/lib/env.ts`, `api.ts`, `types.ts`: environment boundary and typed HTTP client for development responses
- `frontend/src/components/WelcomePortal.tsx`, `UploadStep.tsx`, `ProcessingStep.tsx`: welcome, dropzone/preview, and staged progress copy
- `frontend/src/components/PipelineResult.tsx`, `DocumentInbox.tsx`: read-only pipeline summary and history list/delete

### What you should observe

- The welcome screen offers **Review a document** and **View history**.
- Upload accepts PDF/JPEG/PNG up to 4 MB, shows a local preview, and does not call Azure until **Process document**.
- Process switches to the processing view, then lands on a result that shows classification, extraction highlights, validation findings, and the GL suggestion.
- Failed uploads return to the upload step with the API error message (`413`, `415`, `502`, and so on).
- History loads `GET /api/documents` and can delete with `DELETE /api/documents/{id}`.

### Checkpoint

- [ ] Frontend type-check, lint, and production build pass.
- [ ] With the API running, you can upload a sample and see a persisted pipeline result in the browser.
- [ ] You can explain why the UI types follow development `DocumentResponse` instead of the solution’s flattened review model.
- [ ] You can explain why corrections, decisions, and correction-email stay out of this slice.

## Close the Maya review loop

### Outcome

Maya can upload a sample, inspect the prepared review, correct fields, confirm a Northstar GL account, approve or reject, and draft a supplier correction email when supplier-fixable issues exist. Document Intelligence stays primary; an independent Azure OpenAI review fills gaps and exposes provenance. Northstar policy issue codes match `samples/manifest.json`.

### Why this boundary exists

The cleaner `documents/` + `pipeline/` layout stays intact. Solution behavior is ported as:

- a flat `ReviewData` projection for policy and edits
- pure validation that emits manifest issue codes
- review APIs under `/api/documents`
- LLM merge in `document_review/` + a pipeline step
- correction-email eligibility as a small pure package

Stage JSON columns remain for teaching; the interactive UI reads `review_data`, `issues`, `document_review`, and `accounting_coding`.

### Commands

```bash
# Backend
cd backend
rm -f data/documents.db   # recreate schema after model changes
uv run --locked --no-sync ruff check app scripts
uv run --locked --no-sync uvicorn app.main:create_app --factory --reload

# Optional live corpus checks (Azure usage)
uv run --locked --no-sync python scripts/evaluate_corpus.py
uv run --locked --no-sync python scripts/evaluate_hybrid.py

# Frontend
cd frontend
pnpm exec tsc -b --pretty false
pnpm lint
pnpm build
pnpm dev
```

Manual demo set: `02-nl-happy-compact.pdf` (approve), `06-de-invalid-vendor-vat.pdf` (edit or reject), `08-en-total-mismatch.pdf` (totals error), `13-nl-fuel-receipt.png` (receipt), and `10-de-duplicate.pdf` after `03-de-happy-modern.pdf` (duplicate).

### Important locations

- `backend/app/documents/validation.py`, `projection.py`, `schemas.py`, `service.py`, `routes.py`
- `backend/app/pipeline/document_review.py`, `validation.py`
- `backend/app/document_review/reconciliation.py`
- `backend/app/correction_email/`
- `backend/app/providers/azure_openai_document_review.py`, `azure_openai_correction_email.py`
- `frontend/src/components/DocumentReview.tsx`, `DocumentReviewSection.tsx`, `CorrectionEmailDialog.tsx`
- `frontend/src/lib/api.ts`, `types.ts`, `review-outcome.ts`

### What you should observe

- Happy-path samples land as `ready` with empty issue lists (PO present).
- Sample `05` reports `vendor_vat_id_required`; `06` reports `vendor_vat_id_invalid`; `07` reports `customer_vat_id_mismatch`; `08` reports `invoice_total_mismatch`; `09` reports warning `purchase_order_missing` but stays `ready`.
- Saving field corrections re-runs policy and can clear errors.
- Approve requires a selected GL and no error issues; decided reviews lock editing.
- Rejected reviews with supplier-fixable issues can open a Copy/Close correction-email draft.

### Checkpoint

- [ ] Backend lint passes for `app` and `scripts`.
- [ ] Frontend type-check, lint, and production build pass.
- [ ] You can approve a clean sample and reject a broken one in the browser.
- [ ] You can explain why Document Intelligence remains primary over the LLM fallback.
- [ ] Corpus evaluator field accuracy is high and policy codes match the manifest (except duplicate, which needs a peer in SQLite).

## Deploy a single container to Azure

### Outcome

The FastAPI API and React SPA run as one container in Azure Container Apps inside `rg-invoice-review`, with SQLite/uploads on Azure Files and a shared-password login gate so a public URL cannot freely burn Azure quota.

### Why this boundary exists

Local development stays two processes (`./scripts/dev.sh`). Production collapses to one origin so cookies and relative API calls stay simple. Auth is one shared password plus an HMAC session cookie — not accounts or Entra for the app itself. Provider calls still use API keys from Container App secrets.

### Commands

See [azure-deploy.md](azure-deploy.md) for the full `az` sequence. Summary:

```bash
# Confirm context
az account show
az group show --name rg-invoice-review

# Build image in ACR, create Files share + Container Apps env/app
# (exact resource names and secret wiring are in azure-deploy.md)

# Local verification before/without Azure
cd backend && uv run --locked --no-sync ruff check app scripts
cd ../frontend && pnpm exec tsc -b --pretty false && pnpm lint && VITE_API_BASE_URL=/ pnpm build
```

### Important locations

- `Dockerfile`, `.dockerignore`
- `backend/app/main.py` (static SPA + password middleware)
- `backend/app/auth/`
- `backend/app/config.py` (`APP_ACCESS_PASSWORD`, `APP_SESSION_SECRET`, `ALLOWED_ORIGIN`, `FRONTEND_DIST_DIR`)
- `frontend/src/components/LoginPage.tsx`, `frontend/src/App.tsx`, `frontend/src/lib/api.ts`, `frontend/src/lib/env.ts`
- `docs/azure-deploy.md`

### What you should observe

- `GET /health` returns `{"status":"ok"}` without a cookie.
- `GET /api/documents` returns `401` until you sign in with the shared password.
- After login, the familiar upload → process → review flow works on the Container App HTTPS URL.
- Restarting the Container App revision does not wipe SQLite/uploads when `/app/data` is mounted from Azure Files.

### Checkpoint

- [ ] Backend lint and frontend type-check/lint/build pass.
- [ ] Container image builds (`az acr build` or local Docker).
- [ ] Deployed `/health` is open; API is gated; browser login unlocks a sample upload.
- [ ] You can tear down hosting resources without deleting the whole resource group.
