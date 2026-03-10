from decimal import Decimal

from pydantic import BaseModel


class MarketOrderRequestSchema(BaseModel):
    account_id: int
    symbol: str
    side: str
    quantity: Decimal


class OrderExecutionResultSchema(BaseModel):
    account_id: int
    exchange: str
    success: bool
    exchange_order_id: str | None
    status: str | None
    executed_quantity: Decimal | None
    message: str | None