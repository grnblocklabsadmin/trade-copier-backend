"""Unit tests for position sync contract."""
from decimal import Decimal

import pytest

from app.core.position_sync import (
    PositionSyncDecision,
    PositionSyncInput,
    build_position_sync_decision,
)


def _input(
    follower_current_position_quantity: Decimal,
    master_quantity: Decimal = Decimal("10"),
) -> PositionSyncInput:
    return PositionSyncInput(
        master_symbol="BTCUSDT",
        master_side="buy",
        master_quantity=master_quantity,
        follower_account_id=1,
        follower_exchange="bingx",
        follower_current_position_quantity=follower_current_position_quantity,
        execution_mode="live",
    )


def test_build_position_sync_decision_open():
    """Follower has no position -> action open, target and delta = master_quantity."""
    result = build_position_sync_decision(_input(Decimal("0")))
    assert isinstance(result, PositionSyncDecision)
    assert result.action == "open"
    assert result.target_quantity == Decimal("10")
    assert result.delta_quantity == Decimal("10")
    assert result.reason == "open_new"


def test_build_position_sync_decision_hold():
    """Follower position equals master -> action hold, delta = 0."""
    result = build_position_sync_decision(_input(Decimal("10")))
    assert result.action == "hold"
    assert result.target_quantity == Decimal("10")
    assert result.delta_quantity == Decimal("0")
    assert result.reason == "already_synced"


def test_build_position_sync_decision_increase():
    """Follower position less than master -> action increase, delta = master - current."""
    result = build_position_sync_decision(_input(Decimal("3"), master_quantity=Decimal("10")))
    assert result.action == "increase"
    assert result.target_quantity == Decimal("10")
    assert result.delta_quantity == Decimal("7")
    assert result.reason == "increase_to_master"


def test_build_position_sync_decision_reduce():
    """Follower position greater than master -> action reduce, delta = current - master."""
    result = build_position_sync_decision(_input(Decimal("15"), master_quantity=Decimal("10")))
    assert result.action == "reduce"
    assert result.target_quantity == Decimal("10")
    assert result.delta_quantity == Decimal("5")
    assert result.reason == "reduce_to_master"
