import pytest
from sqlalchemy.engine import make_url

from app.storage.database import _normalize_database_url


@pytest.mark.parametrize("scheme", ["postgres", "postgresql"])
def test_normalizes_postgres_urls_and_ssl_options(scheme):
    url = (
        f"{scheme}://test_user:test_password@localhost:5432/claimlens"
        "?sslmode=require&channel_binding=require&application_name=claimlens"
    )

    normalized = make_url(_normalize_database_url(url))

    assert normalized.drivername == "postgresql+asyncpg"
    assert normalized.query == {
        "ssl": "require",
        "application_name": "claimlens",
    }


@pytest.mark.parametrize("sslmode", ["verify-ca", "verify-full"])
def test_rejects_unverified_asyncpg_sslmode_mappings(sslmode):
    url = (
        "postgresql://test_user:test_password@localhost:5432/claimlens"
        f"?sslmode={sslmode}"
    )

    with pytest.raises(ValueError, match="only sslmode=require is supported") as error:
        _normalize_database_url(url)

    assert "test_password" not in str(error.value)
    assert "localhost" not in str(error.value)


def test_preserves_sqlite_url():
    url = "sqlite+aiosqlite:///./claimlens.db"
    assert _normalize_database_url(url) == url
