import os
from cult_common.config import settings


def test_settings_defaults(tmp_path, monkeypatch):
    monkeypatch.setenv('POSTGRES_HOST', 'db-host')
    assert settings.POSTGRES_HOST == 'db-host'