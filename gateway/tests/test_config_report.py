"""The startup configuration report: redacted, and fails clearly when DATABASE_URL is missing."""
from app.config import Settings, startup_config_report


def _settings(**kw):
    base = dict(
        api_token="a-real-token",
        evidence_read_api_token="another-real-token",
        evidence_cursor_signing_key="a-third-secret",
    )
    base.update(kw)
    return Settings(APP_ENV="test", **base)


def test_report_lists_host_and_secret_presence_never_values():
    s = _settings(database_url="postgresql+psycopg://user:hunter2@db.example.com:5432/qingyu")
    report = startup_config_report(s)
    assert "app_env=test" in report
    assert "host=db.example.com" in report
    assert "api_token=yes" in report
    assert "evidence_read_api_token=yes" in report
    assert "evidence_cursor_signing_key=yes" in report
    # credentials and secret values never appear
    assert "hunter2" not in report
    assert "a-real-token" not in report


def test_report_marks_unset_secrets_and_database():
    s = _settings(database_url=None, api_token="")
    report = startup_config_report(s)
    assert "database=NOT SET" in report
    assert "api_token=no" in report


def test_missing_database_url_outside_test_fails_with_a_pointer():
    try:
        startup_config_report(_settings(APP_ENV="development", database_url=None))
    except RuntimeError as exc:
        assert "DATABASE_URL is not set" in str(exc)
        assert ".env.example" in str(exc)
    else:
        raise AssertionError("expected RuntimeError")


def test_test_env_needs_no_database_url():
    assert "database=NOT SET" in startup_config_report(_settings(database_url=None))
