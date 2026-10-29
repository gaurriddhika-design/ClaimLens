from io import BytesIO

import pymupdf
from fastapi.testclient import TestClient

from app.core.config import Settings, settings
from services.search_service import SearchService, SearchServiceError
from services.source_fetcher import SourceFetcher

from app.main import app

client = TestClient(app)


def configure_mocked_search(monkeypatch):
    monkeypatch.setattr(settings, "search_provider", "tavily")
    monkeypatch.setattr(settings, "search_api_key", "test-api-key")
    monkeypatch.setattr(settings, "tavily_api_key", "")

    def search(_service, _claim, max_results=5):
        assert max_results == 5
        return [
            {
                "title": "First test source",
                "url": "https://first.example/fact",
                "snippet": "ClaimLens uses async persistence.",
                "score": 0.99,
                "published_date": "2026-10-01",
            },
            {
                "title": "Second test source",
                "url": "https://second.example/fact",
                "snippet": "ClaimLens uses async persistence.",
                "score": 0.98,
                "published_date": "2026-10-02",
            },
        ]

    def fetch(_fetcher, url):
        return {
            "url": url,
            "title": "Fetched test article",
            "text": "ClaimLens uses async persistence. The claim is true.",
            "published_date": "2026-10-01",
            "fetched_at": "2026-10-27T12:00:00+00:00",
        }

    monkeypatch.setattr(SearchService, "search", search)
    monkeypatch.setattr(SourceFetcher, "fetch", fetch)


def test_health_endpoint():
    response = client.get("/api/health")

    assert response.status_code == 200
    health = response.json()

    assert health["status"] == "healthy"
    assert health["verification_engine_integrated"] is True
    assert "llm_provider_configured" in health
    assert "search_provider_configured" in health
    assert "database_configured" in health


def test_demo_endpoint_is_explicitly_labelled():
    response = client.post("/api/demo")
    assert response.status_code == 200
    assert response.json()["report_id"] == "demo-claimlens-001"
    assert "DEMO ONLY" in response.json()["overall_summary"]


def test_demo_verdict_counts_are_consistent():
    report = client.post("/api/demo").json()
    assert report["total_claims"] == len(report["claims"]) == 1
    assert sum(report["verdict_counts"].values()) == 1


def test_text_verification_returns_heuristic_report(monkeypatch):
    configure_mocked_search(monkeypatch)
    response = client.post(
        "/api/verify",
        json={"text": "ClaimLens uses async persistence."},
    )
    assert response.status_code == 200
    report = response.json()
    assert report["input_type"] == "text"
    assert report["processing_status"] == "completed"
    assert report["total_claims"] == 1
    assert report["claims"][0]["verdict"] == "SUPPORTED"
    assert "heuristic" in report["overall_summary"].lower()
    assert "human reviewer" in report["overall_summary"].lower()
    assert report["verdict_counts"]["SUPPORTED"] == 1
    assert [event["event_type"] for event in report["audit_events"]] == [
        "input_received",
        "verification_completed",
        "heuristic_limitations",
    ]
    assert "2 sources" in report["audit_events"][1]["details"]


def test_blank_text_is_rejected():
    assert client.post("/api/verify", json={"text": "   "}).status_code == 422


def test_too_short_claim_is_rejected_before_search_configuration():
    response = client.post("/api/verify", json={"text": "short"})
    assert response.status_code == 422
    assert "too short" in response.json()["detail"]


def test_missing_text_is_rejected():
    assert client.post("/api/verify", json={}).status_code == 422


def test_extra_request_fields_are_rejected():
    assert client.post("/api/verify", json={"text": "hello", "verdict": "SUPPORTED"}).status_code == 422


