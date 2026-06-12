"""Simple risk classifier for GMP compliance questions."""

from __future__ import annotations

from src.core.models import RiskLevel


HIGH_RISK_TERMS = {"放行", "无菌", "灭菌", "重大偏差", "召回", "质量事故", "数据完整性"}
MEDIUM_RISK_TERMS = {"偏差", "CAPA", "洁净", "污染", "交叉污染", "变更", "验证", "确认"}


def classify_risk(question: str) -> RiskLevel:
    if any(term in question for term in HIGH_RISK_TERMS):
        return "high"
    if any(term in question for term in MEDIUM_RISK_TERMS):
        return "medium"
    return "low"
