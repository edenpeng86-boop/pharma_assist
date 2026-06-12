from fastapi.testclient import TestClient

from src.core.models import ChatResponse, CitationCheck
from src.api.app import app


client = TestClient(app)


def test_index_serves_web_client():
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "PharmAssist" in response.text


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_chat_stream_returns_ndjson(monkeypatch):
    class FakeAgent:
        def run(self, question, strategy=None, language="zh-CN"):
            return ChatResponse(
                answer="**测试回答**[1]",
                sources=[],
                sub_questions=[],
                strategy=strategy or "direct",
                risk_level="low",
                requires_human_review=False,
                citation_check=CitationCheck(has_citation=True, grounded=True),
            )

    monkeypatch.setattr("src.api.routes.agent", FakeAgent())

    response = client.post(
        "/chat/stream",
        json={"question": "测试问题", "session_id": "stream-test", "strategy": "direct", "language": "zh-CN"},
    )

    assert response.status_code == 200
    assert "application/x-ndjson" in response.headers["content-type"]
    assert '"type": "meta"' in response.text
    assert '"type": "token"' in response.text
    assert '"type": "done"' in response.text


def test_chat_stream_passes_language_to_agent(monkeypatch):
    captured = {}

    class FakeAgent:
        def run(self, question, strategy=None, language="zh-CN"):
            captured["language"] = language
            return ChatResponse(
                answer="Answer [1]",
                sources=[],
                sub_questions=[],
                strategy=strategy or "direct",
                risk_level="low",
                requires_human_review=False,
                citation_check=CitationCheck(has_citation=True, grounded=True),
            )

    monkeypatch.setattr("src.api.routes.agent", FakeAgent())

    response = client.post(
        "/chat/stream",
        json={"question": "test question", "session_id": "stream-test", "language": "en"},
    )

    assert response.status_code == 200
    assert captured["language"] == "en"
