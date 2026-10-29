from datetime import datetime
from pydantic import BaseModel, ConfigDict


class EvidenceItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    evidence_id: str
    source_title: str
    source_url: str | None = None
    excerpt: str | None = None
    source_type: str = "unknown"
    supports_claim: bool | None = None
    retrieved_at: datetime | None = None
