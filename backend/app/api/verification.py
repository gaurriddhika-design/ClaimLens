
import httpx
from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, ConfigDict, Field
from starlette.concurrency import run_in_threadpool

from ..core.config import settings
from ..schemas import AuditEvent, ReportResponse
from ..services.verification_engine import (
    build_verified_report,
    validate_claim_text,
)
from ..services.ingestion import IngestedDocument, ingest_pdf, ingest_text, ingest_url
from ..services.report_service import empty_verdict_counts
from ..utils.url_safety import UnsafeURLError
from ..storage.repository import get_report, save_report
from services.search_service import SearchService, SearchServiceError
from services.source_fetcher import SourceFetcher
from services.verification_service import VerificationService

router = APIRouter(tags=["verification"])


class TextVerificationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1, max_length=settings.max_text_chars)


class URLVerificationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    url: str = Field(min_length=1, max_length=2048)


def _map_ingestion_error(exc: Exception) -> HTTPException:
    if isinstance(exc, (ValueError, UnsafeURLError)):
        return HTTPException(status_code=422, detail=str(exc))
    if isinstance(exc, httpx.TimeoutException):
        return HTTPException(status_code=504, detail="Timed out while retrieving the URL.")
    if isinstance(exc, httpx.HTTPStatusError):
        return HTTPException(status_code=502, detail=f"Source website returned HTTP {exc.response.status_code}.")
    if isinstance(exc, httpx.RequestError):
        return HTTPException(status_code=502, detail="Could not retrieve the source website.")
    return HTTPException(status_code=500, detail="Input ingestion failed.")


async def _verify_document(document: IngestedDocument) -> ReportResponse:
    """Run any supported input through the same verification engine."""
    try:
        validate_claim_text(document.text)
    except ValueError as exc:
        raise _map_ingestion_error(exc) from exc

    if not settings.search_provider_is_configured:
        raise HTTPException(
            status_code=503,
            detail="Verification is unavailable; configure the Tavily search provider.",
        )

    try:
        search_service = SearchService(api_key=settings.configured_search_api_key)
    except SearchServiceError as exc:
        raise HTTPException(
            status_code=503,
            detail="Verification is unavailable; configure the Tavily search provider.",
        ) from exc

    verification_service = VerificationService(
        search_service=search_service,
        source_fetcher=SourceFetcher(),
    )
    try:
        result = await run_in_threadpool(verification_service.verify, document.text)
    except ValueError as exc:
        raise _map_ingestion_error(exc) from exc
    except SearchServiceError as exc:
        raise HTTPException(
            status_code=502,
            detail="The search provider failed; no verdict was generated.",
        ) from exc

    try:
        report = build_verified_report(document, result)
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=502,
            detail="The verification engine returned an unusable result; no report was saved.",
        ) from exc

    return await save_report(report)


@router.post("/api/verify", response_model=ReportResponse)
async def submit_text_for_verification(payload: TextVerificationRequest) -> ReportResponse:
    try:
        document = ingest_text(payload.text)
    except ValueError as exc:
        raise _map_ingestion_error(exc) from exc
    return await _verify_document(document)


@router.post("/api/verify/pdf", response_model=ReportResponse)
async def submit_pdf_for_verification(file: UploadFile = File(...)) -> ReportResponse:
    try:
        document = await ingest_pdf(file)
    except (ValueError, httpx.HTTPError) as exc:
        raise _map_ingestion_error(exc) from exc
    finally:
        await file.close()
    return await _verify_document(document)


@router.post("/api/verify/url", response_model=ReportResponse)
async def submit_url_for_verification(payload: URLVerificationRequest) -> ReportResponse:
    try:
        document = await ingest_url(payload.url)
    except (ValueError, UnsafeURLError, httpx.HTTPError) as exc:
        raise _map_ingestion_error(exc) from exc
    return await _verify_document(document)


@router.get("/api/reports/{report_id}", response_model=ReportResponse, tags=["reports"])
async def retrieve_report(report_id: str) -> ReportResponse:
    """Retrieve a previously ingested report by its report ID."""
    report = await get_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found.")
    return report
