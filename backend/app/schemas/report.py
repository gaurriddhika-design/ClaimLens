from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field
from .claim import ClaimResult, Verdict
from .evidence import EvidenceItem


class AuditEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_type: str
    occurred_at: datetime
    details: str


class ReportResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    report_id: str
    input_type: Literal["text", "url", "pdf", "image" , "demo"]
    input_summary: str
    created_at: datetime
    processing_status: Literal["queued", "processing", "completed", "failed"]
    overall_summary: str
    total_claims: int = Field(ge=0)
    verdict_counts: dict[Verdict, int]
    claims: list[ClaimResult]
    evidence: list[EvidenceItem]
    audit_events: list[AuditEvent]


class HealthResponse(BaseModel):
    status: Literal["healthy"]
    llm_provider_configured: bool
    search_provider_configured: bool
    database_configured: bool
    verification_engine_integrated: bool = False
