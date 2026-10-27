"""Async SQLAlchemy database setup and report table definition."""
from collections.abc import AsyncIterator

from sqlalchemy import JSON, DateTime, String, Text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError
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
    """Normalize PostgreSQL URLs for asyncpg without weakening TLS settings."""
    if not url.startswith(("postgres://", "postgresql://")):
        return url

    try:
        parsed_url = make_url(url)
    except ArgumentError:
        raise ValueError("Invalid PostgreSQL database URL") from None

    query = dict(parsed_url.query)
    query.pop("channel_binding", None)
    sslmode = query.pop("sslmode", None)
    if sslmode is not None:
        if isinstance(sslmode, tuple) or sslmode.lower() != "require":
            raise ValueError(
                "Unsupported PostgreSQL sslmode; only sslmode=require is supported"
            )
        query["ssl"] = "require"

    return parsed_url.set(
        drivername="postgresql+asyncpg",
        query=query,
    ).render_as_string(hide_password=False)


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
