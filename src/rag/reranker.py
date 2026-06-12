"""Lightweight reranking for retrieved evidence."""

from __future__ import annotations

from src.core.models import Evidence


class SimpleReranker:
    """Token-overlap reranker used as an explainable MVP baseline."""

    def rerank(self, query: str, evidence: list[Evidence], top_k: int = 4) -> list[Evidence]:
        query_terms = set(_terms(query))
        scored: list[Evidence] = []
        for item in evidence:
            doc_terms = set(_terms(item.content))
            overlap = len(query_terms & doc_terms)
            union = len(query_terms | doc_terms) or 1
            item.score = round((overlap / union) + item.score, 4)
            scored.append(item)
        return sorted(scored, key=lambda item: item.score, reverse=True)[:top_k]


def _terms(text: str) -> list[str]:
    compact = "".join(ch.lower() if ch.isalnum() else " " for ch in text)
    words = compact.split()
    chars = [ch for ch in text if "\u4e00" <= ch <= "\u9fff"]
    return words + chars
