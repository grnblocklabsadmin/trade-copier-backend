from dataclasses import dataclass
from typing import Any, Dict

from app.core.execution_request import ExecutionRequest
from app.exchanges.base import OrderExecutionResult
from app.services.order_request_validation_service import (
    build_manual_dispatch_log_payload,
    build_manual_simulated_order_result,
    validate_order_request_for_execution,
)
from app.sizing.position_sizing import (
    PositionSizingInput,
    PositionSizingResult,
    calculate_position_size,
)


@dataclass(slots=True)
class ManualDispatchAccountProcessingResult:
    sizing_result: PositionSizingResult
    order_result: OrderExecutionResult
    log_payload: Dict[str, Any]


def process_manual_simulated_dispatch_for_account(
    *,
    account,
    execution_request: ExecutionRequest,
) -> ManualDispatchAccountProcessingResult:
    """
    Оркестрация manual simulated dispatch для одного аккаунта:
    сайзинг, валидация ордер-запроса, итоговый OrderExecutionResult и log payload.
    """
    req = execution_request
    sizing_result = calculate_position_size(
        PositionSizingInput(
            available_balance=account.available_balance,
            risk_percent=req.risk_percent,
            leverage=req.leverage,
            current_price=req.current_price,
            quantity_step=account.quantity_step,
            min_quantity=account.min_quantity,
            min_notional=account.min_notional,
        )
    )

    order_request_validation, order_request_payload = validate_order_request_for_execution(
        execution_mode=req.execution_mode,
        side=req.side,
        price=req.current_price,
        requested_quantity=sizing_result.rounded_quantity,
        quantity_step=account.quantity_step,
        min_quantity=account.min_quantity,
        min_notional=account.min_notional,
        final_notional=sizing_result.final_notional,
        run_id=req.run_id,
        account_id=account.account_id,
        exchange=account.exchange,
        symbol=req.symbol,
    )

    order_result = build_manual_simulated_order_result(
        sizing_result=sizing_result,
        order_request_validation=order_request_validation,
    )

    log_payload = build_manual_dispatch_log_payload(
        current_price=req.current_price,
        account=account,
        sizing_result=sizing_result,
        order_result=order_result,
        order_request_payload=order_request_payload,
    )

    return ManualDispatchAccountProcessingResult(
        sizing_result=sizing_result,
        order_result=order_result,
        log_payload=log_payload,
    )
