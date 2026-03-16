"""Unit tests for copier plan runner service."""
from decimal import Decimal
from unittest.mock import MagicMock

from app.core.execution_request import ExecutionRequest
from app.schemas.copier import ManualCopierDispatchAccount
from app.services.copier_plan_execution_service import CopierPlanExecutionItem
from app.services.copier_plan_runner_service import (
    CopierPlanRunResult,
    execute_copier_plan_items,
)


def _account(account_id: int = 1) -> ManualCopierDispatchAccount:
    return ManualCopierDispatchAccount(
        account_id=account_id,
        exchange="bingx",
        available_balance=Decimal("1000"),
        quantity_step=Decimal("0.001"),
        min_quantity=Decimal("0.001"),
        min_notional=Decimal("5"),
    )


def _execution_item(account_id: int = 1, action: str = "open") -> CopierPlanExecutionItem:
    return CopierPlanExecutionItem(
        account_id=account_id,
        exchange="bingx",
        symbol="BTCUSDT",
        side="buy",
        action=action,
        execution_request=ExecutionRequest(
            execution_mode="simulated",
            account_id=account_id,
            exchange="bingx",
            symbol="BTCUSDT",
            side="buy",
            current_price=Decimal("50000"),
            risk_percent=Decimal("0.01"),
            leverage=Decimal("2"),
            run_id="run-test",
        ),
        reason="open_new",
    )


def _mock_execute_result():
    from app.exchanges.base import OrderExecutionResult
    from app.services.manual_dispatch_service import ManualDispatchAccountProcessingResult
    from app.sizing.position_sizing import PositionSizingResult

    zero = Decimal("0")
    return ManualDispatchAccountProcessingResult(
        sizing_result=PositionSizingResult(
            allocated_margin=zero,
            target_notional=zero,
            raw_quantity=zero,
            rounded_quantity=Decimal("0.01"),
            final_notional=Decimal("500"),
            is_valid=True,
            validation_errors=[],
        ),
        order_result=OrderExecutionResult(
            success=True,
            status="simulated_dispatched",
            exchange_order_id=None,
            executed_quantity=Decimal("0.01"),
            message="ok",
        ),
        log_payload={"simulated": True},
    )


def test_execute_copier_plan_items_calls_execution_engine_per_item():
    """Open/increase/reduce items each trigger execute_order_for_account."""
    from unittest.mock import patch

    items = [
        _execution_item(1, "open"),
        _execution_item(2, "increase"),
        _execution_item(3, "reduce"),
    ]
    get_account = lambda aid: _account(aid)
    log_service = MagicMock()
    execute_mock = MagicMock(return_value=_mock_execute_result())

    with patch("app.services.copier_plan_runner_service.execute_order_for_account", execute_mock):
        out = execute_copier_plan_items(
            execution_items=items,
            run_id="run-123",
            get_account=get_account,
            log_service=log_service,
        )

    assert execute_mock.call_count == 3
    assert isinstance(out, CopierPlanRunResult)
    assert out.run_id == "run-123"
    assert len(out.results) == 3
    assert log_service.create_log.call_count == 3
    assert out.results[0].account_id == 1 and out.results[0].dispatch_status == "simulated_dispatched"
    assert out.results[1].account_id == 2
    assert out.results[2].account_id == 3


def test_execute_copier_plan_items_empty_returns_empty_result_with_run_id():
    """Empty execution_items -> CopierPlanRunResult with same run_id, no execution calls."""
    from unittest.mock import patch

    log_service = MagicMock()
    execute_mock = MagicMock()

    with patch("app.services.copier_plan_runner_service.execute_order_for_account", execute_mock):
        out = execute_copier_plan_items(
            execution_items=[],
            run_id="run-empty",
            get_account=_account,
            log_service=log_service,
        )

    assert execute_mock.call_count == 0
    assert log_service.create_log.call_count == 0
    assert out.run_id == "run-empty"
    assert out.results == []


def test_execute_copier_plan_items_mixed_actions_result_length():
    """Mixed open/reduce items -> result length equals execution_items length (no hold)."""
    from unittest.mock import patch

    items = [_execution_item(1, "open"), _execution_item(2, "reduce")]
    get_account = lambda aid: _account(aid)
    log_service = MagicMock()

    with patch("app.services.copier_plan_runner_service.execute_order_for_account", MagicMock(return_value=_mock_execute_result())):
        out = execute_copier_plan_items(
            execution_items=items,
            run_id="run-mixed",
            get_account=get_account,
            log_service=log_service,
        )

    assert len(out.results) == 2
    assert out.results[0].account_id == 1
    assert out.results[1].account_id == 2
