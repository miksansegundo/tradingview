"""Paper trading domain models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Order:
    """A paper order — created on signal, immediately filled."""
    id: int
    symbol: str
    side: str  # "buy" | "sell"
    qty: int
    status: str  # "filled" | "rejected"
    fill_price: float | None
    signal_id: str | None
    created_at: str
    filled_at: str | None
    notes: str | None = None


@dataclass
class Position:
    """Current open position for a symbol."""
    symbol: str
    side: str  # "long" | "short"
    qty: int
    entry_price: float
    current_price: float
