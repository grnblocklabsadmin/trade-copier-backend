from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.execution import (
    DryRunExecutionItem,
    DryRunExecutionRequest,
    DryRunExecutionResponse,
    ManualDryRunExecutionRequest,
    ManualDryRunExecutionResponse,
)
from app.services.exchange_client_service import ExchangeClientService
from app.services.trade_execution_service import TradeExecutionService
from app.sizing.position_sizing import (
    PositionSizingInput,
    calculate_position_size,
)

router = APIRouter(prefix="/execution", tags=["execution"])


@router.post("/dry-run", response_model=DryRunExecutionResponse)
def dry_run_execution(
    payload: DryRunExecutionRequest,
    db: Session = Depends(get_db),
) -> DryRunExecutionResponse:
    exchange_client_service = ExchangeClientService(db)
    execution_service = TradeExecutionService(exchange_client_service)

    results: list[DryRunExecutionItem] = []

    for account_id in payload.account_ids:
        exchange_name, balance, market_spec, sizing_result = (
            execution_service.build_dry_run_for_account(
                account_id=account_id,
                symbol=payload.symbol,
                risk_percent=payload.risk_percent,
                leverage=payload.leverage,
                current_price=payload.current_price,
            )
        )

        results.append(
            DryRunExecutionItem(
                account_id=account_id,
                exchange=exchange_name,
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

    return DryRunExecutionResponse(
        symbol=payload.symbol,
        current_price=payload.current_price,
        results=results,
    )


@router.post("/dry-run/manual", response_model=ManualDryRunExecutionResponse)
def dry_run_execution_manual(
    payload: ManualDryRunExecutionRequest,
) -> ManualDryRunExecutionResponse:
    results: list[DryRunExecutionItem] = []

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
            DryRunExecutionItem(
                account_id=account.account_id,
                exchange=account.exchange,
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

    return ManualDryRunExecutionResponse(
        symbol=payload.symbol,
        current_price=payload.current_price,
        results=results,
    )