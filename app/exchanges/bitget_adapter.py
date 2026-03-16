"""
Skeleton адаптера BitGet для live execution. Не подключён к runtime.
"""
from app.exchanges.adapter_models import AdapterOrderRequest, AdapterOrderResult
from app.exchanges.base_adapter import BaseExchangeAdapter


class BitgetAdapter(BaseExchangeAdapter):
    async def place_order(self, order_request: AdapterOrderRequest) -> AdapterOrderResult:
        raise NotImplementedError

    async def cancel_order(self, order_id: str):
        raise NotImplementedError

    async def get_position(self, symbol: str):
        raise NotImplementedError
