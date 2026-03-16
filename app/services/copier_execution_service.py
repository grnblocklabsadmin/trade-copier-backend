"""
Сервис оркестрации multi-account copier execution.
"""
from dataclasses import dataclass
from uuid import uuid4

from app.core.execution_request import ExecutionRequest
from app.core.trading import normalize_order_side
from app.schemas.copier import CopierDispatchItem
from app.services.execution_engine import execute_order_for_account
from app.services.execution_log_service import ExecutionLogService


@dataclass(slots=True)
class CopierExecutionResult:
    """Результат multi-account copier execution."""
    run_id: str
    results: list[CopierDispatchItem]


def execute_copier_for_accounts(
    *,
    execution_mode: str,
    symbol: str,
    side: str,
    current_price,
    risk_percent,
    leverage,
    accounts,
    log_service: ExecutionLogService,
    event_type: str = "copier_dispatch_manual",
) -> CopierExecutionResult:
    """
    Оркестрация copier execution по списку accounts.
    Для каждого account: ExecutionRequest → execute_order_for_account → log → CopierDispatchItem.
    """
    run_id = str(uuid4())
    normalized_side = normalize_order_side(side)
    results: list[CopierDispatchItem] = []

    for account in accounts:
        execution_request = ExecutionRequest(
            execution_mode=execution_mode,
            account_id=account.account_id,
            exchange=account.exchange,
            symbol=symbol,
            side=normalized_side,
            current_price=current_price,
            risk_percent=risk_percent,
            leverage=leverage,
            run_id=run_id,
        )
        result = execute_order_for_account(
            account=account,
            execution_request=execution_request,
        )

        log_service.create_log(
            run_id=run_id,
            event_type=event_type,
            symbol=symbol,
            side=normalized_side,
            account_id=account.account_id,
            exchange=account.exchange,
            status=result.order_result.status or "unknown",
            message=result.order_result.message,
            payload=result.log_payload,
        )

        results.append(
            CopierDispatchItem(
                account_id=account.account_id,
                exchange=account.exchange,
                symbol=symbol,
                side=normalized_side,
                rounded_quantity=result.sizing_result.rounded_quantity,
                final_notional=result.sizing_result.final_notional,
                is_valid=result.sizing_result.is_valid,
                validation_errors=result.sizing_result.validation_errors,
                dispatched=result.order_result.success,
                dispatch_status=result.order_result.status or "unknown",
                exchange_order_id=result.order_result.exchange_order_id,
                message=result.order_result.message,
            )
        )

    return CopierExecutionResult(run_id=run_id, results=results)
