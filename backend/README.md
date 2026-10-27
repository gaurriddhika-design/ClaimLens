# ClaimLens Backend

ClaimLens accepts text, selectable-text PDFs, and URLs. Text verification invokes the Member 3 search and lexical-analysis engine; PDF and URL requests currently validate and persist intake reports only.

**Important limitation:** Engine verdicts are heuristic results, not definitive fact-checks. Human review of source authority, context, and corroboration is required.

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

### Text verification

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

Successful text verification saves a report and returns its ID. PDF and URL intake requests also save reports, but do not invoke the verification engine. Use the ID with `GET /api/reports/{report_id}` to retrieve the saved report.

## Setup — Windows PowerShell

Run these commands from the repository root:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r .\backend\requirements.txt
cd .\backend
python -m uvicorn backend.app.main:app --app-dir .. --reload
```

If the virtual environment is already active, skip the activation command.

Text verification requires the Tavily provider and API key. Set `SEARCH_PROVIDER=tavily` and `SEARCH_API_KEY` in the local, ignored `.env` file. For compatibility, `TAVILY_API_KEY` is also accepted when `SEARCH_PROVIDER` is unset. Provider credentials are never included in API responses or report audit events.

Open `http://127.0.0.1:8000/docs` to explore and test the API.

## Database and Persistence

The default development database URL is:

`sqlite+aiosqlite:///./claimlens.db`

The relative database path depends on the process working directory. Starting the server from the `backend` directory normally creates or uses `backend/claimlens.db`.

PostgreSQL connection URLs using `postgres://` or `postgresql://` are normalized to the asyncpg driver. `sslmode=require` is translated to asyncpg's `ssl=require`, and `channel_binding` is removed because asyncpg does not support that parameter. Other `sslmode` values, including `verify-ca` and `verify-full`, are rejected rather than silently changing their TLS behavior. Set `DATABASE_URL` in the local, ignored `.env` file; never put credentials in tracked files.

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

## Verification Limitations

The verification engine uses basic lexical heuristics for evidence analysis. Source-quality indicators are not truth probabilities, and search ranking scores are not treated as evidence of truth. Unknown engine verdict labels conservatively map to `UNVERIFIED`. Fetch failures may leave only weaker search-snippet evidence.

PDF and URL ingestion remain intake-only. Reports from those endpoints must not be presented as verified results.