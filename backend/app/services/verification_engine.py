"""Adapt Member 3's synchronous verification engine to backend report schemas."""
from datetime import datetime, timezone
from uuid import uuid4

from ..schemas import (
    AuditEvent,
    ClaimResult,
    ConfidenceLevel,
    EvidenceItem,
    ReportResponse,
    Verdict,
)
from ..services.ingestion import IngestedDocument
from ..services.report_service import empty_verdict_counts
from services.claim_extractor import ClaimExtractor


_VERDICT_MAP = {
    "Verified": Verdict.SUPPORTED,
    "False / Contradicted": Verdict.CONTRADICTED,
    "Partially True / Misleading": Verdict.MISLEADING_OR_MISSING_CONTEXT,
    "Unverified / Insufficient Evidence": Verdict.UNVERIFIED,
    "Opinion / Not Fact-Checkable": Verdict.NOT_FACT_CHECKABLE,
}
_CONFIDENCE_MAP = {
    "high": ConfidenceLevel.HIGH,
    "medium": ConfidenceLevel.MEDIUM,
    "low": ConfidenceLevel.LOW,
}
_SUPPORTING_STANCES = {"support", "supports", "supporting", "consistent"}
_CONTRADICTING_STANCES = {
    "contradiction",
    "contradicts",
    "contradicting",
    "potential_contradiction",
}
_HEURISTIC_LIMITATION = (
    "Evidence analysis uses lexical heuristics and is not definitive; "
    "a human reviewer must assess source authority, context, and corroboration."
)


def validate_claim_text(text: str) -> str:
    """Reject claims the engine cannot meaningfully process before searching."""
    return ClaimExtractor().extract_claim(text)


def _parse_timestamp(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None


def build_verified_report(
    document: IngestedDocument,
    result: dict,
) -> ReportResponse:
    """Translate a successful engine result into a complete persisted report."""
    if not isinstance(result, dict):
        raise TypeError("Verification result must be an object.")

    claim_text = result.get("claim")
    if not isinstance(claim_text, str) or not claim_text.strip():
        raise ValueError("Verification result has no claim.")
    claim_text = claim_text.strip()

    engine_verdict = result.get("verdict")
    verdict = _VERDICT_MAP.get(engine_verdict, Verdict.UNVERIFIED)
    if not isinstance(engine_verdict, str):
        verdict = Verdict.UNVERIFIED

    confidence = result.get("confidence")
    confidence_level = (
        _CONFIDENCE_MAP.get(confidence.lower(), ConfidenceLevel.NOT_ASSESSED)
        if isinstance(confidence, str)
        else ConfidenceLevel.NOT_ASSESSED
    )

    raw_sources = result.get("sources", [])
    if not isinstance(raw_sources, list):
        raise TypeError("Verification result sources must be a list.")

    evidence: list[EvidenceItem] = []
    supporting_ids: list[str] = []
    contradicting_ids: list[str] = []
    for source in raw_sources:
        if not isinstance(source, dict):
            continue

        stance = source.get("stance")
        stance = stance.lower() if isinstance(stance, str) else ""
        if stance in _SUPPORTING_STANCES:
            supports_claim = True
        elif stance in _CONTRADICTING_STANCES:
            supports_claim = False
        else:
            supports_claim = None

        title = source.get("title")
        if not isinstance(title, str) or not title.strip():
            title = "Untitled source"
        url = source.get("url")
        if not isinstance(url, str) or not url.strip():
            url = None
        excerpt_sentences = source.get("relevant_sentences")
        excerpt = None
        if isinstance(excerpt_sentences, list):
            sentences = [
                sentence.strip()
                for sentence in excerpt_sentences
                if isinstance(sentence, str) and sentence.strip()
            ]
            if sentences:
                excerpt = " ".join(sentences)

        origin = source.get("content_origin")
        if origin == "webpage":
            source_type = "webpage"
        elif origin == "search_snippet":
            source_type = "search_snippet"
        else:
            source_type = "unknown"

        evidence_id = str(uuid4())
        evidence.append(
            EvidenceItem(
                evidence_id=evidence_id,
                source_title=title.strip(),
                source_url=url,
                excerpt=excerpt,
                source_type=source_type,
                supports_claim=supports_claim,
                retrieved_at=_parse_timestamp(source.get("fetched_at")),
            )
        )
        if supports_claim is True:
            supporting_ids.append(evidence_id)
        elif supports_claim is False:
            contradicting_ids.append(evidence_id)

    raw_limitations = result.get("limitations", [])
    limitations = (
        [item.strip() for item in raw_limitations if isinstance(item, str) and item.strip()]
        if isinstance(raw_limitations, list)
        else []
    )
    if _HEURISTIC_LIMITATION not in limitations:
        limitations.append(_HEURISTIC_LIMITATION)

    explanation = result.get("reason")
    if not isinstance(explanation, str) or not explanation.strip():
        explanation = "The engine did not provide an explanation."
    explanation = f"{explanation.strip()} {_HEURISTIC_LIMITATION}"

    claim = ClaimResult(
        claim_id=str(uuid4()),
        original_text=claim_text,
        verdict=verdict,
        explanation=explanation,
        confidence_level=confidence_level,
        supporting_evidence_ids=supporting_ids,
        contradicting_evidence_ids=contradicting_ids,
        verification_checks=[
            "Search results were analyzed using lexical heuristics.",
            "Source relevance and truth are not inferred from search ranking scores.",
        ],
        unresolved_questions=[
            "A human reviewer should confirm the sources, context, and corroboration."
        ],
        limitations=limitations,
    )
    counts = empty_verdict_counts()
    counts[verdict] += 1

    now = datetime.now(timezone.utc)
    raw_fetch_failures = result.get("fetch_failures", [])
    fetch_failure_count = (
        len(raw_fetch_failures) if isinstance(raw_fetch_failures, list) else 0
    )
    reason = result.get("reason")
    summary = (
        reason.strip()
        if isinstance(reason, str) and reason.strip()
        else "The verification engine did not provide a verdict explanation."
    )

    return ReportResponse(
        report_id=str(uuid4()),
        input_type=document.input_type,
        input_summary=document.summary,
        created_at=now,
        processing_status="completed",
        overall_summary=(
            f"Heuristic result: {verdict.value}. {summary} {_HEURISTIC_LIMITATION}"
        ),
        total_claims=1,
        verdict_counts=counts,
        claims=[claim],
        evidence=evidence,
        audit_events=[
            AuditEvent(
                event_type="input_received",
                occurred_at=now,
                details=(
                    f"{document.input_type.upper()} input received; "
                    f"{len(document.text)} characters available."
                    + (
                        f" PDF pages: {document.page_count}."
                        if document.page_count is not None
                        else ""
                    )
                    + (
                        f" Source URL: {document.source_url}"
                        if document.source_url
                        else ""
                    )
                ),
            ),
            AuditEvent(
                event_type="verification_completed",
                occurred_at=now,
                details=(
                    f"Verification completed with {len(evidence)} sources and "
                    f"{fetch_failure_count} source fetch failures."
                ),
            ),
            AuditEvent(
                event_type="heuristic_limitations",
                occurred_at=now,
                details=_HEURISTIC_LIMITATION,
            ),
        ],
    )
