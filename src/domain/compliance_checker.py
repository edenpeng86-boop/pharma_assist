"""Compliance response policy."""

from __future__ import annotations

from src.core.config import config
from src.core.models import CitationCheck, RiskLevel


def requires_human_review(risk_level: RiskLevel, citation_check: CitationCheck) -> bool:
    if not citation_check.grounded:
        return True
    if config.get("agent", {}).get("high_risk_requires_review", True) and risk_level == "high":
        return True
    return False
