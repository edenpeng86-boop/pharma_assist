from src.core.config import load_config


def test_llm_and_embedding_can_use_separate_credentials(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "llm-key")
    monkeypatch.setenv("LLM_BASE_URL", "https://llm.example.com/v1")
    monkeypatch.setenv("LLM_MODEL", "chat-model")
    monkeypatch.setenv("EMBEDDING_API_KEY", "embedding-key")
    monkeypatch.setenv("EMBEDDING_PROVIDER", "ollama")
    monkeypatch.setenv("EMBEDDING_BASE_URL", "https://embedding.example.com/v1")
    monkeypatch.setenv("EMBEDDING_MODEL", "embedding-model")

    cfg = load_config(load_env=False)

    assert cfg["llm"]["api_key"] == "llm-key"
    assert cfg["llm"]["base_url"] == "https://llm.example.com/v1"
    assert cfg["llm"]["model"] == "chat-model"
    assert cfg["embedding"]["api_key"] == "embedding-key"
    assert cfg["embedding"]["provider"] == "ollama"
    assert cfg["embedding"]["base_url"] == "https://embedding.example.com/v1"
    assert cfg["embedding"]["model"] == "embedding-model"


def test_openai_env_is_backward_compatible_fallback(monkeypatch):
    monkeypatch.setenv("EMBEDDING_PROVIDER", "openai")
    for key in [
        "LLM_API_KEY",
        "LLM_BASE_URL",
        "LLM_MODEL",
        "EMBEDDING_API_KEY",
        "EMBEDDING_BASE_URL",
        "EMBEDDING_MODEL",
    ]:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "legacy-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://legacy.example.com/v1")

    cfg = load_config(load_env=False)

    assert cfg["llm"]["api_key"] == "legacy-key"
    assert cfg["llm"]["base_url"] == "https://legacy.example.com/v1"
    assert cfg["embedding"]["api_key"] == "legacy-key"
    assert cfg["embedding"]["base_url"] == "https://legacy.example.com/v1"


def test_ollama_embedding_keeps_local_base_url(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "legacy-key")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://legacy.example.com/v1")
    monkeypatch.setenv("EMBEDDING_PROVIDER", "ollama")
    monkeypatch.delenv("EMBEDDING_API_KEY", raising=False)
    monkeypatch.delenv("EMBEDDING_BASE_URL", raising=False)
    monkeypatch.delenv("EMBEDDING_MODEL", raising=False)

    cfg = load_config(load_env=False)

    assert cfg["embedding"]["provider"] == "ollama"
    assert cfg["embedding"]["api_key"] == ""
    assert cfg["embedding"]["base_url"] == "http://localhost:11434"
