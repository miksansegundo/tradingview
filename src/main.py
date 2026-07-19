"""FastAPI application entry point."""

from __future__ import annotations

import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager

from src.config import SETTINGS
from src.db.database import init_db, log_event
from src.webhook.router import router as webhook_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    init_db()
    log_event("INFO", "Server started", {
        "symbol": SETTINGS.default_symbol,
        "port": SETTINGS.port,
        "webhook_secret": "SET" if SETTINGS.webhook_secret else "NONE",
    })
    yield


app = FastAPI(
    title="TradingView Paper Trader",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(webhook_router)


@app.get("/health")
async def health():
    return {"status": "ok", "symbol": SETTINGS.default_symbol}


if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host=SETTINGS.host,
        port=SETTINGS.port,
        reload=True,
    )
