"""Row types returned from DB queries."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class OrderRow:
    id: int
    symbol: str
    side: str  # "buy" | "sell"
    order_type: str  # "market" | "limit" | "stop"
    qty: int
    price: float | None
    status: str  # "pending" | "filled" | "cancelled" | "rejected"
    signal_id: str | None
    created_at: str  # ISO timestamp
    filled_at: str | None
    fill_price: float | None
    notes: str | None


@dataclass
class PositionRow:
    id: int
    symbol: str
    side: str  # "long" | "short"
    qty: int
    entry_price: float
    current_price: float
    unrealized_pnl: float
    opened_at: str
    updated_at: str


@dataclass
class TradeLogRow:
    id: int
    timestamp: str
    level: str  # "INFO" | "WARN" | "ERROR" | "SIGNAL"
    message: str
    payload: str | None  # JSON dump
