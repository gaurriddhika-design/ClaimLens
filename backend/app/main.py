from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.health import router as health_router
from .api.verification import router as verification_router
from .core.config import settings
from .core.logging import configure_logging
from .schemas import (
    AuditEvent, ClaimResult, ConfidenceLevel, ReportResponse, Verdict,
)
from .services.report_service import empty_verdict_counts
from .storage.database import close_database, initialize_database

configure_logging()


@asynccontextmanager
async def lifespan(_: FastAPI):
    await initialize_database()
    try:
        yield
    finally:
        await close_database()


app = FastAPI(
    title="ClaimLens Backend API",
    description="Backend API for claim intake and evidence-based verification.",
    version="0.3.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(health_router)
app.include_router(verification_router)


@app.post("/api/demo", response_model=ReportResponse, tags=["demo"])
def demo_report() -> ReportResponse:
    """Return explicitly labelled static demo data; no providers or sources are called."""
    now = datetime.now(timezone.utc)
    counts = empty_verdict_counts()
    counts[Verdict.UNVERIFIED] = 1

    return ReportResponse(
        report_id="demo-claimlens-001",
        input_type="demo",
        input_summary="Static demonstration data",
        created_at=now,
        processing_status="completed",
        overall_summary=(
            "DEMO ONLY: this response illustrates the report format. "
            "No external sources were queried and no real fact-check was performed."
        ),
        total_claims=1,
        verdict_counts=counts,
        claims=[
            ClaimResult(
                claim_id="demo-claim-001",
                original_text="Example claim used to demonstrate the report layout.",
                verdict=Verdict.UNVERIFIED,
                explanation="DEMO ONLY: this example was not fact-checked.",
                confidence_level=ConfidenceLevel.NOT_ASSESSED,
                limitations=["Static demo data; not a factual assessment."],
            )
        ],
        evidence=[],
        audit_events=[
            AuditEvent(
                event_type="demo_result_generated",
                occurred_at=now,
                details="Static mock response returned; no external provider was called.",
            )
        ],
    )
