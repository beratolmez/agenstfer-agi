import importlib
import sys
from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_setup_no_files(monkeypatch):
    response = client.post("/api/setup", json={"files": []})
    assert response.status_code == 200
    assert response.json() == {"message": "Setup complete", "details": []}


def test_chat(monkeypatch):
    class FakeGraph:
        def invoke(self, input_data):
            return {
                "research_data": "research",
                "analysis_data": "analysis",
                "messages": ["Final review result"],
            }

    mock_ai = MagicMock()
    mock_ai.graph.create_graph.return_value = FakeGraph()
    sys.modules["ai_agent.graph"] = mock_ai.graph

    # Reload main so it picks up the mocked module
    import main

    importlib.reload(main)

    # We must redefine client because app was reloaded
    test_client = TestClient(main.app)
    response = test_client.post("/api/chat", json={"query": "test query"})
    assert response.status_code == 200
    data = response.json()
    assert data["research_data"] == "research"
    assert data["analysis_data"] == "analysis"
    assert data["final_review"] == "Final review result"
