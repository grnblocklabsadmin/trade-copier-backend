from typing import Any, Dict, Tuple

from app.core.order_validation import (
    OrderRequestValidationInput,
    OrderRequestValidationResult,
    validate_order_request,
)
from app.exchanges.base import OrderExecutionResult
from app.sizing.position_sizing import PositionSizingResult


def validate_order_request_for_execution(
    *,
    execution_mode: str,
    side: str,
    price,
    requested_quantity,
    quantity_step,
    min_quantity,
    min_notional,
    final_notional,
    run_id: str | None,
    account_id: int | None,
    exchange: str | None,
    symbol: str | None,
) -> Tuple[OrderRequestValidationResult, Dict[str, Any]]:
    """
    Небольшой сервисный слой для валидации ордер-запроса
    и формирования фрагмента payload для execution logs.
    """
    validation_input = OrderRequestValidationInput(
        execution_mode=execution_mode,
        side=side,
        price=price,
        requested_quantity=requested_quantity,
        quantity_step=quantity_step,
        min_quantity=min_quantity,
        min_notional=min_notional,
        final_notional=final_notional,
        run_id=run_id,
        account_id=account_id,
        exchange=exchange,
        symbol=symbol,
    )

    validation_result = validate_order_request(validation_input)

    payload_fragment: Dict[str, Any] = {
        "order_request_status": validation_result.status,
        "order_request_errors": validation_result.errors,
        "execution_mode": execution_mode,
        "order_request_account_id": account_id,
        "order_request_exchange": exchange,
        "order_request_symbol": symbol,
    }

    return validation_result, payload_fragment


def build_manual_simulated_order_result(
    sizing_result: PositionSizingResult,
    order_request_validation: OrderRequestValidationResult,
) -> OrderExecutionResult:
    """
    Решение по итоговому OrderExecutionResult для manual simulated dispatch,
    без сайд-эффектов и без логирования.
    """
    if not sizing_result.is_valid:
        return OrderExecutionResult(
            success=False,
            status="validation_failed",
            exchange_order_id=None,
            executed_quantity=None,
            message="Manual copier dispatch was skipped because sizing validation failed.",
        )

    if not order_request_validation.is_valid:
        return OrderExecutionResult(
            success=False,
            status="order_request_validation_failed",
            exchange_order_id=None,
            executed_quantity=None,
            message="Manual copier dispatch was skipped because order request validation failed.",
        )

    return OrderExecutionResult(
        success=True,
        status="simulated_dispatched",
        exchange_order_id=None,
        executed_quantity=sizing_result.rounded_quantity,
        message="Manual copier dispatch simulated successfully.",
    )


def build_manual_dispatch_log_payload(
    *,
    current_price,
    account,
    sizing_result: PositionSizingResult,
    order_result: OrderExecutionResult,
    order_request_payload: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Сборка payload для ExecutionLogService.create_log(...)
    в manual simulated dispatch.

    Сохраняет различие между sizing validation и order request validation.
    """
    return {
        "current_price": str(current_price),
        "available_balance": str(account.available_balance),
        "allocated_margin": str(sizing_result.allocated_margin),
        "target_notional": str(sizing_result.target_notional),
        "raw_quantity": str(sizing_result.raw_quantity),
        "rounded_quantity": str(sizing_result.rounded_quantity),
        "final_notional": str(sizing_result.final_notional),
        "quantity_step": str(account.quantity_step),
        "min_quantity": str(account.min_quantity) if account.min_quantity is not None else None,
        "min_notional": str(account.min_notional) if account.min_notional is not None else None,
        # sizing validation vs order request validation:
        # sizing_* отражают расчёт размера позиции,
        # order_request_* — итоговую проверку ордер-запроса перед исполнением.
        "is_valid": sizing_result.is_valid,
        "validation_errors": sizing_result.validation_errors,
        "dispatched": order_result.success,
        **order_request_payload,
    }



