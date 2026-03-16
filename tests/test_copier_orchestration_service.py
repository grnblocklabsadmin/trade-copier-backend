"""Unit tests for copier orchestration service."""
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.schemas.copier import CopierDispatchItem
from app.services.copier_orchestration_service import (
    CopierOrchestrationResult,
    execute_copier_from_master_position,
)
from app.services.copier_plan_execution_service import CopierPlanExecutionItem
from app.services.copier_planning_service import CopierPlanItem


def _account_ref(account_id: int, exchange: str = "bingx"):
    return SimpleNamespace(account_id=account_id, exchange=exchange)


def test_empty_follower_accounts_returns_empty_plan_execution_results_with_run_id():
    """Empty follower_accounts -> empty plan_items, execution_items, results; run_id present."""
    log_service = MagicMock()
    get_account = MagicMock()

    out = execute_copier_from_master_position(
        master_symbol="BTCUSDT",
        master_side="buy",
        master_quantity=Decimal("10"),
        execution_mode="live",
        current_price=Decimal("50000"),
        risk_percent=Decimal("0.01"),
        leverage=Decimal("2"),
        follower_accounts=[],
        follower_positions=None,
        get_account=get_account,
        log_service=log_service,
        run_id=None,
    )

    assert isinstance(out, CopierOrchestrationResult)
    assert out.run_id is not None
    assert len(out.run_id) > 0
    assert out.plan_items == []
    assert out.execution_items == []
    assert out.results == []
    get_account.assert_not_called()


def test_follower_without_position_plan_open_execution_item_runner_called():
    """Follower without position -> plan has action open, execution item built, runner invoked."""
    from app.core.execution_request import ExecutionRequest

    plan_items = [
        CopierPlanItem(
            account_id=1,
            exchange="bingx",
            symbol="BTCUSDT",
            side="buy",
            action="open",
            target_quantity=Decimal("10"),
            delta_quantity=Decimal("10"),
            reason="open_new",
        ),
    ]
    execution_items = [
        CopierPlanExecutionItem(
            account_id=1,
            exchange="bingx",
            symbol="BTCUSDT",
            side="buy",
            action="open",
            execution_request=ExecutionRequest(
                execution_mode="simulated",
                account_id=1,
                exchange="bingx",
                symbol="BTCUSDT",
                side="buy",
                current_price=Decimal("50000"),
                risk_percent=Decimal("0.01"),
                leverage=Decimal("2"),
                run_id="run-fixed",
            ),
            reason="open_new",
        ),
    ]
    dispatch_item = CopierDispatchItem(
        account_id=1,
        exchange="bingx",
        symbol="BTCUSDT",
        side="buy",
        rounded_quantity=Decimal("0.01"),
        final_notional=Decimal("500"),
        is_valid=True,
        validation_errors=[],
        dispatched=True,
        dispatch_status="simulated_dispatched",
        exchange_order_id=None,
        message="ok",
    )

    log_service = MagicMock()
    get_account = MagicMock()

    with (
        patch("app.services.copier_orchestration_service.build_copier_plan_for_accounts", return_value=plan_items),
        patch("app.services.copier_orchestration_service.build_execution_items_from_copier_plan", return_value=execution_items),
        patch(
            "app.services.copier_orchestration_service.execute_copier_plan_items",
            return_value=SimpleNamespace(run_id="run-fixed", results=[dispatch_item]),
        ),
    ):
        out = execute_copier_from_master_position(
            master_symbol="BTCUSDT",
            master_side="buy",
            master_quantity=Decimal("10"),
            execution_mode="simulated",
            current_price=Decimal("50000"),
            risk_percent=Decimal("0.01"),
            leverage=Decimal("2"),
            follower_accounts=[_account_ref(1)],
            follower_positions={},
            get_account=get_account,
            log_service=log_service,
            run_id="run-fixed",
        )

    assert out.run_id == "run-fixed"
    assert len(out.plan_items) == 1
    assert out.plan_items[0].action == "open"
    assert len(out.execution_items) == 1
    assert out.execution_items[0].action == "open"
    assert len(out.results) == 1
    assert out.results[0].account_id == 1
    assert out.results[0].dispatch_status == "simulated_dispatched"


def test_mixed_follower_positions_plan_and_execution_items_expected_length():
    """Mixed follower_positions -> plan has all accounts; execution_items excludes hold."""
    from app.core.execution_request import ExecutionRequest

    # One open, one hold, one reduce -> plan 3, execution 2 (no hold)
    plan_items = [
        CopierPlanItem(account_id=1, exchange="bingx", symbol="BTCUSDT", side="buy", action="open", target_quantity=Decimal("10"), delta_quantity=Decimal("10"), reason="open_new"),
        CopierPlanItem(account_id=2, exchange="stub", symbol="BTCUSDT", side="buy", action="hold", target_quantity=Decimal("10"), delta_quantity=Decimal("0"), reason="already_synced"),
        CopierPlanItem(account_id=3, exchange="bingx", symbol="BTCUSDT", side="buy", action="reduce", target_quantity=Decimal("10"), delta_quantity=Decimal("5"), reason="reduce_to_master"),
    ]
    execution_items = [
        CopierPlanExecutionItem(
            account_id=1, exchange="bingx", symbol="BTCUSDT", side="buy", action="open",
            execution_request=ExecutionRequest(execution_mode="live", account_id=1, exchange="bingx", symbol="BTCUSDT", side="buy", current_price=Decimal("1"), risk_percent=Decimal("0.01"), leverage=Decimal("1"), run_id="r"),
            reason="open_new",
        ),
        CopierPlanExecutionItem(
            account_id=3, exchange="bingx", symbol="BTCUSDT", side="buy", action="reduce",
            execution_request=ExecutionRequest(execution_mode="live", account_id=3, exchange="bingx", symbol="BTCUSDT", side="buy", current_price=Decimal("1"), risk_percent=Decimal("0.01"), leverage=Decimal("1"), run_id="r"),
            reason="reduce_to_master",
        ),
    ]
    log_service = MagicMock()
    get_account = MagicMock()

    with (
        patch("app.services.copier_orchestration_service.build_copier_plan_for_accounts", return_value=plan_items),
        patch("app.services.copier_orchestration_service.build_execution_items_from_copier_plan", return_value=execution_items),
        patch("app.services.copier_orchestration_service.execute_copier_plan_items", return_value=SimpleNamespace(run_id="r", results=[MagicMock(), MagicMock()])),
    ):
        out = execute_copier_from_master_position(
            master_symbol="BTCUSDT",
            master_side="buy",
            master_quantity=Decimal("10"),
            execution_mode="live",
            current_price=Decimal("50000"),
            risk_percent=Decimal("0.01"),
            leverage=Decimal("2"),
            follower_accounts=[_account_ref(1), _account_ref(2), _account_ref(3)],
            follower_positions={1: Decimal("0"), 2: Decimal("10"), 3: Decimal("15")},
            get_account=get_account,
            log_service=log_service,
            run_id="r",
        )

    assert len(out.plan_items) == 3
    assert len(out.execution_items) == 2
    assert len(out.results) == 2
    assert out.plan_items[1].action == "hold"
    assert out.execution_items[0].account_id == 1 and out.execution_items[1].account_id == 3
