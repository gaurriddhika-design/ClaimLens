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

The search service requires a Tavily API key.

Create a `.env` file in the project root:

```env
TAVILY_API_KEY=your_tavily_api_key
```

Replace the placeholder with your own API key. Never commit the real `.env` file to GitHub.

Ensure the application loads environment variables before using the search service, if this is not already handled by the implementation.

### 5. Run the tests

Run the complete test suite:

```bash
python -m pytest tests/ -v
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

The complete test suite has successfully passed **107 tests** in the current development environment.

The tests cover:

- Claim cleaning and input validation.
- Search result normalization and search errors.
- URL validation, HTML extraction, and network failures.
- Source-quality scoring and score ordering.
- Evidence classification and conflicting signals.
- Verdict generation for different evidence conditions.
- Verification workflow behavior, including fallback to snippets and empty search results.

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

The verification engine is intended to integrate with the ClaimLens backend.

The backend integration should define:

- The method used to invoke `VerificationService.verify()`.
- The request format for submitted claims.
- The response schema for verdicts, evidence, and source information.
- Error handling between the backend and verification engine.
- Report persistence and retrieval using report IDs.

The final request and response formats must be agreed upon with the backend developer before integration is considered complete.

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
- Integrate the engine with the backend and test the complete verification workflow.
- Improve reporting of evidence, source metadata, and uncertainty.

## Developer

**Role:** Member 3 – AI Verification Engine  
**Project:** ClaimLens  
**Branch:** `feature`
