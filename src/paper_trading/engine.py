"""Paper trading engine — signal in, paper fill out."""

from __future__ import annotations

from datetime import datetime, timezone

from src.config import SETTINGS
from src.db.database import get_connection, log_event
from src.paper_trading.models import Order, Position
from src.webhook.models import TradingViewAlert


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _get_open_position(symbol: str) -> Position | None:
    """Fetch the current open position for *symbol*, or None if flat."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT side, qty, entry_price, current_price FROM positions WHERE symbol = ? ORDER BY id DESC LIMIT 1",
            (symbol,),
        ).fetchone()
    if row is None:
        return None
    return Position(
        symbol=symbol,
        side=row["side"],
        qty=row["qty"],
        entry_price=row["entry_price"],
        current_price=row["current_price"],
    )


def _update_position(symbol: str, side: str, qty: int, price: float) -> None:
    """Upsert: replace the open position for this symbol."""
    now = _now_iso()
    with get_connection() as conn:
        conn.execute("DELETE FROM positions WHERE symbol = ?", (symbol,))
        conn.execute(
            "INSERT INTO positions (symbol, side, qty, entry_price, current_price, opened_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (symbol, side, qty, price, price, now, now),
        )


def _close_position(symbol: str) -> None:
    """Remove the open position for this symbol (flat)."""
    with get_connection() as conn:
        conn.execute("DELETE FROM positions WHERE symbol = ?", (symbol,))


def _signal_exists(signal_id: str) -> bool:
    """Return True if a signal with this ID was already processed."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT 1 FROM orders WHERE signal_id = ? LIMIT 1", (signal_id,)
        ).fetchone()
    return row is not None


def _insert_order(
    symbol: str,
    side: str,
    qty: int,
    status: str,
    fill_price: float | None,
    signal_id: str | None,
    notes: str | None,
) -> Order:
    now = _now_iso()
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO orders (symbol, side, qty, status, fill_price, signal_id, filled_at, notes) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (symbol, side, qty, status, fill_price, signal_id,
             now if status == "filled" else None, notes),
        )
        order_id = cur.lastrowid
        assert order_id is not None, "lastrowid should never be None after INSERT"
    return Order(
        id=order_id,
        symbol=symbol,
        side=side,
        qty=qty,
        status=status,
        fill_price=fill_price,
        signal_id=signal_id,
        created_at=now,
        filled_at=now if status == "filled" else None,
        notes=notes,
    )


def process_signal(alert: TradingViewAlert) -> Order:
    """Convert a TradingView alert into a paper order with immediate fill.

    Rules (YAGNI — just enough for Phase 1):
      - 'buy'    -> open/reverse/scale long
      - 'sell'   -> open/reverse/scale short
      - 'exit' / 'exit_long' / 'exit_short' / 'close_all' -> flatten
    """
    action = alert.action.lower()
    symbol = alert.ticker.upper()
    qty = alert.qty or SETTINGS.default_qty
    price = alert.price
    signal_id = alert.signal_id

    current = _get_open_position(symbol)

    # --- Resolve action -> desired side -----------------------------------
    if action in ("buy",):
        desired_side = "long"
    elif action in ("sell",):
        desired_side = "short"
    elif action in ("exit", "exit_long", "exit_short", "close_all"):
        desired_side = "flat"
    else:
        raise ValueError(f"Unknown action: {action}")

    flat = current is None

    # --- Dedup: reject if signal_id already processed ------------------------
    if signal_id and _signal_exists(signal_id):
        raise ValueError(f"Duplicate signal: {signal_id} already processed")

    # --- Flat -> enter ----------------------------------------------------
    if flat:
        if desired_side == "flat":
            return _insert_order(symbol, "buy", 0, "cancelled", None, signal_id,
                                 "Already flat — nothing to close")
        order_side = "buy" if desired_side == "long" else "sell"
        _update_position(symbol, desired_side, qty, price or 0.0)
        log_event("INFO", f"Opened {desired_side.upper()} {qty} {symbol} @ {price or 'market'}")
        return _insert_order(symbol, order_side, qty, "filled", price, signal_id, None)

    # --- In position -> manage --------------------------------------------
    if desired_side == current.side:
        raise ValueError(
            f"Already {current.side.upper()} {current.qty} {symbol}. "
            "Scaling not supported in Phase 1."
        )
    elif desired_side == "flat":
        # Map position side to order side: closing long = sell, closing short = buy
        close_side = "sell" if current.side == "long" else "buy"
        pnl = (price - current.entry_price) * current.qty if price and current.side == "long" else \
              (current.entry_price - price) * current.qty if price else 0.0
        _close_position(symbol)
        log_event("INFO", f"Closed {current.side.upper()} {current.qty} {symbol} "
                          f"@ {price or 'market'} — PnL: {pnl:.2f}")
        return _insert_order(symbol, close_side, current.qty, "filled", price, signal_id,
                             f"Close {current.side.upper()} — PnL {pnl:.2f}")
    else:
        # Reverse: close current, open opposite
        # Map desired_side to order side for the new position: long = buy, short = sell
        order_side = "buy" if desired_side == "long" else "sell"
        _close_position(symbol)
        _update_position(symbol, desired_side, qty, price or 0.0)
        log_event("INFO", f"Reversed {current.side.upper()} -> {desired_side.upper()} {qty} {symbol}")
        return _insert_order(symbol, order_side, qty, "filled", price, signal_id,
                             f"Reverse from {current.side.upper()}")
