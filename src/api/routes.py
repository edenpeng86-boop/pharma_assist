"""FastAPI routes."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from src.agent.memory import memory
from src.agent.workflow import PharmAssistAgent
from src.core.models import ChatRequest, ChatResponse


router = APIRouter()
agent = PharmAssistAgent()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    try:
        response = agent.run(request.question, request.strategy)
        memory.add(request.session_id, "user", request.question)
        memory.add(request.session_id, "assistant", response.answer)
        return response
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/history/{session_id}")
async def get_history(session_id: str) -> dict:
    return {"history": [item.model_dump() for item in memory.get_history(session_id)]}


@router.delete("/history/{session_id}")
async def clear_history(session_id: str) -> dict[str, str]:
    memory.clear(session_id)
    return {"status": "ok"}


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "pharmassist"}
