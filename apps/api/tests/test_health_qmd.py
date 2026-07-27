from agi_server.config import Settings
from agi_server.main import app, get_settings
from fastapi.testclient import TestClient


def test_health_qmd_disabled_when_qmd_url_is_empty():
    def get_settings_override():
        return Settings(_env_file=None, qmd_url="", cloud_models_enabled=False)

    app.dependency_overrides[get_settings] = get_settings_override
    try:
        client = TestClient(app)
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["components"]["qmd"] == "disabled; lexical fallback active"
    finally:
        app.dependency_overrides.clear()


def test_health_qmd_unavailable_when_qmd_url_unreachable():
    def get_settings_override():
        return Settings(_env_file=None, qmd_url="http://127.0.0.1:59999", cloud_models_enabled=False)

    app.dependency_overrides[get_settings] = get_settings_override
    try:
        client = TestClient(app)
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["components"]["qmd"] == "unavailable; lexical fallback active"
    finally:
        app.dependency_overrides.clear()
