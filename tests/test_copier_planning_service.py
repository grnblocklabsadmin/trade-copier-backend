"""Unit tests for copier planning service."""
from decimal import Decimal
from types import SimpleNamespace

from app.services.copier_planning_service import (
    CopierPlanItem,
    build_copier_plan_for_accounts,
)


def _account(account_id: int, exchange: str = "bingx"):
    return SimpleNamespace(account_id=account_id, exchange=exchange)


def test_build_copier_plan_no_position_action_open():
    """No follower position -> plan item with action=open."""
    plan = build_copier_plan_for_accounts(
        master_symbol="BTCUSDT",
        master_side="buy",
        master_quantity=Decimal("10"),
        execution_mode="live",
        follower_accounts=[_account(1)],
        follower_positions={},
    )
    assert len(plan) == 1
    item = plan[0]
    assert isinstance(item, CopierPlanItem)
    assert item.account_id == 1
    assert item.exchange == "bingx"
    assert item.symbol == "BTCUSDT"
    assert item.side == "buy"
    assert item.action == "open"
    assert item.target_quantity == Decimal("10")
    assert item.delta_quantity == Decimal("10")
    assert item.reason == "open_new"


def test_build_copier_plan_position_equals_master_action_hold():
    """Follower position equals master -> action=hold."""
    plan = build_copier_plan_for_accounts(
        master_symbol="BTCUSDT",
        master_side="buy",
        master_quantity=Decimal("10"),
        execution_mode="live",
        follower_accounts=[_account(1)],
        follower_positions={1: Decimal("10")},
    )
    assert len(plan) == 1
    assert plan[0].action == "hold"
    assert plan[0].delta_quantity == Decimal("0")
    assert plan[0].reason == "already_synced"


def test_build_copier_plan_position_less_than_master_action_increase():
    """Follower position less than master -> action=increase."""
    plan = build_copier_plan_for_accounts(
        master_symbol="BTCUSDT",
        master_side="sell",
        master_quantity=Decimal("10"),
        execution_mode="simulated",
        follower_accounts=[_account(1, "stub")],
        follower_positions={1: Decimal("3")},
    )
    assert len(plan) == 1
    assert plan[0].action == "increase"
    assert plan[0].target_quantity == Decimal("10")
    assert plan[0].delta_quantity == Decimal("7")
    assert plan[0].reason == "increase_to_master"
    assert plan[0].exchange == "stub"


def test_build_copier_plan_position_greater_than_master_action_reduce():
    """Follower position greater than master -> action=reduce."""
    plan = build_copier_plan_for_accounts(
        master_symbol="ETHUSDT",
        master_side="buy",
        master_quantity=Decimal("5"),
        execution_mode="live",
        follower_accounts=[_account(2)],
        follower_positions={2: Decimal("15")},
    )
    assert len(plan) == 1
    assert plan[0].action == "reduce"
    assert plan[0].target_quantity == Decimal("5")
    assert plan[0].delta_quantity == Decimal("10")
    assert plan[0].reason == "reduce_to_master"


def test_build_copier_plan_multiple_accounts():
    """Multiple followers -> one plan item per account, each with correct action."""
    plan = build_copier_plan_for_accounts(
        master_symbol="BTCUSDT",
        master_side="buy",
        master_quantity=Decimal("10"),
        execution_mode="live",
        follower_accounts=[_account(1), _account(2, "stub")],
        follower_positions={1: Decimal("0"), 2: Decimal("10")},
    )
    assert len(plan) == 2
    by_id = {p.account_id: p for p in plan}
    assert by_id[1].action == "open"
    assert by_id[2].action == "hold"
