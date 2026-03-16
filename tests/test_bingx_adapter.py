"""
Unit tests для BingX adapter: payload builder, result normalization, request params, place_order stub path, misconfiguration.
Фиксируют exchange-specific contract для _build_bingx_order_payload, _build_bingx_adapter_result_from_payload, build_bingx_signed_params, BingXAdapter.place_order stub, и защиту от неправильного wiring.
"""
import asyncio
from decimal import Decimal

import pytest

from app.exchanges.adapter_models import AdapterOrderRequest
from app.exchanges.bingx_adapter import (
    BingXAdapter,
    _build_bingx_adapter_result_from_payload,
    _build_bingx_order_payload,
)
from app.exchanges.bingx_signing import build_bingx_signed_params
from app.exchanges.credentials_provider import get_exchange_credentials
from app.exchanges.exceptions import ExchangeOrderPlacementError
from app.exchanges.http_client import ExchangeHTTPClient

BINGX_STUB_RESPONSE = {
    "success": True,
    "status": "live_stub_dispatched",
    "exchange_order_id": "bingx-stub-order-id",
    "message": "BingX stub order executed.",
}


def _bingx_stub_http_client():
    """HTTP client со stub response для тестов без сетевых вызовов."""
    return ExchangeHTTPClient(stub_response=BINGX_STUB_RESPONSE)


def test_build_bingx_order_payload_limit_order():
    """LIMIT order: price задан -> type=LIMIT, payload содержит price."""
    order_request = AdapterOrderRequest(
        exchange="bingx",
        symbol="BTC-USDT",
        side="buy",
        quantity=Decimal("0.001"),
        price=Decimal("50000"),
    )
    payload = _build_bingx_order_payload(order_request)

    assert payload["symbol"] == order_request.symbol
    assert payload["side"] == order_request.side
    assert payload["quantity"] == order_request.quantity
    assert payload["type"] == "LIMIT"
    assert payload["price"] == order_request.price


def test_build_bingx_order_payload_market_order():
    """MARKET order: price is None -> type=MARKET, ключ price отсутствует."""
    order_request = AdapterOrderRequest(
        exchange="bingx",
        symbol="ETH-USDT",
        side="sell",
        quantity=Decimal("0.01"),
        price=None,
    )
    payload = _build_bingx_order_payload(order_request)

    assert payload["symbol"] == order_request.symbol
    assert payload["side"] == order_request.side
    assert payload["quantity"] == order_request.quantity
    assert payload["type"] == "MARKET"
    assert "price" not in payload


def test_build_bingx_adapter_result_from_payload_success_response():
    """Success response: все поля маппятся в AdapterOrderResult; executed_quantity из str в Decimal."""
    order_request = AdapterOrderRequest(
        exchange="bingx",
        symbol="BTC-USDT",
        side="buy",
        quantity=Decimal("0.001"),
    )
    raw_response = {
        "success": True,
        "status": "filled",
        "exchange_order_id": "abc123",
        "executed_quantity": "0.001",
        "message": "order filled",
    }
    result = _build_bingx_adapter_result_from_payload(order_request, raw_response)

    assert result.success is True
    assert result.status == "filled"
    assert result.exchange_order_id == "abc123"
    assert result.executed_quantity == Decimal("0.001")
    assert result.message == "order filled"


def test_build_bingx_adapter_result_from_payload_executed_quantity_fallback():
    """Если executed_quantity отсутствует в raw_response, используется order_request.quantity."""
    order_request = AdapterOrderRequest(
        exchange="bingx",
        symbol="ETH-USDT",
        side="sell",
        quantity=Decimal("0.01"),
    )
    raw_response = {
        "success": True,
        "status": "accepted",
    }
    result = _build_bingx_adapter_result_from_payload(order_request, raw_response)

    assert result.executed_quantity == order_request.quantity


def test_build_bingx_adapter_result_from_payload_real_success():
    """Реальный success ответ BingX API (code=0, data.orderId) → live_dispatched, exchange_order_id."""
    order_request = AdapterOrderRequest(
        exchange="bingx",
        symbol="BTC-USDT",
        side="buy",
        quantity=Decimal("0.001"),
    )
    raw_response = {
        "code": 0,
        "msg": "success",
        "data": {"orderId": "123456"},
    }
    result = _build_bingx_adapter_result_from_payload(order_request, raw_response)

    assert result.status == "live_dispatched"
    assert result.exchange_order_id == "123456"
    assert result.success is True
    assert result.executed_quantity == order_request.quantity


