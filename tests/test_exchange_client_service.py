"""
Unit tests для exchange_client_service: execute_adapter_order_with_retry, HTTP error mapping, rate-limit.
"""
import time
from decimal import Decimal
from unittest.mock import patch

import httpx
import pytest

from app.exchanges.adapter_models import AdapterOrderRequest, AdapterOrderResult
from app.exchanges.exceptions import ExchangeOrderPlacementError, ExchangeTransportError
from app.services import exchange_client_service
from app.services.exchange_client_service import (
    execute_adapter_order,
    execute_adapter_order_with_rate_limit,
    execute_adapter_order_with_retry,
)


def _sample_request() -> AdapterOrderRequest:
    return AdapterOrderRequest(
        exchange="bingx",
        symbol="BTC-USDT",
        side="buy",
        quantity=Decimal("0.001"),
    )


def _sample_result() -> AdapterOrderResult:
    return AdapterOrderResult(
        success=True,
        status="live_dispatched",
        exchange_order_id="123",
        executed_quantity=Decimal("0.001"),
        message="ok",
    )


def test_execute_adapter_order_with_retry_retryable_then_success():
    """Retryable ошибка на первой попытке, успех на второй — возвращается результат, 2 вызова."""
    adapter = object()
    request = _sample_request()
    result = _sample_result()
    with patch(
        "app.services.exchange_client_service.execute_adapter_order",
        side_effect=[ExchangeTransportError("network"), result],
    ) as mock_execute:
        got = execute_adapter_order_with_retry(adapter, request)
    assert got == result
    assert mock_execute.call_count == 2


def test_execute_adapter_order_with_retry_non_retryable_no_second_attempt():
    """Non-retryable ошибка — без второй попытки, исключение пробрасывается."""
    adapter = object()
    request = _sample_request()
    with patch(
        "app.services.exchange_client_service.execute_adapter_order",
        side_effect=ExchangeOrderPlacementError("order failed"),
    ) as mock_execute:
        with pytest.raises(ExchangeOrderPlacementError, match="order failed"):
            execute_adapter_order_with_retry(adapter, request)
    assert mock_execute.call_count == 1


def test_execute_adapter_order_timeout_maps_to_exchange_transport_error():
    """httpx.TimeoutException маппится в ExchangeTransportError с сообщением про timeout."""
    adapter = object()
    request = _sample_request()
    with patch(
        "app.services.exchange_client_service._run_async_adapter_place_order",
        side_effect=httpx.TimeoutException("timed out"),
    ):
        with pytest.raises(ExchangeTransportError, match="Exchange request timed out"):
            execute_adapter_order(adapter, request)


def test_execute_adapter_order_http_status_error_maps_to_exchange_transport_error():
    """httpx.HTTPStatusError маппится в ExchangeTransportError с status code в сообщении."""
    adapter = object()
    request = _sample_request()
    response = httpx.Response(500, request=httpx.Request("POST", "https://example.com"))
    with patch(
        "app.services.exchange_client_service._run_async_adapter_place_order",
        side_effect=httpx.HTTPStatusError("server error", request=response.request, response=response),
    ):
        with pytest.raises(ExchangeTransportError, match="Exchange HTTP error: 500"):
            execute_adapter_order(adapter, request)


def test_execute_adapter_order_with_rate_limit_applies_sleep():
    """При elapsed < MIN_REQUEST_INTERVAL вызываются time.sleep и execute_adapter_order_with_retry."""
    adapter = object()
    request = _sample_request()
    result = _sample_result()
    exchange_client_service._exchange_last_request_time["bingx"] = 0.0
    with (
        patch("app.services.exchange_client_service.time.monotonic", side_effect=[0.05, 0.05]),
        patch("app.services.exchange_client_service.time.sleep") as mock_sleep,
        patch("app.services.exchange_client_service.execute_adapter_order_with_retry", return_value=result) as mock_retry,
    ):
        got = execute_adapter_order_with_rate_limit(adapter, request)
    assert got == result
    mock_sleep.assert_called_once()
    call_arg = mock_sleep.call_args[0][0]
    assert abs(call_arg - 0.05) < 1e-6
    mock_retry.assert_called_once_with(adapter, request)


def test_execute_adapter_order_with_rate_limit_updates_timestamp_on_error():
    """При ошибке от execute_adapter_order_with_retry timestamp в finally обновляется, исключение пробрасывается."""
    adapter = object()
    request = _sample_request()
    exchange_client_service._exchange_last_request_time.pop("bingx", None)
    with patch(
        "app.services.exchange_client_service.execute_adapter_order_with_retry",
        side_effect=ExchangeTransportError("transport failed"),
    ):
        with pytest.raises(ExchangeTransportError, match="transport failed"):
            execute_adapter_order_with_rate_limit(adapter, request)
    assert "bingx" in exchange_client_service._exchange_last_request_time
    assert isinstance(exchange_client_service._exchange_last_request_time["bingx"], (int, float))
