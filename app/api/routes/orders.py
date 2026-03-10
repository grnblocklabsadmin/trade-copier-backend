from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.orders import (
    MarketOrderRequestSchema,
    OrderExecutionResultSchema,
)
from app.services.exchange_client_service import ExchangeClientService
from app.exchanges.base import MarketOrderRequest

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/market", response_model=OrderExecutionResultSchema)
def place_market_order(
    payload: MarketOrderRequestSchema,
    db: Session = Depends(get_db),
) -> OrderExecutionResultSchema:
    exchange_client_service = ExchangeClientService(db)
    adapter = exchange_client_service.get_adapter_for_account(payload.account_id)

    result = adapter.place_market_order(
        MarketOrderRequest(
            symbol=payload.symbol,
            side=payload.side,
            quantity=payload.quantity,
        )
    )

    return OrderExecutionResultSchema(
        account_id=payload.account_id,
        exchange=adapter.get_exchange_name(),
        success=result.success,
        exchange_order_id=result.exchange_order_id,
        status=result.status,
        executed_quantity=result.executed_quantity,
        message=result.message,
    )