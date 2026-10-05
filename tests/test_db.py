import pytest
from sqlalchemy.engine import make_url

from warehouse.db import get_database_url


def test_get_database_url_encodes_reserved_characters(monkeypatch):
    monkeypatch.setenv("DB_HOST", "db.example.com")
    monkeypatch.setenv("DB_PORT", "5432")
    monkeypatch.setenv("DB_NAME", "gitpulse")
    monkeypatch.setenv("DB_USER", "tenant/user")
    monkeypatch.setenv("DB_PASSWORD", "pa:ss/word?x#y")

    parsed = make_url(get_database_url())

    assert parsed.drivername == "postgresql"
    assert parsed.username == "tenant/user"
    assert parsed.password == "pa:ss/word?x#y"
    assert parsed.host == "db.example.com"
    assert parsed.port == 5432
    assert parsed.database == "gitpulse"


def test_get_database_url_raises_for_missing_required_vars(monkeypatch):
    monkeypatch.delenv("DB_HOST", raising=False)
    monkeypatch.delenv("DB_PORT", raising=False)
    monkeypatch.delenv("DB_NAME", raising=False)
    monkeypatch.delenv("DB_USER", raising=False)
    monkeypatch.delenv("DB_PASSWORD", raising=False)

    with pytest.raises(RuntimeError, match="Missing required database environment variables:"):
        get_database_url()
