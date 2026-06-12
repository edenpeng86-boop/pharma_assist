"""FastAPI routes."""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import AsyncIterator

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import FileResponse, StreamingResponse

from src.agent.memory import memory
from src.agent.workflow import PharmAssistAgent
from src.core.models import ChatRequest, ChatResponse


router = APIRouter()
agent = PharmAssistAgent()
WEB_DIR = Path(__file__).resolve().parents[1] / "web"
logger = logging.getLogger(__name__)


@router.get("/")
async def index() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


@router.get("/favicon.ico", include_in_schema=False)
async def favicon() -> Response:
    return Response(status_code=204)


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    try:
        logger.info(
            "chat.start session_id=%s strategy=%s question=%s",
            request.session_id,
            request.strategy or "default",
            request.question,
        )
        response = agent.run(request.question, request.strategy, request.language)
        memory.add(request.session_id, "user", request.question)
        memory.add(request.session_id, "assistant", response.answer)
        logger.info(
            "chat.end session_id=%s risk_level=%s sources=%s review=%s",
            request.session_id,
            response.risk_level,
            len(response.sources),
            response.requires_human_review,
        )
        return response
    except Exception as exc:
        logger.exception(
            "chat.error session_id=%s question=%s",
            request.session_id,
            request.question,
        )
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest) -> StreamingResponse:
    async def event_stream() -> AsyncIterator[str]:
        try:
            logger.info(
                "chat_stream.start session_id=%s strategy=%s question=%s",
                request.session_id,
                request.strategy or "default",
                request.question,
            )
            yield _json_line({"type": "status", "message": "retrieving"})

            response = await asyncio.to_thread(agent.run, request.question, request.strategy, request.language)
            memory.add(request.session_id, "user", request.question)
            memory.add(request.session_id, "assistant", response.answer)

            meta = response.model_dump(exclude={"answer"})
            yield _json_line({"type": "meta", "data": meta})

            for chunk in _chunk_text(response.answer):
                yield _json_line({"type": "token", "content": chunk})
                await asyncio.sleep(0.01)

            logger.info(
                "chat_stream.end session_id=%s risk_level=%s sources=%s review=%s",
                request.session_id,
                response.risk_level,
                len(response.sources),
                response.requires_human_review,
            )
            yield _json_line({"type": "done"})
        except Exception as exc:
            logger.exception(
                "chat_stream.error session_id=%s question=%s",
                request.session_id,
                request.question,
            )
            yield _json_line({"type": "error", "message": str(exc)})

    return StreamingResponse(event_stream(), media_type="application/x-ndjson")


def _json_line(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False) + "\n"


def _chunk_text(text: str, size: int = 8) -> list[str]:
    return [text[index : index + size] for index in range(0, len(text), size)]


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
