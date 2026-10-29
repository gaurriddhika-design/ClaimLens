from enum import Enum
from pydantic import BaseModel, ConfigDict, Field


class Verdict(str, Enum):
    SUPPORTED = "SUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    MISLEADING_OR_MISSING_CONTEXT = "MISLEADING_OR_MISSING_CONTEXT"
    MIXED_EVIDENCE = "MIXED_EVIDENCE"
    UNVERIFIED = "UNVERIFIED"
    NOT_FACT_CHECKABLE = "NOT_FACT_CHECKABLE"


class ConfidenceLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NOT_ASSESSED = "NOT_ASSESSED"


class ClaimResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    claim_id: str
    original_text: str
    source_location: str | None = None
    verdict: Verdict
    explanation: str
    confidence_level: ConfidenceLevel = ConfidenceLevel.NOT_ASSESSED
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    contradicting_evidence_ids: list[str] = Field(default_factory=list)
    official_source_matches: list[str] = Field(default_factory=list)
    verification_checks: list[str] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
