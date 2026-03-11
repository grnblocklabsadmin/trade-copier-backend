from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.services.execution_log_service import ExecutionLogService

from app.api.deps import get_db
from app.exchanges.base import OrderExecutionResult
from app.schemas.copier import (
    CopierDispatchItem,
    CopierDispatchRequest,
    CopierDispatchResponse,
    CopierExecutionItem,
    CopierExecutionRequest,
    CopierExecutionResponse,
    ManualCopierDispatchRequest,
    ManualCopierDispatchResponse,
    ManualCopierExecutionRequest,
    ManualCopierExecutionResponse,
)
from app.services.exchange_client_service import ExchangeClientService
from app.services.trade_copier_execution_engine import TradeCopierExecutionEngine
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


@router.post("/dispatch", response_model=CopierDispatchResponse)
def dispatch_copier_plan(
    payload: CopierDispatchRequest,
    db: Session = Depends(get_db),
) -> CopierDispatchResponse:
    exchange_client_service = ExchangeClientService(db)
    execution_engine = TradeCopierExecutionEngine(exchange_client_service)

    results: list[CopierDispatchItem] = []

    for account_id in payload.account_ids:
        exchange_name, market_spec, sizing_result, order_result = (
            execution_engine.dispatch_for_account(
                account_id=account_id,
                symbol=payload.symbol,
                side=payload.side,
                risk_percent=payload.risk_percent,
                leverage=payload.leverage,
                current_price=payload.current_price,
            )
        )

        results.append(
            CopierDispatchItem(
                account_id=account_id,
                exchange=exchange_name,
                symbol=payload.symbol,
                side=payload.side,
                rounded_quantity=sizing_result.rounded_quantity,
                final_notional=sizing_result.final_notional,
                is_valid=sizing_result.is_valid,
                validation_errors=sizing_result.validation_errors,
                dispatched=order_result.success,
                dispatch_status=order_result.status or "unknown",
                exchange_order_id=order_result.exchange_order_id,
                message=order_result.message,
            )
        )

    return CopierDispatchResponse(
        symbol=payload.symbol,
        side=payload.side,
        current_price=payload.current_price,
        results=results,
    )


@router.post("/dispatch/manual", response_model=ManualCopierDispatchResponse)
def dispatch_manual_copier_plan(
    payload: ManualCopierDispatchRequest,
    db: Session = Depends(get_db),
) -> ManualCopierDispatchResponse:
    log_service = ExecutionLogService(db)
    results: list[CopierDispatchItem] = []

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

        if sizing_result.is_valid:
            order_result = OrderExecutionResult(
                success=True,
                status="simulated_dispatched",
                exchange_order_id=None,
                executed_quantity=sizing_result.rounded_quantity,
                message="Manual copier dispatch simulated successfully.",
            )
        else:
            order_result = OrderExecutionResult(
                success=False,
                status="validation_failed",
                exchange_order_id=None,
                executed_quantity=None,
                message="Manual copier dispatch was skipped because validation failed.",
            )

        log_service.create_log(
            event_type="copier_dispatch_manual",
            symbol=payload.symbol,
            side=payload.side,
            account_id=account.account_id,
            exchange=account.exchange,
            status=order_result.status or "unknown",
            message=order_result.message,
            payload={
                "current_price": str(payload.current_price),
                "available_balance": str(account.available_balance),
                "allocated_margin": str(sizing_result.allocated_margin),
                "target_notional": str(sizing_result.target_notional),
                "raw_quantity": str(sizing_result.raw_quantity),
                "rounded_quantity": str(sizing_result.rounded_quantity),
                "final_notional": str(sizing_result.final_notional),
                "quantity_step": str(account.quantity_step),
                "min_quantity": str(account.min_quantity) if account.min_quantity is not None else None,
                "min_notional": str(account.min_notional) if account.min_notional is not None else None,
                "is_valid": sizing_result.is_valid,
                "validation_errors": sizing_result.validation_errors,
                "dispatched": order_result.success,
            },
        )

        results.append(
            CopierDispatchItem(
                account_id=account.account_id,
                exchange=account.exchange,
                symbol=payload.symbol,
                side=payload.side,
                rounded_quantity=sizing_result.rounded_quantity,
                final_notional=sizing_result.final_notional,
                is_valid=sizing_result.is_valid,
                validation_errors=sizing_result.validation_errors,
                dispatched=order_result.success,
                dispatch_status=order_result.status or "unknown",
                exchange_order_id=order_result.exchange_order_id,
                message=order_result.message,
            )
        )

    return ManualCopierDispatchResponse(
        symbol=payload.symbol,
        side=payload.side,
        current_price=payload.current_price,
        results=results,
    )