"""
Тесты stub live execution path в live_execution_service.
"""
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.core.execution_request import ExecutionRequest
from app.exchanges.exceptions import ExchangeAdapterNotImplementedError
from app.exchanges.http_client import ExchangeHTTPClient
from app.services.live_execution_service import execute_live_order_for_account
from app.services.manual_dispatch_service import ManualDispatchAccountProcessingResult

BINGX_STUB_HTTP_CLIENT = ExchangeHTTPClient(
    stub_response={
        "success": True,
        "status": "live_stub_dispatched",
        "exchange_order_id": "bingx-stub-order-id",
        "message": "BingX stub order executed.",
    }
)


def _stub_execution_request() -> ExecutionRequest:
    return ExecutionRequest(
        execution_mode="live",
        account_id=1,
        exchange="stub",
        symbol="BTCUSDT",
        side="buy",
        current_price=Decimal("50000"),
        risk_percent=Decimal("0.01"),
        leverage=Decimal("2"),
        run_id="run-1",
    )


def test_execute_live_order_for_account_stub_returns_typed_result():
    execution_request = _stub_execution_request()
    result = execute_live_order_for_account(execution_request=execution_request)
    assert isinstance(result, ManualDispatchAccountProcessingResult)
    assert result.order_result.status == "live_stub_dispatched"
    assert result.log_payload.get("live_stub") is True


def test_execute_live_order_for_account_bingx_returns_stub_result():
    """Live path для exchange=bingx; HTTP client подменён на stub, без сетевых вызовов."""
    execution_request = ExecutionRequest(
        execution_mode="live",
        account_id=1,
        exchange="bingx",
        symbol="BTC-USDT",
        side="buy",
        current_price=Decimal("50000"),
        risk_percent=Decimal("0.01"),
        leverage=Decimal("2"),
        run_id="run-bingx-1",
    )
    with (
        patch("app.services.live_execution_service.get_settings", return_value=SimpleNamespace(enable_real_trading=True)),
        patch("app.services.live_execution_service.get_exchange_http_client", return_value=BINGX_STUB_HTTP_CLIENT),
    ):
        result = execute_live_order_for_account(execution_request=execution_request)

    assert isinstance(result, ManualDispatchAccountProcessingResult)
    assert result.order_result.success is True
    assert result.order_result.status == "live_stub_dispatched"
    assert result.order_result.exchange_order_id == "bingx-stub-order-id"
    assert result.log_payload.get("live_stub") is True
    assert result.log_payload.get("exchange") == "bingx"


def test_execute_live_order_for_account_non_stub_raises_adapter_not_implemented():
    execution_request = ExecutionRequest(
        execution_mode="live",
        account_id=1,
        exchange="binance",
        symbol="BTCUSDT",
        side="buy",
        current_price=Decimal("50000"),
        risk_percent=Decimal("0.01"),
        leverage=Decimal("2"),
        run_id="run-1",
    )
    with pytest.raises(
        ExchangeAdapterNotImplementedError,
        match="Exchange adapter for .binance. is not implemented yet",
    ):
        execute_live_order_for_account(execution_request=execution_request)
