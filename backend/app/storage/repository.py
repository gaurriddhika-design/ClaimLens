"""Persistence operations for complete ClaimLens report payloads."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..schemas import ReportResponse
from .database import ReportRecord, SessionFactory, initialize_database


async def save_report(report: ReportResponse) -> ReportResponse:
    """Insert or replace a report by ID and return the validated report."""
    await initialize_database()  # Also supports test clients that do not enter ASGI lifespan.
    payload = report.model_dump(mode="json")
    async with SessionFactory() as session:
        existing = await session.get(ReportRecord, report.report_id)
        if existing is None:
            existing = ReportRecord(
                report_id=report.report_id,
                input_type=report.input_type,
                created_at=report.created_at,
                report_json=payload,
            )
            session.add(existing)
        else:
            existing.input_type = report.input_type
            existing.created_at = report.created_at
            existing.report_json = payload
        await session.commit()
    return report


async def get_report(report_id: str) -> ReportResponse | None:
    await initialize_database()  # Safe for first read and local test clients.
    async with SessionFactory() as session:
        result = await session.execute(
            select(ReportRecord).where(ReportRecord.report_id == report_id)
        )
        record = result.scalar_one_or_none()
        if record is None:
            return None
        return ReportResponse.model_validate(record.report_json)


async def count_reports() -> int:
    """Small helper used by tests and diagnostics; never exposed publicly."""
    from sqlalchemy import func
    async with SessionFactory() as session:
        result = await session.execute(select(func.count()).select_from(ReportRecord))
        return int(result.scalar_one())
