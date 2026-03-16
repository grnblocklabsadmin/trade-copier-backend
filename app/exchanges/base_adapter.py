"""
Базовый async-интерфейс для exchange adapters.
Контракт для live_execution_service; не подключён к runtime до реализации live path.
"""
from abc import ABC, abstractmethod

from app.exchanges.adapter_models import AdapterOrderRequest, AdapterOrderResult


class BaseExchangeAdapter(ABC):
    """
    Минимальный контракт адаптера биржи для размещения и отмены ордеров, получения позиции.
    Реализации — в конкретных адаптерах (будущая интеграция с live_execution_service).
    """

    @abstractmethod
    async def place_order(self, order_request: AdapterOrderRequest) -> AdapterOrderResult:
        raise NotImplementedError

    @abstractmethod
    async def cancel_order(self, order_id: str):
        raise NotImplementedError

    @abstractmethod
    async def get_position(self, symbol: str):
        raise NotImplementedError
