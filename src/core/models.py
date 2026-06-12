"""Pydantic models shared by API, Agent, and RAG layers."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


RiskLevel = Literal["low", "medium", "high"]
RetrievalStrategy = Literal["direct", "hyde", "decompose", "hybrid"]


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


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=2, description="User question")
    session_id: str = Field("default", description="Conversation id")
    strategy: RetrievalStrategy | None = Field(None, description="Optional retrieval strategy")


class ChatResponse(BaseModel):
    answer: str
    sources: list[Evidence] = Field(default_factory=list)
    sub_questions: list[str] = Field(default_factory=list)
    strategy: RetrievalStrategy = "direct"
    risk_level: RiskLevel = "low"
    requires_human_review: bool = False
    citation_check: CitationCheck


class ConversationMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str
