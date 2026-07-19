"""Pydantic models for incoming TradingView webhook payloads."""

from __future__ import annotations

from pydantic import BaseModel, Field


class TradingViewAlert(BaseModel):
    """Schema for TradingView strategy alert webhook payload.

    TradingView sends a POST with Content-Type application/json.
    The user configures the alert message as a JSON string containing
    these fields. We accept extras so unknown fields don't cause a 422.
    """

    ticker: str = Field(default="MPL", description="Symbol the alert fired on")
    action: str = Field(..., description="'buy', 'sell', 'exit_long', 'exit_short', or 'close_all'")
    price: float | None = Field(default=None, description="Current price when alert fired")
    qty: int | None = Field(default=None, description="Quantity to trade (default from settings)")
    strategy: str | None = Field(default=None, description="Strategy name for traceability")
    signal_id: str | None = Field(default=None, description="Unique signal ID for dedup")
    metadata: dict[str, object] | None = Field(default=None, description="Additional context from strategy")


class WebhookResponse(BaseModel):
    """Standard response returned to TradingView's webhook POST."""
    status: str  # "ok" | "error"
    order_id: int | None = None
    message: str = ""
