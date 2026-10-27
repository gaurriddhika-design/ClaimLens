import pytest

from app.schemas import ConfidenceLevel, Verdict
from app.services.ingestion import IngestedDocument
from app.services.verification_engine import build_verified_report


@pytest.mark.parametrize(
    ("engine_label", "expected"),
    [
        ("Verified", Verdict.SUPPORTED),
        ("False / Contradicted", Verdict.CONTRADICTED),
        ("Partially True / Misleading", Verdict.MISLEADING_OR_MISSING_CONTEXT),
        ("Unverified / Insufficient Evidence", Verdict.UNVERIFIED),
        ("Opinion / Not Fact-Checkable", Verdict.NOT_FACT_CHECKABLE),
        ("future unknown verdict", Verdict.UNVERIFIED),
    ],
)
def test_maps_engine_verdict_labels_explicitly(engine_label, expected):
    report = build_verified_report(
        IngestedDocument("text", "A sufficiently long claim.", "A sufficiently long claim."),
        {
            "claim": "A sufficiently long claim.",
            "verdict": engine_label,
            "confidence": "high",
            "reason": "Synthetic engine result.",
            "sources": [],
            "limitations": [],
        },
    )

    assert report.claims[0].verdict is expected
    assert report.verdict_counts[expected] == 1
    assert report.total_claims == 1


@pytest.mark.parametrize(
    ("engine_label", "expected"),
    [
        ("high", ConfidenceLevel.HIGH),
        ("medium", ConfidenceLevel.MEDIUM),
        ("low", ConfidenceLevel.LOW),
        ("unknown", ConfidenceLevel.NOT_ASSESSED),
        (None, ConfidenceLevel.NOT_ASSESSED),
    ],
)
def test_maps_confidence_labels(engine_label, expected):
    report = build_verified_report(
        IngestedDocument("text", "A sufficiently long claim.", "A sufficiently long claim."),
        {
            "claim": "A sufficiently long claim.",
            "verdict": "Unverified / Insufficient Evidence",
            "confidence": engine_label,
            "reason": "Synthetic engine result.",
            "sources": [],
            "limitations": [],
        },
    )

    assert report.claims[0].confidence_level is expected


def test_maps_actual_source_stances_and_retrieval_fields():
    report = build_verified_report(
        IngestedDocument("text", "A sufficiently long claim.", "A sufficiently long claim."),
        {
            "claim": "A sufficiently long claim.",
            "verdict": "Partially True / Misleading",
            "confidence": "low",
            "reason": "Synthetic mixed evidence.",
            "sources": [
                {
                    "title": "Supporting",
                    "url": "https://support.example",
                    "stance": "supports",
                    "content_origin": "webpage",
                    "relevant_sentences": ["Relevant source sentence."],
                    "fetched_at": "2026-10-27T12:00:00Z",
                },
                {
                    "title": "Contradicting",
                    "url": "https://contradict.example",
                    "stance": "potential_contradiction",
                    "content_origin": "search_snippet",
                    "relevant_sentences": ["Contrary source sentence."],
                    "fetched_at": "invalid",
                },
                {
                    "title": "Unclear",
                    "url": "https://unknown.example",
                    "stance": "needs_review",
                    "content_origin": "unknown",
                },
            ],
            "limitations": [],
        },
    )

    claim = report.claims[0]
    assert report.claims[0].verdict is Verdict.MISLEADING_OR_MISSING_CONTEXT
    assert [item.supports_claim for item in report.evidence] == [True, False, None]
    assert claim.supporting_evidence_ids == [report.evidence[0].evidence_id]
    assert claim.contradicting_evidence_ids == [report.evidence[1].evidence_id]
    assert report.evidence[0].source_type == "webpage"
    assert report.evidence[0].retrieved_at is not None
    assert report.evidence[1].source_type == "search_snippet"
    assert report.evidence[1].retrieved_at is None
    assert report.evidence[2].source_type == "unknown"
