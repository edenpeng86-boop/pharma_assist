"""FastAPI application entrypoint."""

from __future__ import annotations

import uvicorn
from fastapi import FastAPI

from src.api.routes import router
from src.core.config import config


app = FastAPI(
    title="PharmAssist API",
    description="Traceable GMP compliance RAG Agent",
    version="0.1.0",
)
app.include_router(router)


if __name__ == "__main__":
    server_cfg = config.get("server", {})
    uvicorn.run(
        "src.api.app:app",
        host=server_cfg.get("host", "0.0.0.0"),
        port=int(server_cfg.get("port", 8000)),
        reload=False,
    )
