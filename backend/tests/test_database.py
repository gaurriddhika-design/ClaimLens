from app.storage.database import _normalize_database_url


def test_normalizes_postgres_scheme():
    url = "postgres://user:password@localhost:5432/claimlens"
    assert _normalize_database_url(url) == (
        "postgresql+asyncpg://user:password@localhost:5432/claimlens"
    )


def test_normalizes_postgresql_scheme():
    url = "postgresql://user:password@localhost:5432/claimlens"
    assert _normalize_database_url(url) == (
        "postgresql+asyncpg://user:password@localhost:5432/claimlens"
    )


def test_preserves_sqlite_url():
    url = "sqlite+aiosqlite:///./claimlens.db"
    assert _normalize_database_url(url) == url