def test_pdf_upload_returns_verified_report(monkeypatch):
    configure_mocked_search(monkeypatch)
    buffer = BytesIO()
    with pymupdf.open() as doc:
        page = doc.new_page()
        page.insert_text((72, 72), "PDF ingestion API test")
        buffer.write(doc.tobytes())

    response = client.post(
        "/api/verify/pdf",
        files={"file": ("test.pdf", buffer.getvalue(), "application/pdf")},
    )
    assert response.status_code == 200, response.text
    report = response.json()
    assert report["input_type"] == "pdf"
    assert report["total_claims"] == 1
    assert len(report["claims"]) == 1
    assert report["processing_status"] == "completed"
    assert any(event["event_type"] == "verification_completed"
               for event in report["audit_events"])



def test_pdf_upload_rejects_wrong_file_type():
    response = client.post("/api/verify/pdf", files={"file": ("notes.txt", b"hello", "text/plain")})
    assert response.status_code == 422


def test_url_endpoint_rejects_localhost_before_network_request():
    response = client.post("/api/verify/url", json={"url": "http://localhost/private"})
    assert response.status_code == 422


def test_text_request_rejects_text_over_configured_schema_limit():
    from app.core.config import settings

    response = client.post("/api/verify", json={"text": "x" * (settings.max_text_chars + 1)})
    assert response.status_code == 422


def test_text_verification_report_can_be_retrieved_from_database(monkeypatch):
    configure_mocked_search(monkeypatch)
    submitted = client.post(
        "/api/verify",
        json={"text": "ClaimLens uses async persistence."},
    )
    assert submitted.status_code == 200, submitted.text
    report_id = submitted.json()["report_id"]

    retrieved = client.get(f"/api/reports/{report_id}")
    assert retrieved.status_code == 200, retrieved.text
    assert retrieved.json()["report_id"] == report_id
    assert retrieved.json()["input_type"] == "text"
    assert retrieved.json()["input_summary"] == "ClaimLens uses async persistence."
    assert retrieved.json()["total_claims"] == 1
    assert retrieved.json()["claims"][0]["verdict"] == "SUPPORTED"


def test_verified_report_maps_confidence_and_evidence_ids(monkeypatch):
    configure_mocked_search(monkeypatch)
    response = client.post(
        "/api/verify",
        json={"text": "ClaimLens uses async persistence."},
    )

    assert response.status_code == 200
    report = response.json()
    claim = report["claims"][0]
    evidence_ids = {item["evidence_id"] for item in report["evidence"]}
    assert claim["verdict"] == "SUPPORTED"
    assert claim["confidence_level"] == "MEDIUM"
    assert len(report["evidence"]) == 2
    assert claim["supporting_evidence_ids"]
    assert set(claim["supporting_evidence_ids"]) <= evidence_ids
    assert claim["contradicting_evidence_ids"] == []
    assert all(item["supports_claim"] is True for item in report["evidence"])
    assert all(item["source_type"] == "webpage" for item in report["evidence"])
    assert all(item["retrieved_at"] == "2026-10-27T12:00:00Z" for item in report["evidence"])


def test_missing_search_configuration_returns_503_without_saving(monkeypatch):
    monkeypatch.setattr(settings, "search_provider", "tavily")
    monkeypatch.setattr(settings, "search_api_key", "")
    monkeypatch.setattr(settings, "tavily_api_key", "")
    saved_reports = []

    async def record_save(report):
        saved_reports.append(report)
        return report

    monkeypatch.setattr("app.api.verification.save_report", record_save)
    response = client.post(
        "/api/verify",
        json={"text": "ClaimLens uses async persistence."},
    )

    assert response.status_code == 503
    assert "Tavily" in response.json()["detail"]
    assert saved_reports == []


def test_search_failure_returns_safe_error_without_saving(monkeypatch):
    configure_mocked_search(monkeypatch)
    saved_reports = []

    def fail_search(_service, _claim, max_results=5):
        raise SearchServiceError("upstream request included secret test-api-key")

    async def record_save(report):
        saved_reports.append(report)
        return report

    monkeypatch.setattr(SearchService, "search", fail_search)
    monkeypatch.setattr("app.api.verification.save_report", record_save)
    response = client.post(
        "/api/verify",
        json={"text": "ClaimLens uses async persistence."},
    )

    assert response.status_code == 502
    assert "test-api-key" not in response.text
    assert "verdict was generated" in response.json()["detail"]
    assert saved_reports == []


