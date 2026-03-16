"""Unit tests for master position event contract."""
from decimal import Decimal

from app.core.master_position import MasterPositionEvent


def test_master_position_event_dataclass_creates_correctly():
    """MasterPositionEvent dataclass creates with all fields."""
    ev = MasterPositionEvent(
        source_exchange="bingx",
        source_account_id=1,
        symbol="BTCUSDT",
        side="buy",
        quantity=Decimal("0.05"),
        entry_price=Decimal("50000"),
        event_type="position_update",
    )
    assert ev.source_exchange == "bingx"
    assert ev.source_account_id == 1
    assert ev.symbol == "BTCUSDT"
    assert ev.side == "buy"
    assert ev.quantity == Decimal("0.05")
    assert ev.entry_price == Decimal("50000")
    assert ev.event_type == "position_update"


def test_master_position_event_decimal_fields_preserved():
    """Decimal quantity and entry_price are stored and comparable."""
    ev = MasterPositionEvent(
        source_exchange="stub",
        source_account_id=None,
        symbol="ETHUSDT",
        side="sell",
        quantity=Decimal("1.234"),
        entry_price=Decimal("3000.50"),
        event_type="snapshot",
    )
    assert ev.quantity == Decimal("1.234")
    assert ev.entry_price == Decimal("3000.50")
    assert ev.quantity + Decimal("0.001") == Decimal("1.235")
    assert ev.source_account_id is None


def test_master_position_event_typed_contract_access():
    """event_type, side, symbol are accessible as typed contract."""
    ev = MasterPositionEvent(
        source_exchange="binance",
        source_account_id=42,
        symbol="BTC-USDT",
        side="buy",
        quantity=Decimal("0.02"),
        entry_price=Decimal("60000"),
        event_type="open",
    )
    assert ev.event_type == "open"
    assert ev.side == "buy"
    assert ev.symbol == "BTC-USDT"
