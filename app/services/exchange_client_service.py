import asyncio
import time

import httpx
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.crypto import decrypt_value
from app.exchanges.adapter_models import AdapterOrderRequest, AdapterOrderResult
from app.exchanges.adapter_factory import create_exchange_adapter_instance
from app.exchanges.base import BaseExchangeAdapter, ExchangeCredentials
from app.exchanges.credentials import ExchangeAdapterCredentials
from app.exchanges.exceptions import (
    ExchangeAdapterNotImplementedError,
    ExchangeAuthenticationError,
    ExchangeError,
    ExchangeOrderPlacementError,
    ExchangeTransportError,
)
from app.exchanges.http_client import ExchangeHTTPClient
from app.exchanges.factory import ExchangeAdapterFactory
from app.models.exchange_account import ExchangeAccount

NON_RETRYABLE_EXCHANGE_ERRORS = (
    ExchangeOrderPlacementError,
    ExchangeAdapterNotImplementedError,
    ExchangeAuthenticationError,
)
RETRYABLE_EXCEPTIONS = (ExchangeTransportError, httpx.RequestError)
MAX_ATTEMPTS = 2
MIN_REQUEST_INTERVAL = 0.1  # секунд между запросами к одной бирже (burst protection)

_exchange_last_request_time: dict[str, float] = {}


def _run_async_adapter_place_order(adapter, order_request: AdapterOrderRequest) -> AdapterOrderResult:
    """
    Выполняет async adapter.place_order из sync-контекста.
    """
    return asyncio.run(adapter.place_order(order_request))


def execute_adapter_order(
    adapter,
    adapter_order_request: AdapterOrderRequest,
) -> AdapterOrderResult:
    """
    Вызывает adapter.place_order через async boundary; возвращает AdapterOrderResult.
    ExchangeError пробрасывается как есть. httpx-ошибки маппятся в ExchangeTransportError.
    """
    try:
        return _run_async_adapter_place_order(adapter, adapter_order_request)
    except ExchangeError:
        raise
    except httpx.TimeoutException:
        raise ExchangeTransportError("Exchange request timed out.")
    except httpx.HTTPStatusError as e:
        raise ExchangeTransportError(f"Exchange HTTP error: {e.response.status_code}")
    except httpx.RequestError:
        raise ExchangeTransportError("Exchange transport error.")


def execute_adapter_order_with_retry(
    adapter,
    adapter_order_request: AdapterOrderRequest,
) -> AdapterOrderResult:
    """
    До 2 попыток; retry только при transport/временных ошибках.
    Не retry при ExchangeOrderPlacementError, ExchangeAdapterNotImplementedError, ExchangeAuthenticationError.
    """
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return execute_adapter_order(adapter, adapter_order_request)
        except NON_RETRYABLE_EXCHANGE_ERRORS:
            raise
        except RETRYABLE_EXCEPTIONS:
            if attempt == MAX_ATTEMPTS:
                raise


def execute_adapter_order_with_rate_limit(
    adapter,
    adapter_order_request: AdapterOrderRequest,
) -> AdapterOrderResult:
    """
    Простой in-process rate limiter для burst protection: минимум 0.1 с между запросами к одной бирже.
    Применяется между попытками независимо от успеха/ошибки (время фиксируется в finally).
    """
    exchange = adapter_order_request.exchange
    now = time.monotonic()
    if exchange in _exchange_last_request_time:
        elapsed = now - _exchange_last_request_time[exchange]
        if elapsed < MIN_REQUEST_INTERVAL:
            time.sleep(MIN_REQUEST_INTERVAL - elapsed)
    try:
        return execute_adapter_order_with_retry(adapter, adapter_order_request)
    finally:
        _exchange_last_request_time[exchange] = time.monotonic()


def create_exchange_adapter(
    exchange: str,
    http_client: ExchangeHTTPClient | None = None,
    credentials: ExchangeAdapterCredentials | None = None,
):
    """
    Создаёт экземпляр адаптера биржи по названию через adapter factory.
    Неизвестная биржа → ValueError из registry.
    Опционально передаёт http_client и credentials в фабрику (для BingX и др.).
    """
    return create_exchange_adapter_instance(
        exchange=exchange,
        http_client=http_client,
        credentials=credentials,
    )


class ExchangeClientService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_adapter_for_account(self, account_id: int) -> BaseExchangeAdapter:
        exchange_account = self.db.execute(
            select(ExchangeAccount).where(ExchangeAccount.id == account_id)
        ).scalar_one_or_none()

        if exchange_account is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exchange account not found.",
            )

        credentials = ExchangeCredentials(
            api_key=decrypt_value(exchange_account.api_key),
            api_secret=decrypt_value(exchange_account.api_secret),
        )

        return ExchangeAdapterFactory.create_adapter(
            exchange=exchange_account.exchange,
            credentials=credentials,
        )