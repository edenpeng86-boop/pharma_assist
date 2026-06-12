from src.rag.embeddings import OllamaEmbeddings


def test_ollama_embeddings_uses_embed_endpoint(monkeypatch):
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {"embeddings": [[0.1, 0.2], [0.3, 0.4]]}

    class FakeClient:
        def __init__(self, timeout):
            captured["timeout"] = timeout

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

        def post(self, url, json):
            captured["url"] = url
            captured["json"] = json
            return FakeResponse()

    monkeypatch.setattr("src.rag.embeddings.httpx.Client", FakeClient)

    embeddings = OllamaEmbeddings(model="bge-m3", base_url="http://localhost:11434/")
    result = embeddings.embed_documents(["a", "b"])

    assert result == [[0.1, 0.2], [0.3, 0.4]]
    assert captured["url"] == "http://localhost:11434/api/embed"
    assert captured["json"] == {"model": "bge-m3", "input": ["a", "b"]}
