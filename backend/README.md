# ClaimLens Backend

ClaimLens accepts text, selectable-text PDFs, and URLs for claim-verification workflows. The backend currently implements input ingestion, validation, report persistence, and report retrieval.

**Current limitation:** Reports are intake records, not completed factual verifications. The AI verification engine, live evidence retrieval, claim-level analysis, and verdict generation are not integrated yet.

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Service and configuration status |
| POST | `/api/demo` | Return a static demo report |
| POST | `/api/verify` | Accept text submitted as JSON |
| POST | `/api/verify/pdf` | Accept a PDF file upload |
| POST | `/api/verify/url` | Fetch and extract text from a URL |
| GET | `/api/reports/{report_id}` | Retrieve a previously saved report |

## Request Examples

### Text verification intake

`POST /api/verify`

```json
{
  "text": "The Earth orbits the Sun."
}
```

### URL verification intake

`POST /api/verify/url`

```json
{
  "url": "https://example.com/article"
}
```

For PDF ingestion, submit a multipart form upload using the field name `file`.

Successful ingestion requests save a report and return its ID. Use that ID with `GET /api/reports/{report_id}` to retrieve the saved report. A completed intake operation does not mean the submitted claims have been fact-checked.

## Setup — Windows PowerShell

Run these commands from the repository root:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r .\backend\requirements.txt
cd .\backend
python -m uvicorn app.main:app --reload
```

If the virtual environment is already active, skip the activation command.

Open `http://127.0.0.1:8000/docs` to explore and test the API.

## Database and Persistence

The default development database URL is:

`sqlite+aiosqlite:///./claimlens.db`

The relative database path depends on the process working directory. Starting the server from the `backend` directory normally creates or uses `backend/claimlens.db`.

Reports are persisted using SQLAlchemy's asynchronous database support. Tables are created at application startup for this prototype. A migration tool such as Alembic should be introduced before production schema changes.

**Do not commit local database files or environment secrets to Git.**

## Running Tests

From the repository root, with the virtual environment activated:

```powershell
python -m pytest .\backend\tests -q
```

## Input Limits and Security

The backend configuration includes limits for upload size, PDF page count, input text length, URL response size, and request timeouts.

- PDF uploads are validated and checked against page-count and extracted-text limits.
- URL ingestion restricts protocols, rejects credentials and localhost names, checks resolved IP addresses, revalidates redirects, limits redirects, and bounds streamed response size.
- URL text extraction is heuristic and is not a full article-quality extraction algorithm.
- OCR for scanned PDFs is not implemented.
- URL validation reduces server-side request forgery (SSRF) risk, but additional protections are required before production deployment. DNS rebinding and changes in network resolution require defense-in-depth, such as outbound network restrictions or connection-level destination enforcement.

## Integration Boundary

This backend provides the ingestion and persistence foundation for the next integration stage. The AI verification engine and its evidence retrieval, claim-level analysis, and verdict generation must be integrated separately.

Until that integration is complete, reports must not be presented as fact-checked results.