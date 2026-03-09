from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.trade import (
    DryRunTradePreviewRequest,
    DryRunTradePreviewResponse,
    TradePreviewRequest,
    TradePreviewResponse,
)
from app.services.exchange_client_service import ExchangeClientService
from app.services.trade_preview_service import TradePreviewService
from app.sizing.position_sizing import (
    PositionSizingInput,
    calculate_position_size,
)

router = APIRouter(prefix="/trade", tags=["trade"])


@router.post("/preview", response_model=TradePreviewResponse)
def preview_trade(
    payload: TradePreviewRequest,
    db: Session = Depends(get_db),
) -> TradePreviewResponse:
    exchange_client_service = ExchangeClientService(db)
    trade_preview_service = TradePreviewService(exchange_client_service)

    exchange_name, balance, market_spec, sizing_result = trade_preview_service.build_preview(
        account_id=payload.account_id,
        symbol=payload.symbol,
        risk_percent=payload.risk_percent,
        leverage=payload.leverage,
        current_price=payload.current_price,
    )

    return TradePreviewResponse(
        account_id=payload.account_id,
        exchange=exchange_name,
        symbol=payload.symbol,
        current_price=payload.current_price,
        available_balance=balance.available_balance,
        allocated_margin=sizing_result.allocated_margin,
        target_notional=sizing_result.target_notional,
        raw_quantity=sizing_result.raw_quantity,
        rounded_quantity=sizing_result.rounded_quantity,
        final_notional=sizing_result.final_notional,
        quantity_step=market_spec.quantity_step,
        min_quantity=market_spec.min_quantity,
        min_notional=market_spec.min_notional,
        is_valid=sizing_result.is_valid,
        validation_errors=sizing_result.validation_errors,
    )


@router.post("/preview/dry-run", response_model=DryRunTradePreviewResponse)
def preview_trade_dry_run(
    payload: DryRunTradePreviewRequest,
) -> DryRunTradePreviewResponse:
    sizing_result = calculate_position_size(
        PositionSizingInput(
            available_balance=payload.available_balance,
            risk_percent=payload.risk_percent,
            leverage=payload.leverage,
            current_price=payload.current_price,
            quantity_step=payload.quantity_step,
            min_quantity=payload.min_quantity,
            min_notional=payload.min_notional,
        )
    )

    return DryRunTradePreviewResponse(
        symbol=payload.symbol,
        current_price=payload.current_price,
        available_balance=payload.available_balance,
        allocated_margin=sizing_result.allocated_margin,
        target_notional=sizing_result.target_notional,
        raw_quantity=sizing_result.raw_quantity,
        rounded_quantity=sizing_result.rounded_quantity,
        final_notional=sizing_result.final_notional,
        quantity_step=payload.quantity_step,
        min_quantity=payload.min_quantity,
        min_notional=payload.min_notional,
        is_valid=sizing_result.is_valid,
        validation_errors=sizing_result.validation_errors,
    )