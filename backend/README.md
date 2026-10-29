# ClaimLens Backend

FastAPI backend integrating text, PDF, and URL submissions with the ClaimLens verification engine and persistent reports.

## Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Service and integration status |
| POST | `/api/demo` | Static demo report; does not verify a claim |
| POST | `/api/verify` | Verify submitted text |
| POST | `/api/verify/pdf` | Extract PDF text and verify it |
| POST | `/api/verify/url` | Extract URL text and verify it |
| GET | `/api/reports/{report_id}` | Retrieve a saved report |

Scanned PDFs requiring OCR are not supported by the current ingestion flow.

## Requirements and configuration

Use the repository virtual environment and install dependencies from the repository root:

```powershell
.\.venv\Scripts\python.exe -m pip install -r .\backend\requirements.txt
```

Create `backend/.env` locally. Never commit credentials. Example:

```dotenv
DATABASE_URL=sqlite+aiosqlite:///./claimlens.db
SEARCH_PROVIDER=tavily
TAVILY_API_KEY=your_tavily_api_key
```

Check `backend/app/core/config.py` for exact environment-variable precedence. A valid Tavily configuration is required for live verification. The relative SQLite path depends on the server working directory.

## Start the API

From the repository root:

```powershell
Set-Location .\backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

## Example requests

Text: `POST /api/verify`, JSON body:

```json
{
  "text": "The Earth orbits the Sun."
}
```

URL: `POST /api/verify/url`, JSON body:

```json
{
  "url": "https://example.com/article"
}
```

PDF: `POST /api/verify/pdf` using `multipart/form-data` with the upload field named `file`.

Use the returned report ID with `GET /api/reports/{report_id}`.

## Verification flow

The API validates and ingests input, calls the Member 3 verification engine, maps its output into the API report schema, and persists the report. The engine cleans the claim, searches Tavily, retrieves source pages or falls back to search snippets, analyzes evidence using lexical heuristics, scores observable source-quality indicators, and generates a cautious verdict.

**Verdicts are heuristic assessments, not definitive fact-checks.** Source scores are not probabilities of truth; human review and independent corroboration are necessary.

## Frontend integration

- Local API base URL: `http://127.0.0.1:8000`.
- Send JSON for text and URL requests.
- Send PDF files as multipart form data; let the HTTP client set the multipart boundary.
- Handle non-2xx responses, including validation failures, unavailable search configuration, and upstream search failures.
- Use the report response's verdict, evidence, confidence, and limitations fields rather than inventing client-side results.
- Confirm exact response fields in `backend/app/schemas/` and `/docs`.
- Local CORS origins are configured in `backend/app/core/config.py`.

## Persistence

SQLAlchemy's async database layer stores reports. The prototype creates tables at application startup; introduce managed migrations such as Alembic before production schema changes. PostgreSQL URLs are normalized for asyncpg compatibility in `backend/app/storage/database.py`.


## Tests

Run from the repository root. The isolated SQLite URL prevents tests from depending on Neon:

```powershell
# Save existing environment values.
$oldPythonPath = $env:PYTHONPATH
$oldDatabaseUrl = $env:DATABASE_URL

try {
    $env:PYTHONPATH = (Get-Location).Path
    $env:DATABASE_URL = "sqlite+aiosqlite:///./claimlens_test.db"

    Push-Location .\backend
    try {
        ..\.venv\Scripts\python.exe -m pytest -q
        $testExit = $LASTEXITCODE
    }
    finally {
        Pop-Location
    }

    if ($testExit -ne 0) {
        throw "Backend tests failed with exit code $testExit."
    }
}
finally {
    # Restore the original environment values.
    if ($null -eq $oldPythonPath) {
        Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue
    } else {
        $env:PYTHONPATH = $oldPythonPath
    }

    if ($null -eq $oldDatabaseUrl) {
        Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
    } else {
        $env:DATABASE_URL = $oldDatabaseUrl
    }
}
```


## Security and limitations

- Input size, PDF page count, text length, and request time are bounded by backend settings.
- URL protections reduce SSRF risk but need defense-in-depth, including network-level egress restrictions, before production deployment.
- Source extraction and evidence matching are heuristic; fetched text may be incomplete or misleading.
- Failed page fetches can leave only weaker search-snippet evidence.
- Authentication, rate limiting, operational monitoring, and production deployment hardening remain separate production-readiness tasks.
