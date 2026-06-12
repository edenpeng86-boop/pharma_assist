"""Configuration loading for PharmAssist."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - convenience before requirements install
    def load_dotenv(*args: Any, **kwargs: Any) -> bool:
        return False


ROOT_DIR = Path(__file__).resolve().parents[2]


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_config(load_env: bool = True) -> dict[str, Any]:
    """Load config/config.yaml, optional config/local.yaml, and environment secrets."""
    if load_env:
        load_dotenv(ROOT_DIR / ".env")

    configured_path = os.getenv("PHARMASSIST_CONFIG")
    config_path = ROOT_DIR / configured_path if configured_path else ROOT_DIR / "config" / "config.yaml"

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    local_path = ROOT_DIR / "config" / "local.yaml"
    if local_path.exists():
        with open(local_path, "r", encoding="utf-8") as f:
            config = _deep_merge(config, yaml.safe_load(f) or {})

    legacy_api_key = os.getenv("OPENAI_API_KEY", "")
    legacy_base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

    llm_cfg = config.setdefault("llm", {})
    llm_cfg["api_key"] = os.getenv("LLM_API_KEY", legacy_api_key)
    llm_cfg["base_url"] = os.getenv("LLM_BASE_URL", legacy_base_url)
    if os.getenv("LLM_MODEL"):
        llm_cfg["model"] = os.getenv("LLM_MODEL")

    embedding_cfg = config.setdefault("embedding", {})
    provider = os.getenv("EMBEDDING_PROVIDER", embedding_cfg.get("provider", "openai"))
    embedding_cfg["provider"] = provider
    if os.getenv("EMBEDDING_API_KEY") is not None:
        embedding_cfg["api_key"] = os.getenv("EMBEDDING_API_KEY", "")
    elif provider != "ollama":
        embedding_cfg["api_key"] = legacy_api_key

    if os.getenv("EMBEDDING_BASE_URL") is not None:
        embedding_cfg["base_url"] = os.getenv("EMBEDDING_BASE_URL", "")
    elif provider != "ollama":
        embedding_cfg["base_url"] = legacy_base_url

    if os.getenv("EMBEDDING_MODEL"):
        embedding_cfg["model"] = os.getenv("EMBEDDING_MODEL")
    return config


config = load_config()