def test_build_bingx_adapter_result_from_payload_real_error():
    """Реальный error ответ BingX API (code!=0) → ExchangeOrderPlacementError с code и msg."""
    order_request = AdapterOrderRequest(
        exchange="bingx",
        symbol="BTC-USDT",
        side="buy",
        quantity=Decimal("0.001"),
    )
    raw_response = {
        "code": 100001,
        "msg": "insufficient margin",
    }
    with pytest.raises(ExchangeOrderPlacementError) as exc_info:
        _build_bingx_adapter_result_from_payload(order_request, raw_response)
    assert "BingX order failed (code=100001): insufficient margin" in str(exc_info.value)


def test_build_bingx_signed_params():
    """Параметры копируются, добавляются timestamp и apiKey; исходный dict не изменяется."""
    input_params = {
        "symbol": "BTC-USDT",
        "side": "buy",
    }
    api_key = "test-key"

    result = build_bingx_signed_params(input_params, api_key)

    assert result["symbol"] == "BTC-USDT"
    assert result["side"] == "buy"
    assert result["apiKey"] == "test-key"
    assert "timestamp" in result
    assert type(result["timestamp"]) is int

    assert "timestamp" not in input_params
    assert "apiKey" not in input_params


def test_bingx_adapter_place_order_stub_path_limit():
    """Полный place_order stub path (LIMIT): AdapterOrderRequest -> BingXAdapter -> AdapterOrderResult."""
    order_request = AdapterOrderRequest(
        exchange="bingx",
        symbol="BTC-USDT",
        side="buy",
        quantity=Decimal("0.001"),
        price=Decimal("50000"),
    )
    adapter = BingXAdapter(
        http_client=_bingx_stub_http_client(),
        credentials=get_exchange_credentials("bingx"),
    )
    result = asyncio.run(adapter.place_order(order_request))

    assert result.success is True
    assert result.status == "live_stub_dispatched"
    assert result.exchange_order_id == "bingx-stub-order-id"
    assert result.executed_quantity == order_request.quantity
    assert result.message == "BingX stub order executed."


def test_bingx_adapter_place_order_stub_path_market():
    """Полный place_order stub path (MARKET, price=None): тот же контракт результата."""
    order_request = AdapterOrderRequest(
        exchange="bingx",
        symbol="ETH-USDT",
        side="sell",
        quantity=Decimal("0.01"),
        price=None,
    )
    adapter = BingXAdapter(
        http_client=_bingx_stub_http_client(),
        credentials=get_exchange_credentials("bingx"),
    )
    result = asyncio.run(adapter.place_order(order_request))

    assert result.success is True
    assert result.status == "live_stub_dispatched"
    assert result.exchange_order_id == "bingx-stub-order-id"
    assert result.executed_quantity == order_request.quantity
    assert result.message == "BingX stub order executed."


def test_bingx_adapter_place_order_without_http_client_raises():
    """place_order без http_client выбрасывает ExchangeOrderPlacementError."""
    adapter = BingXAdapter(
        http_client=None,
        credentials=get_exchange_credentials("bingx"),
    )
    order_request = AdapterOrderRequest(
        exchange="bingx",
        symbol="BTC-USDT",
        side="buy",
        quantity=Decimal("0.001"),
    )
    with pytest.raises(ExchangeOrderPlacementError, match="BingX HTTP client is not configured."):
        asyncio.run(adapter.place_order(order_request))


def test_bingx_adapter_place_order_without_credentials_raises():
    """place_order без credentials выбрасывает ExchangeOrderPlacementError."""
    adapter = BingXAdapter(
        http_client=_bingx_stub_http_client(),
        credentials=None,
    )
    order_request = AdapterOrderRequest(
        exchange="bingx",
        symbol="BTC-USDT",
        side="buy",
        quantity=Decimal("0.001"),
    )
    with pytest.raises(ExchangeOrderPlacementError, match="BingX credentials are not configured."):
        asyncio.run(adapter.place_order(order_request))
