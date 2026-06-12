"""Embedding providers."""

from __future__ import annotations

import hashlib
import math
from typing import Any

import httpx

from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings

from src.core.config import config


class HashEmbeddings(Embeddings):
    """Deterministic local embeddings for demos without external services."""

    def __init__(self, dimensions: int = 256) -> None:
        self.dimensions = dimensions

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimensions
        for token in _tokenize(text):
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            idx = int.from_bytes(digest[:4], "big") % self.dimensions
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[idx] += sign
        norm = math.sqrt(sum(item * item for item in vector)) or 1.0
        return [item / norm for item in vector]


class OllamaEmbeddings(Embeddings):
    """Embeddings backed by Ollama's /api/embed endpoint."""

    def __init__(self, model: str = "bge-m3", base_url: str = "http://localhost:11434") -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        return self._embed(texts)

    def embed_query(self, text: str) -> list[float]:
        return self._embed([text])[0]

    def _embed(self, inputs: list[str]) -> list[list[float]]:
        payload: dict[str, Any] = {
            "model": self.model,
            "input": inputs,
        }
        with httpx.Client(timeout=120) as client:
            response = client.post(f"{self.base_url}/api/embed", json=payload)
            response.raise_for_status()
            data = response.json()

        embeddings = data.get("embeddings")
        if not isinstance(embeddings, list) or not embeddings:
            raise ValueError("Ollama /api/embed returned no embeddings.")
        return embeddings


def _tokenize(text: str) -> list[str]:
    compact = "".join(ch.lower() if ch.isalnum() else " " for ch in text)
    words = compact.split()
    chars = [ch for ch in text if "\u4e00" <= ch <= "\u9fff"]
    return words + chars


def get_embeddings() -> Embeddings:
    emb_cfg = config["embedding"]
    provider = str(emb_cfg.get("provider", "openai")).lower()
    if provider == "ollama":
        return OllamaEmbeddings(
            model=emb_cfg.get("model", "bge-m3"),
            base_url=emb_cfg.get("base_url", "http://localhost:11434"),
        )
    if emb_cfg.get("api_key"):
        return OpenAIEmbeddings(
            model=emb_cfg.get("model", "text-embedding-3-small"),
            api_key=emb_cfg.get("api_key"),
            base_url=emb_cfg.get("base_url"),
        )
    return HashEmbeddings()
