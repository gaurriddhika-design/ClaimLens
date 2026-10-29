# AVINYA-ClaimLens-AI-powered-online-claim-verification

an interactive web platform for verifying online claims through evidence analysis, source comparison, and credibility assessment

--------------------------------------------------------
# AVINYA-ClaimLens-AI-powered-online-claim-verification
--------------------------------------------------------------
# ClaimLens: AI Verification Engine

an interactive web platform for verifying online claims through evidence analysis, source comparison, and credibility assessment

## Overview

The AI Verification Engine is developed by **Member 3** of the ClaimLens project. It is responsible for processing submitted claims, retrieving relevant online sources, analysing evidence, evaluating source-quality indicators, and generating a verification verdict.

The engine is organized into separate Python modules under the `services/` directory. This modular structure makes the code easier to test, maintain, and integrate with the backend.

## Responsibilities

The verification engine is responsible for:

- **Claim Extraction:** Cleans and prepares user-submitted claims.
- **Web Search:** Searches for relevant sources using the Tavily Search API.
- **Source Fetching:** Retrieves article content and metadata from URLs while applying URL and response safety checks.
- **Evidence Analysis:** Analyses source text for supporting, contradicting, mixed, or insufficient evidence.
- **Source Scoring:** Calculates a heuristic score from observable source-quality indicators.
- **Verdict Generation:** Combines analysed evidence and source-quality information to determine an appropriate verdict.
- **Verification Orchestration:** Coordinates the verification workflow through a single service.

## Directory Structure

```text
services/
├── __init__.py
├── claim_extractor.py
├── search_service.py
├── source_fetcher.py
├── evidence_analyzer.py
├── source_scorer.py
├── verdict_engine.py
└── verification_service.py

tests/
├── __init__.py
├── test_claim_extractor.py
├── test_search_service.py
├── test_source_fetcher.py
├── test_source_scorer.py
├── test_evidence_analyzer.py
├── test_verdict_engine.py
└── test_verification_service.py
```

## Module Descriptions

| Module | Responsibility |
|---|---|
| `claim_extractor.py` | Cleans the submitted claim and removes unnecessary introductory phrases and whitespace. |
| `search_service.py` | Searches for relevant sources, normalizes results, and handles search-related errors. |
| `source_fetcher.py` | Fetches web pages and extracts titles, article text, and available publication dates. |
| `evidence_analyzer.py` | Analyses the relationship between a claim and retrieved source text. |
| `source_scorer.py` | Scores observable source-quality indicators and sorts sources by score. |
| `verdict_engine.py` | Generates a verdict from the analysed evidence and source-quality information. |
| `verification_service.py` | Coordinates the verification workflow across the individual services. |

## Technology Stack

- **Python:** Core implementation language.
- **Requests:** HTTP requests for web search and source retrieval.
- **Beautiful Soup 4:** HTML parsing and content extraction.
- **Pytest:** Automated testing.
- **python-dotenv:** Loading environment variables from a `.env` file when configured in the application.
- **Tavily Search API:** Retrieving relevant web search results.

## Setup Instructions

### 1. Navigate to the project root

```bash
cd ClaimLens
```

Run the following commands from the root directory, where `requirements.txt` is located.

### 2. Activate the virtual environment

On Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

If your virtual environment is stored elsewhere, activate it using its actual path.

### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```

### 4. Configure the API key

Text verification requires the Tavily search provider and API key.

Set these values in the `.env` file in the application's working directory (`backend/.env` when launching from the `backend` directory):

```env
SEARCH_PROVIDER=tavily
SEARCH_API_KEY=your_tavily_api_key
```

For compatibility, `TAVILY_API_KEY` is also accepted when `SEARCH_PROVIDER` is unset. Never commit a real `.env` file to GitHub.

### 5. Run the tests

Run the complete test suite:

```bash
python -m pytest tests backend/tests -q
```

To test individual components:

```bash
python -m pytest tests/test_claim_extractor.py -v
python -m pytest tests/test_search_service.py -v
python -m pytest tests/test_source_fetcher.py -v
python -m pytest tests/test_source_scorer.py -v
python -m pytest tests/test_evidence_analyzer.py -v
python -m pytest tests/test_verdict_engine.py -v
python -m pytest tests/test_verification_service.py -v
```

## Testing Status

The complete test suite passed **151 tests** in the current development environment during this integration change.

The tests cover:

- Claim cleaning and input validation.
- Search result normalization and search errors.
- URL validation, HTML extraction, and network failures.
- Source-quality scoring and score ordering.
- Evidence classification and conflicting signals.
- Verdict generation for different evidence conditions.
- Verification workflow behavior, including fallback to snippets and empty search results.
- FastAPI verification integration, report persistence, provider configuration, and PDF/URL intake behavior.

These results confirm that the tested cases pass. They do not establish that every real-world claim will receive a correct verdict.

## Source-Quality Scoring

The source scorer evaluates observable characteristics such as:

- Presence of an HTTP or HTTPS URL.
- Use of HTTPS.
- Government or educational domain patterns.
- Availability of a page title.
- Availability of a publication date.
- Length of extracted source content.

The resulting score is a **heuristic source-quality indicator, not a probability of truthfulness**.

HTTPS does not guarantee factual accuracy, and an official-looking domain does not guarantee that every page is reliable. Sources and evidence must be assessed in context.

## Verdict Interpretation

The verdict engine handles different evidence conditions, including:

- **Verified:** Sufficient supporting evidence under the implemented rules.
- **False:** Sufficient contradicting evidence under the implemented rules.
- **Partial or mixed:** Evidence contains conflicting or mixed signals.
- **Insufficient evidence:** Available evidence does not justify a confident conclusion.
- **Opinion or not fact-checkable:** The submitted content cannot appropriately be classified as a straightforward factual claim.

The exact verdict values and response fields should remain consistent with the implementation and the backend API contract.

## Backend Integration

Text submissions to `/api/verify` invoke `VerificationService.verify()` through a worker thread, map the engine result to the backend report schema, and persist the report for retrieval by ID. Tavily credentials are passed to the search service without being included in responses or audit events. The health endpoint reports provider configuration separately from whether the engine integration is wired.

PDF and URL endpoints currently perform validated intake and persist intake-only reports; they do not invoke the verification engine. Engine verdicts use lexical heuristics, are not definitive fact-checks, and require human review. Unknown engine verdict labels conservatively map to `UNVERIFIED`.

## Current Limitations

- Evidence analysis currently relies on implemented rules and textual signals rather than a fully validated semantic fact-checking model.
- Source-quality scores are heuristic indicators and cannot establish whether a claim is true.
- Search results and article extraction depend on source availability and website structure.
- The engine's unit tests do not replace end-to-end testing of the frontend, backend, verification engine, and report storage.
- URL validation and redirect restrictions reduce certain risks but should not be considered complete protection against server-side request forgery (SSRF).

## Future Improvements

- Improve evidence analysis using semantic similarity or natural language inference.
- Evaluate verdict quality against a labelled set of real-world claims and evidence.
- Improve source independence and duplicate-source detection.
- Strengthen URL-fetching security and validation.
- Integrate PDF and URL workflows with the engine after defining suitable validation and failure handling.
- Improve reporting of evidence, source metadata, and uncertainty.

## Developer

**Role:** Member 3 – AI Verification Engine
**Project:** ClaimLens
**Branch:** `feature`
