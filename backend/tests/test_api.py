from io import BytesIO

import pymupdf
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_demo_endpoint_is_explicitly_labelled():
    response = client.post("/api/demo")
    assert response.status_code == 200
    assert response.json()["report_id"] == "demo-claimlens-001"
    assert "DEMO ONLY" in response.json()["overall_summary"]


def test_demo_verdict_counts_are_consistent():
    report = client.post("/api/demo").json()
    assert report["total_claims"] == len(report["claims"]) == 1
    assert sum(report["verdict_counts"].values()) == 1


def test_text_intake_returns_pending_report_without_fake_claims():
    response = client.post("/api/verify", json={"text": "The Earth orbits the Sun."})
    assert response.status_code == 200
    report = response.json()
    assert report["input_type"] == "text"
    assert report["processing_status"] == "completed"
    assert report["total_claims"] == 0
    assert report["claims"] == []
    assert "has not run" in report["overall_summary"]


def test_blank_text_is_rejected():
    assert client.post("/api/verify", json={"text": "   "}).status_code == 422


def test_missing_text_is_rejected():
    assert client.post("/api/verify", json={}).status_code == 422


def test_extra_request_fields_are_rejected():
    assert client.post("/api/verify", json={"text": "hello", "verdict": "SUPPORTED"}).status_code == 422


def test_pdf_upload_returns_pending_report():
    buffer = BytesIO()
    with pymupdf.open() as doc:
        page = doc.new_page()
        page.insert_text((72, 72), "PDF ingestion API test")
        buffer.write(doc.tobytes())
    response = client.post("/api/verify/pdf", files={"file": ("test.pdf", buffer.getvalue(), "application/pdf")})
    assert response.status_code == 200, response.text
    report = response.json()
    assert report["input_type"] == "pdf"
    assert report["claims"] == []
    assert "PDF ingestion API test" in report["input_summary"]


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


def test_text_intake_report_can_be_retrieved_from_database():
    submitted = client.post("/api/verify", json={"text": "Persistence integration test text."})
    assert submitted.status_code == 200, submitted.text
    report_id = submitted.json()["report_id"]

    retrieved = client.get(f"/api/reports/{report_id}")
    assert retrieved.status_code == 200, retrieved.text
    assert retrieved.json()["report_id"] == report_id
    assert retrieved.json()["input_type"] == "text"
    assert retrieved.json()["input_summary"] == "Persistence integration test text."


def test_unknown_report_id_returns_404():
    response = client.get("/api/reports/does-not-exist-claimlens")
    assert response.status_code == 404
    assert response.json()["detail"] == "Report not found."


def test_pdf_intake_report_is_persisted():
    buffer = BytesIO()
    with pymupdf.open() as doc:
        page = doc.new_page()
        page.insert_text((72, 72), "Persistent PDF report")
        buffer.write(doc.tobytes())
    submitted = client.post("/api/verify/pdf", files={"file": ("persist.pdf", buffer.getvalue(), "application/pdf")})
    assert submitted.status_code == 200, submitted.text
    report_id = submitted.json()["report_id"]
    retrieved = client.get(f"/api/reports/{report_id}")
    assert retrieved.status_code == 200
    assert retrieved.json()["input_type"] == "pdf"
    assert "Persistent PDF report" in retrieved.json()["input_summary"]
