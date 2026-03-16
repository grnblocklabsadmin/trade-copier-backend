"""
Stub adapter для проверки live execution pipeline без реальных бирж.
"""
from decimal import Decimal

from app.exchanges.adapter_models import AdapterOrderRequest, AdapterOrderResult
from app.exchanges.base_adapter import BaseExchangeAdapter


class StubLiveAdapter(BaseExchangeAdapter):
    async def place_order(self, order_request: AdapterOrderRequest) -> AdapterOrderResult:
        return AdapterOrderResult(
            success=True,
            status="live_stub_dispatched",
            exchange_order_id="stub-order-id",
            executed_quantity=order_request.quantity,
            message="Stub live order executed.",
        )

    async def cancel_order(self, order_id: str):
        raise NotImplementedError

    async def get_position(self, symbol: str):
        raise NotImplementedError
