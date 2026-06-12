"""Pydantic models shared by API, Agent, and RAG layers."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


RiskLevel = Literal["low", "medium", "high"]
RetrievalStrategy = Literal["direct", "hyde", "decompose", "hybrid"]
LanguageCode = Literal["zh-CN", "zh-TW", "en", "ja", "de"]


class Evidence(BaseModel):
    """A retrieved document chunk with traceable metadata."""

    id: str
    content: str
    source: str
    score: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class CitationCheck(BaseModel):
    has_citation: bool
    grounded: bool
    missing_sources: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class TraceStep(BaseModel):
    title: str
    detail: str
    status: Literal["done", "warning", "error"] = "done"


class TimingMetrics(BaseModel):
    total_ms: float = 0.0
    retrieval_ms: float = 0.0
    rerank_ms: float = 0.0
    generation_ms: float = 0.0
    validation_ms: float = 0.0


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=2, description="User question")
    session_id: str = Field("default", description="Conversation id")
    strategy: RetrievalStrategy | None = Field(None, description="Optional retrieval strategy")
    language: LanguageCode = Field("zh-CN", description="Response language")


class ChatResponse(BaseModel):
    answer: str
    sources: list[Evidence] = Field(default_factory=list)
    sub_questions: list[str] = Field(default_factory=list)
    strategy: RetrievalStrategy = "direct"
    risk_level: RiskLevel = "low"
    requires_human_review: bool = False
    citation_check: CitationCheck
    trace_steps: list[TraceStep] = Field(default_factory=list)
    timing: TimingMetrics = Field(default_factory=TimingMetrics)


class ConversationMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str
