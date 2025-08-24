import pytest

from common.r2_config import load_r2_config


def test_load_r2_config_success(monkeypatch):
    monkeypatch.setenv("R2_ENDPOINT_URL", "endpoint")
    monkeypatch.setenv("R2_BUCKET_NAME", "bucket")
    monkeypatch.setenv("R2_ACCESS_KEY_ID", "key")
    monkeypatch.setenv("R2_SECRET_ACCESS_KEY", "secret")

    cfg = load_r2_config()
    assert cfg["endpoint_url"] == "endpoint"
    assert cfg["bucket"] == "bucket"


def test_load_r2_config_missing(monkeypatch):
    for var in [
        "R2_ENDPOINT_URL",
        "R2_BUCKET_NAME",
        "R2_ACCESS_KEY_ID",
        "R2_SECRET_ACCESS_KEY",
    ]:
        monkeypatch.delenv(var, raising=False)

    with pytest.raises(RuntimeError):
        load_r2_config()
