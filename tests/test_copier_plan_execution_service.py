"""Unit tests for copier plan -> execution request bridge."""
from decimal import Decimal

from app.services.copier_plan_execution_service import (
    CopierPlanExecutionItem,
    build_execution_items_from_copier_plan,
)
from app.services.copier_planning_service import CopierPlanItem


def _plan_item(action: str, account_id: int = 1, exchange: str = "bingx") -> CopierPlanItem:
    return CopierPlanItem(
        account_id=account_id,
        exchange=exchange,
        symbol="BTCUSDT",
        side="buy",
        action=action,
        target_quantity=Decimal("10"),
        delta_quantity=Decimal("10") if action == "open" else (Decimal("0") if action == "hold" else Decimal("3")),
        reason="open_new" if action == "open" else "already_synced" if action == "hold" else "increase_to_master" if action == "increase" else "reduce_to_master",
    )


def test_build_execution_items_open_creates_execution_request():
    """open -> execution_request is built and item is in result."""
    plan = [_plan_item("open")]
    items = build_execution_items_from_copier_plan(
        plan_items=plan,
        current_price=Decimal("50000"),
        risk_percent=Decimal("0.01"),
        leverage=Decimal("2"),
        execution_mode="live",
        run_id="run-1",
    )
    assert len(items) == 1
    assert isinstance(items[0], CopierPlanExecutionItem)
    assert items[0].action == "open"
    assert items[0].execution_request is not None
    assert items[0].execution_request.account_id == 1
    assert items[0].execution_request.exchange == "bingx"
    assert items[0].execution_request.symbol == "BTCUSDT"
    assert items[0].execution_request.side == "buy"
    assert items[0].execution_request.run_id == "run-1"
    assert items[0].execution_request.execution_mode == "live"


def test_build_execution_items_increase_creates_execution_request():
    """increase -> execution_request is built."""
    plan = [_plan_item("increase")]
    items = build_execution_items_from_copier_plan(
        plan_items=plan,
        current_price=Decimal("50000"),
        risk_percent=Decimal("0.01"),
        leverage=Decimal("2"),
        execution_mode="simulated",
        run_id="run-2",
    )
    assert len(items) == 1
    assert items[0].action == "increase"
    assert items[0].execution_request.execution_mode == "simulated"
    assert items[0].execution_request.run_id == "run-2"


def test_build_execution_items_reduce_creates_execution_request():
    """reduce -> execution_request is built."""
    plan = [_plan_item("reduce")]
    items = build_execution_items_from_copier_plan(
        plan_items=plan,
        current_price=Decimal("50000"),
        risk_percent=Decimal("0.01"),
        leverage=Decimal("2"),
        execution_mode="live",
        run_id="run-3",
    )
    assert len(items) == 1
    assert items[0].action == "reduce"
    assert items[0].execution_request is not None


def test_build_execution_items_hold_excluded_from_result():
    """hold -> item is not included in result (no execution needed)."""
    plan = [_plan_item("hold")]
    items = build_execution_items_from_copier_plan(
        plan_items=plan,
        current_price=Decimal("50000"),
        risk_percent=Decimal("0.01"),
        leverage=Decimal("2"),
        execution_mode="live",
        run_id="run-4",
    )
    assert len(items) == 0


def test_build_execution_items_mixed_plan_hold_excluded_others_included():
    """Mixed plan: open and reduce in result, hold excluded."""
    plan = [
        _plan_item("open", account_id=1),
        _plan_item("hold", account_id=2),
        _plan_item("reduce", account_id=3, exchange="stub"),
    ]
    items = build_execution_items_from_copier_plan(
        plan_items=plan,
        current_price=Decimal("50000"),
        risk_percent=Decimal("0.01"),
        leverage=Decimal("2"),
        execution_mode="live",
        run_id="run-5",
    )
    assert len(items) == 2
    assert items[0].action == "open" and items[0].account_id == 1
    assert items[1].action == "reduce" and items[1].account_id == 3 and items[1].exchange == "stub"
    assert all(i.execution_request is not None for i in items)
