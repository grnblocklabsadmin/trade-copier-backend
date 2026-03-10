from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.copier import (
    CopierExecutionItem,
    CopierExecutionRequest,
    CopierExecutionResponse,
    ManualCopierExecutionRequest,
    ManualCopierExecutionResponse,
)
from app.services.exchange_client_service import ExchangeClientService
from app.services.trade_copier_service import TradeCopierService
from app.sizing.position_sizing import (
    PositionSizingInput,
    calculate_position_size,
)

router = APIRouter(prefix="/copier", tags=["copier"])


@router.post("/execute", response_model=CopierExecutionResponse)
def execute_copier_plan(
    payload: CopierExecutionRequest,
    db: Session = Depends(get_db),
) -> CopierExecutionResponse:
    exchange_client_service = ExchangeClientService(db)
    copier_service = TradeCopierService(exchange_client_service)

    results: list[CopierExecutionItem] = []

    for account_id in payload.account_ids:
        exchange_name, balance, market_spec, sizing_result = (
            copier_service.build_execution_plan_for_account(
                account_id=account_id,
                symbol=payload.symbol,
                risk_percent=payload.risk_percent,
                leverage=payload.leverage,
                current_price=payload.current_price,
            )
        )

        results.append(
            CopierExecutionItem(
                account_id=account_id,
                exchange=exchange_name,
                symbol=payload.symbol,
                side=payload.side,
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
        )

    return CopierExecutionResponse(
        symbol=payload.symbol,
        side=payload.side,
        current_price=payload.current_price,
        results=results,
    )


@router.post("/execute/manual", response_model=ManualCopierExecutionResponse)
def execute_manual_copier_plan(
    payload: ManualCopierExecutionRequest,
) -> ManualCopierExecutionResponse:
    results: list[CopierExecutionItem] = []

    for account in payload.accounts:
        sizing_result = calculate_position_size(
            PositionSizingInput(
                available_balance=account.available_balance,
                risk_percent=payload.risk_percent,
                leverage=payload.leverage,
                current_price=payload.current_price,
                quantity_step=account.quantity_step,
                min_quantity=account.min_quantity,
                min_notional=account.min_notional,
            )
        )

        results.append(
            CopierExecutionItem(
                account_id=account.account_id,
                exchange=account.exchange,
                symbol=payload.symbol,
                side=payload.side,
                available_balance=account.available_balance,
                allocated_margin=sizing_result.allocated_margin,
                target_notional=sizing_result.target_notional,
                raw_quantity=sizing_result.raw_quantity,
                rounded_quantity=sizing_result.rounded_quantity,
                final_notional=sizing_result.final_notional,
                quantity_step=account.quantity_step,
                min_quantity=account.min_quantity,
                min_notional=account.min_notional,
                is_valid=sizing_result.is_valid,
                validation_errors=sizing_result.validation_errors,
            )
        )

    return ManualCopierExecutionResponse(
        symbol=payload.symbol,
        side=payload.side,
        current_price=payload.current_price,
        results=results,
    )