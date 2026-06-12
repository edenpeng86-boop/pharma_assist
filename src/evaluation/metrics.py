"""Small evaluation metrics for the portfolio demo."""

from __future__ import annotations

from src.core.models import ChatResponse


def source_hit(response: ChatResponse, expected_source: str) -> bool:
    return any(item.source == expected_source for item in response.sources)


def keyword_hit(response: ChatResponse, expected_keywords: list[str]) -> float:
    if not expected_keywords:
        return 1.0
    hits = sum(1 for keyword in expected_keywords if keyword in response.answer)
    return hits / len(expected_keywords)
