from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.main import app


def test_healthz_returns_ok_and_version():
    app.dependency_overrides[get_settings] = lambda: Settings(git_sha="abc1234")
    try:
        res = TestClient(app).get("/healthz")
    finally:
        app.dependency_overrides.clear()

    assert res.status_code == 200
    assert res.json() == {"status": "ok", "version": "abc1234"}
