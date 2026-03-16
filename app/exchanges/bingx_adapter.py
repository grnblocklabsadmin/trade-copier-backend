"""
BingX adapter для live execution.
Exchange-specific payload preparation и response/error normalization перед реальной API интеграцией.
"""
from decimal import Decimal

from app.exchanges.adapter_models import AdapterOrderRequest, AdapterOrderResult
from app.exchanges.base_adapter import BaseExchangeAdapter
from app.exchanges.bingx_endpoints import (
    BINGX_BASE_URL,
    BINGX_FUTURES_ORDER_ENDPOINT,
)
from app.exchanges.bingx_signing import (
    build_bingx_signed_params,
    sign_bingx_request,
)
from app.exchanges.credentials import ExchangeAdapterCredentials
from app.exchanges.exceptions import ExchangeOrderPlacementError
from app.exchanges.http_client import ExchangeHTTPClient


def _build_bingx_order_payload(order_request: AdapterOrderRequest) -> dict:
    """
    Собирает минимальный payload dict для будущего BingX order placement.
    Не выполняет запрос; только подготовка полей (symbol, side, quantity, price, type).
    """
    order_type = "MARKET" if order_request.price is None else "LIMIT"
    payload: dict = {
        "symbol": order_request.symbol,
        "side": order_request.side,
        "quantity": order_request.quantity,
        "type": order_type,
    }
    if order_request.price is not None:
        payload["price"] = order_request.price
    return payload


def _build_bingx_adapter_result_from_payload(
    order_request: AdapterOrderRequest,
    raw_response: dict,
) -> AdapterOrderResult:
    """
    Маппинг raw response dict → AdapterOrderResult для BingX.
    Поддерживает: 1) реальный формат API (code, msg, data.orderId); 2) stub формат (success, status, exchange_order_id, message).
    """
    if "code" in raw_response:
        if raw_response.get("code") == 0:
            data = raw_response.get("data") or {}
            order_id = data.get("orderId")
            return AdapterOrderResult(
                success=True,
                status="live_dispatched",
                exchange_order_id=order_id,
                executed_quantity=order_request.quantity,
                message=raw_response.get("msg", "success"),
            )
        code = raw_response.get("code")
        msg = raw_response.get("msg", "unknown error")
        raise ExchangeOrderPlacementError(
            f"BingX order failed (code={code}): {msg}"
        )
    success = bool(raw_response.get("success", False))
    status = str(raw_response.get("status", "unknown"))
    exchange_order_id = raw_response.get("exchange_order_id")
    executed_quantity = raw_response.get("executed_quantity", order_request.quantity)
    if executed_quantity is not None and not isinstance(executed_quantity, Decimal):
        executed_quantity = Decimal(str(executed_quantity))
    message = raw_response.get("message")
    return AdapterOrderResult(
        success=success,
        status=status,
        exchange_order_id=exchange_order_id,
        executed_quantity=executed_quantity,
        message=message,
    )


def _raise_bingx_error(message: str) -> None:
    """Exchange-specific error normalization: выбрасывает ExchangeOrderPlacementError."""
    raise ExchangeOrderPlacementError(message)


class BingXAdapter(BaseExchangeAdapter):
    def __init__(
        self,
        http_client: ExchangeHTTPClient | None = None,
        credentials: ExchangeAdapterCredentials | None = None,
    ) -> None:
        self._http_client = http_client
        self._credentials = credentials

    async def place_order(self, order_request: AdapterOrderRequest) -> AdapterOrderResult:
        if self._http_client is None:
            _raise_bingx_error("BingX HTTP client is not configured.")
        if self._credentials is None:
            _raise_bingx_error("BingX credentials are not configured.")
        payload = _build_bingx_order_payload(order_request)
        url = BINGX_BASE_URL + BINGX_FUTURES_ORDER_ENDPOINT
        params = build_bingx_signed_params(payload)
        api_secret = self._credentials.api_secret or ""
        signature = sign_bingx_request(api_secret, params)
        signed_payload = dict(params)
        signed_payload["signature"] = signature
        raw_response = await self._http_client.post(
            url=url,
            payload=signed_payload,
            headers={"Content-Type": "application/json"},
        )
        return _build_bingx_adapter_result_from_payload(order_request, raw_response)

    async def cancel_order(self, order_id: str):
        raise NotImplementedError

    async def get_position(self, symbol: str):
        raise NotImplementedError
