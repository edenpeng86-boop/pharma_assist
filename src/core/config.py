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


def load_config() -> dict[str, Any]:
    """Load config/config.yaml, optional config/local.yaml, and environment secrets."""
    load_dotenv(ROOT_DIR / ".env")

    configured_path = os.getenv("PHARMASSIST_CONFIG")
    config_path = ROOT_DIR / configured_path if configured_path else ROOT_DIR / "config" / "config.yaml"

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    local_path = ROOT_DIR / "config" / "local.yaml"
    if local_path.exists():
        with open(local_path, "r", encoding="utf-8") as f:
            config = _deep_merge(config, yaml.safe_load(f) or {})

    api_key = os.getenv("OPENAI_API_KEY", "")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    config.setdefault("llm", {})["api_key"] = api_key
    config.setdefault("llm", {})["base_url"] = base_url
    config.setdefault("embedding", {})["api_key"] = api_key
    config.setdefault("embedding", {})["base_url"] = base_url
    return config


config = load_config()
