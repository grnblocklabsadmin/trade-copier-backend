from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.core.execution_modes import ExecutionMode
from app.core.execution_request import ExecutionRequest
from app.exchanges.exceptions import ExchangeAdapterNotImplementedError
from app.exchanges.http_client import ExchangeHTTPClient
from app.schemas.copier import ManualCopierDispatchAccount
from app.services.execution_engine import (
    _executed_idempotency_keys,
    execute_order_for_account,
)
from app.services.manual_dispatch_service import ManualDispatchAccountProcessingResult

BINGX_STUB_HTTP_CLIENT = ExchangeHTTPClient(
    stub_response={
        "success": True,
        "status": "live_stub_dispatched",
        "exchange_order_id": "bingx-stub-order-id",
        "message": "BingX stub order executed.",
    }
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


def _execution_request(execution_mode: str) -> ExecutionRequest:
    return ExecutionRequest(
        execution_mode=execution_mode,
        account_id=1,
        exchange="binance",
        symbol="BTCUSDT",
        side="buy",
        current_price=Decimal("50000"),
        risk_percent=Decimal("0.01"),
        leverage=Decimal("2"),
        run_id="run-1",
    )


def test_execute_order_for_account_simulated_returns_result():
    account = _manual_dispatch_account()
    execution_request = _execution_request(ExecutionMode.SIMULATED.value)
    result = execute_order_for_account(
        account=account,
        execution_request=execution_request,
    )
    assert isinstance(result, ManualDispatchAccountProcessingResult)
    assert result.sizing_result is not None
    assert result.order_result is not None
    assert result.log_payload is not None
    assert result.order_result.status in (
        "simulated_dispatched",
        "validation_failed",
        "order_request_validation_failed",
    )


def test_execute_order_for_account_live_stub_returns_result():
    account = ManualCopierDispatchAccount(
        account_id=1,
        exchange="stub",
        available_balance=Decimal("1000"),
        quantity_step=Decimal("0.001"),
        min_quantity=Decimal("0.001"),
        min_notional=Decimal("5"),
    )
    execution_request = ExecutionRequest(
        execution_mode=ExecutionMode.LIVE.value,
        account_id=1,
        exchange="stub",
        symbol="BTCUSDT",
        side="buy",
        current_price=Decimal("50000"),
        risk_percent=Decimal("0.01"),
        leverage=Decimal("2"),
        run_id="run-1",
    )
    result = execute_order_for_account(
        account=account,
        execution_request=execution_request,
    )
    assert isinstance(result, ManualDispatchAccountProcessingResult)
    assert result.order_result.success is True
    assert result.order_result.status == "live_stub_dispatched"
    assert result.order_result.exchange_order_id == "stub-order-id"


def test_execute_order_for_account_live_bingx_returns_result():
    """Live path для exchange=bingx; HTTP client подменён на stub, без сетевых вызовов."""
    account = ManualCopierDispatchAccount(
        account_id=1,
        exchange="bingx",
        available_balance=Decimal("1000"),
        quantity_step=Decimal("0.001"),
        min_quantity=Decimal("0.001"),
        min_notional=Decimal("5"),
    )
    execution_request = ExecutionRequest(
        execution_mode=ExecutionMode.LIVE.value,
        account_id=1,
        exchange="bingx",
        symbol="BTC-USDT",
        side="buy",
        current_price=Decimal("50000"),
        risk_percent=Decimal("0.01"),
        leverage=Decimal("2"),
        run_id="run-1",
    )
    with (
        patch("app.services.live_execution_service.get_settings", return_value=SimpleNamespace(enable_real_trading=True)),
        patch("app.services.live_execution_service.get_exchange_http_client", return_value=BINGX_STUB_HTTP_CLIENT),
    ):
        result = execute_order_for_account(
            account=account,
            execution_request=execution_request,
        )
    assert isinstance(result, ManualDispatchAccountProcessingResult)
    assert result.order_result.success is True
    assert result.order_result.status == "live_stub_dispatched"
    assert result.order_result.exchange_order_id == "bingx-stub-order-id"


def test_execute_order_for_account_live_raises_adapter_not_implemented():
    account = _manual_dispatch_account()
    execution_request = _execution_request(ExecutionMode.LIVE.value)
    with pytest.raises(
        ExchangeAdapterNotImplementedError,
        match="Exchange adapter for .binance. is not implemented yet",
    ):
        execute_order_for_account(
            account=account,
            execution_request=execution_request,
        )


def test_execute_order_for_account_unsupported_mode_raises_value_error():
    account = _manual_dispatch_account()
    execution_request = _execution_request("unknown")
    with pytest.raises(ValueError, match="Unsupported execution_mode"):
        execute_order_for_account(
            account=account,
            execution_request=execution_request,
        )


def test_idempotency_guard_second_identical_request_skips_live_execution():
    """Two identical execution_requests in a row: second returns idempotent_skip without calling live_execution_service."""
    from decimal import Decimal
    from unittest.mock import MagicMock

    from app.exchanges.base import OrderExecutionResult
    from app.sizing.position_sizing import PositionSizingResult

    account = ManualCopierDispatchAccount(
        account_id=1,
        exchange="stub",
        available_balance=Decimal("1000"),
        quantity_step=Decimal("0.001"),
        min_quantity=Decimal("0.001"),
        min_notional=Decimal("5"),
    )
    execution_request = ExecutionRequest(
        execution_mode=ExecutionMode.LIVE.value,
        account_id=1,
        exchange="stub",
        symbol="BTCUSDT",
        side="buy",
        current_price=Decimal("50000"),
        risk_percent=Decimal("0.01"),
        leverage=Decimal("2"),
        run_id="run-idem",
    )
    zero = Decimal("0")
    live_return = ManualDispatchAccountProcessingResult(
        sizing_result=PositionSizingResult(
            allocated_margin=zero,
            target_notional=zero,
            raw_quantity=zero,
            rounded_quantity=zero,
            final_notional=zero,
            is_valid=True,
            validation_errors=[],
        ),
        order_result=OrderExecutionResult(
            success=True,
            status="live_stub_dispatched",
            exchange_order_id="stub-1",
            executed_quantity=zero,
            message="ok",
        ),
        log_payload={},
    )
    _executed_idempotency_keys.clear()
    live_mock = MagicMock(return_value=live_return)
    with patch("app.services.execution_engine.execute_live_order_for_account", live_mock):
        first = execute_order_for_account(account=account, execution_request=execution_request)
        second = execute_order_for_account(account=account, execution_request=execution_request)

    assert live_mock.call_count == 1
    assert first.order_result.status == "live_stub_dispatched"
    assert second.order_result.status == "idempotent_skip"
    assert second.log_payload.get("idempotent_skip") is True


def test_idempotency_guard_after_exception_retry_calls_live_execution_again():
    """First call raises; second identical request must not get idempotent_skip, live_execution_service called again."""
    from decimal import Decimal
    from unittest.mock import MagicMock

    from app.exchanges.base import OrderExecutionResult
    from app.sizing.position_sizing import PositionSizingResult

    account = ManualCopierDispatchAccount(
        account_id=1,
        exchange="stub",
        available_balance=Decimal("1000"),
        quantity_step=Decimal("0.001"),
        min_quantity=Decimal("0.001"),
        min_notional=Decimal("5"),
    )
    execution_request = ExecutionRequest(
        execution_mode=ExecutionMode.LIVE.value,
        account_id=1,
        exchange="stub",
        symbol="BTCUSDT",
        side="buy",
        current_price=Decimal("50000"),
        risk_percent=Decimal("0.01"),
        leverage=Decimal("2"),
        run_id="run-retry",
    )
    zero = Decimal("0")
    success_return = ManualDispatchAccountProcessingResult(
        sizing_result=PositionSizingResult(
            allocated_margin=zero,
            target_notional=zero,
            raw_quantity=zero,
            rounded_quantity=zero,
            final_notional=zero,
            is_valid=True,
            validation_errors=[],
        ),
        order_result=OrderExecutionResult(
            success=True,
            status="live_stub_dispatched",
            exchange_order_id="stub-1",
            executed_quantity=zero,
            message="ok",
        ),
        log_payload={},
    )
    _executed_idempotency_keys.clear()
    live_mock = MagicMock(side_effect=[RuntimeError("exchange error"), success_return])
    with patch("app.services.execution_engine.execute_live_order_for_account", live_mock):
        with pytest.raises(RuntimeError, match="exchange error"):
            execute_order_for_account(account=account, execution_request=execution_request)
        second = execute_order_for_account(account=account, execution_request=execution_request)

    assert live_mock.call_count == 2
    assert second.order_result.status == "live_stub_dispatched"
    assert second.order_result.status != "idempotent_skip"
