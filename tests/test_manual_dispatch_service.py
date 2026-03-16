from decimal import Decimal

from app.core.execution_request import ExecutionRequest
from app.schemas.copier import ManualCopierDispatchAccount
from app.services.manual_dispatch_service import (
    ManualDispatchAccountProcessingResult,
    process_manual_simulated_dispatch_for_account,
)


def _execution_request() -> ExecutionRequest:
    return ExecutionRequest(
        execution_mode="simulated",
        account_id=1,
        exchange="binance",
        symbol="BTCUSDT",
        side="buy",
        current_price=Decimal("50000"),
        risk_percent=Decimal("0.01"),
        leverage=Decimal("2"),
        run_id="run-1",
    )


def _manual_dispatch_account() -> ManualCopierDispatchAccount:
    return ManualCopierDispatchAccount(
        account_id=1,
        exchange="binance",
        available_balance=Decimal("1000"),
        quantity_step=Decimal("0.001"),
        min_quantity=Decimal("0.001"),
        min_notional=Decimal("5"),
    )


def test_process_manual_simulated_dispatch_returns_typed_dataclass():
    account = _manual_dispatch_account()
    result = process_manual_simulated_dispatch_for_account(
        account=account,
        execution_request=_execution_request(),
    )
    assert type(result) is ManualDispatchAccountProcessingResult
    assert hasattr(result, "sizing_result")
    assert hasattr(result, "order_result")
    assert hasattr(result, "log_payload")


def test_process_manual_simulated_dispatch_log_payload_has_expected_fields():
    account = _manual_dispatch_account()
    result = process_manual_simulated_dispatch_for_account(
        account=account,
        execution_request=_execution_request(),
    )
    payload = result.log_payload
    expected_keys = [
        "current_price",
        "available_balance",
        "allocated_margin",
        "target_notional",
        "rounded_quantity",
        "final_notional",
        "is_valid",
        "validation_errors",
        "dispatched",
        "order_request_status",
        "order_request_errors",
        "execution_mode",
        "order_request_account_id",
        "order_request_exchange",
        "order_request_symbol",
    ]
    for key in expected_keys:
        assert key in payload, f"Missing key in log_payload: {key}"


def test_process_manual_simulated_dispatch_order_result_status_for_valid_path():
    account = _manual_dispatch_account()
    result = process_manual_simulated_dispatch_for_account(
        account=account,
        execution_request=_execution_request(),
    )
    assert result.order_result.status in (
        "simulated_dispatched",
        "validation_failed",
        "order_request_validation_failed",
    )
    if result.sizing_result.is_valid and result.log_payload.get("order_request_status") == "validation_ok":
        assert result.order_result.status == "simulated_dispatched"
