"""Async SQLAlchemy database setup and report table definition."""
from collections.abc import AsyncIterator

from sqlalchemy import JSON, DateTime, String, Text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from ..core.config import settings


class Base(DeclarativeBase):
    pass


class ReportRecord(Base):
    __tablename__ = "reports"

    report_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    input_type: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    report_json: Mapped[dict] = mapped_column(JSON, nullable=False)


def _normalize_database_url(url: str) -> str:
    """Normalize standard PostgreSQL URLs for the async SQLAlchemy driver."""
    if url.startswith("postgres://"):
        return "postgresql+asyncpg://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        return "postgresql+asyncpg://" + url[len("postgresql://"):]
    return url


def _engine_options(url: str) -> dict:
    # SQLite doesn't accept connection-pool sizing options used by server DBs.
    if url.startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}}
    return {"pool_pre_ping": True}


database_url = _normalize_database_url(settings.database_url)
engine = create_async_engine(database_url, **_engine_options(database_url))
SessionFactory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def initialize_database() -> None:
    """Create tables if missing. This is suitable for the prototype, not migrations."""
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)


async def close_database() -> None:
    await engine.dispose()


async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionFactory() as session:
        yield session
