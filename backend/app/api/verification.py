from datetime import datetime, timezone
from uuid import uuid4

import httpx
from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, ConfigDict, Field

from ..core.config import settings
from ..schemas import AuditEvent, ReportResponse
from ..services.ingestion import IngestedDocument, ingest_pdf, ingest_text, ingest_url
from ..services.report_service import empty_verdict_counts
from ..utils.url_safety import UnsafeURLError
from ..storage.repository import get_report, save_report

router = APIRouter(tags=["verification"])


class TextVerificationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(min_length=1, max_length=settings.max_text_chars)


class URLVerificationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    url: str = Field(min_length=1, max_length=2048)


def _pending_report(document: IngestedDocument) -> ReportResponse:
    """Build an intake-only report; no claim verification is performed here."""
    now = datetime.now(timezone.utc)
    details = f"Input extracted and validated; {len(document.text)} characters available."
    if document.page_count is not None:
        details += f" PDF pages: {document.page_count}."
    if document.source_url:
        details += f" Source URL: {document.source_url}"
    return ReportResponse(
        report_id=str(uuid4()),
        input_type=document.input_type,
        input_summary=document.summary,
        created_at=now,
        processing_status="completed",
        overall_summary=(
            "Input ingestion completed. Factual verification has not run because "
            "the separate verification engine is not connected yet."
        ),
        total_claims=0,
        verdict_counts=empty_verdict_counts(),
        claims=[],
        evidence=[],
        audit_events=[AuditEvent(
            event_type="input_ingested",
            occurred_at=now,
            details=details + " No factual assessment was performed.",
        )],
    )


async def _persist_intake_report(document: IngestedDocument) -> ReportResponse:
    report = _pending_report(document)
    return await save_report(report)


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


@router.post("/api/verify", response_model=ReportResponse)
async def submit_text_for_verification(payload: TextVerificationRequest) -> ReportResponse:
    try:
        document = ingest_text(payload.text)
    except ValueError as exc:
        raise _map_ingestion_error(exc) from exc
    return await _persist_intake_report(document)


@router.post("/api/verify/pdf", response_model=ReportResponse)
async def submit_pdf_for_verification(file: UploadFile = File(...)) -> ReportResponse:
    try:
        document = await ingest_pdf(file)
    except (ValueError, httpx.HTTPError) as exc:
        raise _map_ingestion_error(exc) from exc
    finally:
        await file.close()
    return await _persist_intake_report(document)


@router.post("/api/verify/url", response_model=ReportResponse)
async def submit_url_for_verification(payload: URLVerificationRequest) -> ReportResponse:
    try:
        document = await ingest_url(payload.url)
    except (ValueError, UnsafeURLError, httpx.HTTPError) as exc:
        raise _map_ingestion_error(exc) from exc
    return await _persist_intake_report(document)


@router.get("/api/reports/{report_id}", response_model=ReportResponse, tags=["reports"])
async def retrieve_report(report_id: str) -> ReportResponse:
    """Retrieve a previously ingested report by its report ID."""
    report = await get_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found.")
    return report