def test_health_flags_reflect_provider_and_engine_configuration(monkeypatch):
    monkeypatch.setattr(settings, "search_provider", "tavily")
    monkeypatch.setattr(settings, "search_api_key", "test-api-key")
    monkeypatch.setattr(settings, "tavily_api_key", "")

    configured = client.get("/api/health").json()
    assert configured["search_provider_configured"] is True
    assert configured["verification_engine_integrated"] is True
    assert configured["database_configured"] is bool(settings.database_url)

    monkeypatch.setattr(settings, "search_provider", "unsupported")
    unconfigured = client.get("/api/health").json()
    assert unconfigured["search_provider_configured"] is False
    assert unconfigured["verification_engine_integrated"] is True

    monkeypatch.setattr(settings, "search_provider", "")
    monkeypatch.setattr(settings, "search_api_key", "")
    monkeypatch.setattr(settings, "tavily_api_key", "legacy-test-api-key")
    legacy = client.get("/api/health").json()
    assert legacy["search_provider_configured"] is True


def test_legacy_tavily_environment_key_is_loaded(monkeypatch):
    monkeypatch.delenv("SEARCH_PROVIDER", raising=False)
    monkeypatch.delenv("SEARCH_API_KEY", raising=False)
    monkeypatch.setenv("TAVILY_API_KEY", "synthetic-tavily-test-key")

    configuration = Settings(_env_file=None)

    assert configuration.tavily_api_key == "synthetic-tavily-test-key"
    assert configuration.search_provider_is_configured is True


def test_unknown_report_id_returns_404():
    response = client.get("/api/reports/does-not-exist-claimlens")
    assert response.status_code == 404
    assert response.json()["detail"] == "Report not found."


def test_pdf_verification_report_is_persisted(monkeypatch):
    configure_mocked_search(monkeypatch)
    buffer = BytesIO()
    with pymupdf.open() as doc:
        page = doc.new_page()
        page.insert_text((72, 72), "Persistent PDF report")
        buffer.write(doc.tobytes())

    submitted = client.post(
        "/api/verify/pdf",
        files={"file": ("persist.pdf", buffer.getvalue(), "application/pdf")},
    )
    assert submitted.status_code == 200, submitted.text
    report = submitted.json()
    assert report["input_type"] == "pdf"
    assert report["total_claims"] == 1

    retrieved = client.get(f"/api/reports/{report['report_id']}")
    assert retrieved.status_code == 200, retrieved.text
    saved = retrieved.json()
    assert saved["report_id"] == report["report_id"]
    assert saved["input_type"] == "pdf"
    assert saved["total_claims"] == 1
    assert len(saved["claims"]) == 1


def test_url_verification_uses_engine_and_preserves_input_type(monkeypatch):
    from app.services.ingestion import IngestedDocument

    configure_mocked_search(monkeypatch)

    async def fake_ingest_url(url):
        return IngestedDocument(
            input_type="url",
            text="The Earth orbits the Sun once every year.",
            summary="Extracted test page text",
            source_url=url,
        )

    monkeypatch.setattr("app.api.verification.ingest_url", fake_ingest_url)

    response = client.post(
        "/api/verify/url",
        json={"url": "https://example.com/article"},
    )
    assert response.status_code == 200, response.text
    report = response.json()
    assert report["input_type"] == "url"
    assert report["total_claims"] == 1
    assert len(report["claims"]) == 1
    assert any(
        event["event_type"] == "verification_completed"
        for event in report["audit_events"]
    )
    assert any(
        "https://example.com/article" in event["details"]
        for event in report["audit_events"]
    )
