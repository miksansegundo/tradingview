"""Webhook endpoint for TradingView alerts."""

from __future__ import annotations

import secrets

from fastapi import APIRouter, Header, HTTPException, Request

from src.config import SETTINGS
from src.db.database import log_event
from src.paper_trading.engine import process_signal
from src.webhook.models import TradingViewAlert, WebhookResponse

router = APIRouter(prefix="/webhook", tags=["webhook"])


@router.post("/tradingview", response_model=WebhookResponse)
async def receive_alert(
    payload: TradingViewAlert,
    request: Request,
    x_webhook_secret: str | None = Header(default=None),
) -> WebhookResponse:
    """Receive a strategy alert from TradingView and route it to the paper engine."""

    # --- Security check --------------------------------------------------
    if SETTINGS.webhook_secret:
        provided = x_webhook_secret or ""
        if not secrets.compare_digest(SETTINGS.webhook_secret, provided):
            log_event("WARN", "Webhook rejected: invalid secret", {
                "ip": request.client.host if request.client else "unknown",
                "ticker": payload.ticker,
                "action": payload.action,
            })
            raise HTTPException(status_code=403, detail="Invalid webhook secret")

    # --- Log incoming signal ---------------------------------------------
    log_event("SIGNAL", f"Signal received: {payload.action} {payload.ticker}", payload.model_dump())

    # --- Process via paper engine ----------------------------------------
    try:
        order = process_signal(payload)
        log_event("INFO", f"Order {order.status}: {order.side} {order.qty} {payload.ticker}", {
            "order_id": order.id,
            "status": order.status,
            "fill_price": order.fill_price,
        })
        return WebhookResponse(
            status="ok",
            order_id=order.id,
            message=f"{order.side.upper()} {order.qty} {payload.ticker} — {order.status}",
        )
    except ValueError as exc:
        log_event("ERROR", f"Order rejected: {exc}", {"ticker": payload.ticker, "action": payload.action})
        return WebhookResponse(status="error", message=str(exc))
