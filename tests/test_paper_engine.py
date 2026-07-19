"""Paper trading engine tests."""

import pytest

from src.paper_trading.engine import process_signal, _get_open_position
from src.webhook.models import TradingViewAlert


def _alert(action: str, price: float = 1000.0, qty: int = 1, signal_id: str | None = None):
    return TradingViewAlert(ticker="MPL", action=action, price=price, qty=qty, signal_id=signal_id)


class TestOpenPosition:
    def test_buy_opens_long(self):
        order = process_signal(_alert("buy", 1000.0))
        assert order.status == "filled"
        assert order.side == "buy"
        pos = _get_open_position("MPL")
        assert pos is not None
        assert pos.side == "long"
        assert pos.qty == 1

    def test_sell_opens_short(self):
        order = process_signal(_alert("sell", 1000.0))
        assert order.status == "filled"
        assert order.side == "sell"
        pos = _get_open_position("MPL")
        assert pos is not None
        assert pos.side == "short"

    def test_buy_twice_rejected(self):
        process_signal(_alert("buy", 1000.0))
        with pytest.raises(ValueError, match="Already LONG"):
            process_signal(_alert("buy", 1010.0))

    def test_sell_twice_rejected(self):
        process_signal(_alert("sell", 1000.0))
        with pytest.raises(ValueError, match="Already SHORT"):
            process_signal(_alert("sell", 990.0))


class TestClosePosition:
    def test_exit_long_flattens(self):
        process_signal(_alert("buy", 1000.0))
        order = process_signal(_alert("exit_long", 1010.0))
        assert order.status == "filled"
        assert order.side == "sell"  # closing long = sell
        assert _get_open_position("MPL") is None

    def test_exit_short_flattens(self):
        process_signal(_alert("sell", 1000.0))
        order = process_signal(_alert("exit_short", 990.0))
        assert order.status == "filled"
        assert order.side == "buy"  # closing short = buy
        assert _get_open_position("MPL") is None

    def test_close_all_flattens_long(self):
        process_signal(_alert("buy", 1000.0))
        order = process_signal(_alert("close_all", 1010.0))
        assert order.status == "filled"
        assert _get_open_position("MPL") is None

    def test_exit_when_flat_is_noop(self):
        order = process_signal(_alert("close_all", 1000.0))
        assert order.status == "cancelled"


class TestReverse:
    def test_buy_then_sell_reverses_to_short(self):
        process_signal(_alert("buy", 1000.0))
        order = process_signal(_alert("sell", 1000.0))
        assert order.status == "filled"
        pos = _get_open_position("MPL")
        assert pos is not None
        assert pos.side == "short"

    def test_sell_then_buy_reverses_to_long(self):
        process_signal(_alert("sell", 1000.0))
        order = process_signal(_alert("buy", 1000.0))
        assert order.status == "filled"
        pos = _get_open_position("MPL")
        assert pos is not None
        assert pos.side == "long"


class TestDedup:
    def test_duplicate_signal_id_rejected(self):
        sig_id = "dup_001"
        process_signal(_alert("buy", 1000.0, signal_id=sig_id))
        with pytest.raises(ValueError, match="Duplicate signal"):
            process_signal(_alert("buy", 1000.0, signal_id=sig_id))

    def test_different_signal_id_accepted(self):
        process_signal(_alert("buy", 1000.0, signal_id="a"))
        order = process_signal(_alert("exit_long", 1010.0, signal_id="b"))
        assert order.status == "filled"
