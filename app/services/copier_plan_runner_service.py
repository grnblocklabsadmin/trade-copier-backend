"""
Runner: executes CopierPlanExecutionItem via execution_engine.
Produces CopierPlanRunResult (run_id + list[CopierDispatchItem]).
"""
from dataclasses import dataclass
from decimal import Decimal
from typing import Callable, Protocol

from app.schemas.copier import CopierDispatchItem
from app.services.copier_plan_execution_service import CopierPlanExecutionItem
from app.services.execution_engine import execute_order_for_account
from app.services.execution_log_service import ExecutionLogService


class AccountForExecution(Protocol):
    """Минимальный account для execute_order_for_account (sizing/simulated path)."""
    account_id: int
    exchange: str
    available_balance: Decimal
    quantity_step: Decimal
    min_quantity: Decimal | None
    min_notional: Decimal | None


@dataclass(slots=True)
class CopierPlanRunResult:
    """Результат исполнения copier plan (тот же контракт, что и manual dispatch)."""
    run_id: str
    results: list[CopierDispatchItem]


def execute_copier_plan_items(
    *,
    execution_items: list[CopierPlanExecutionItem],
    run_id: str,
    get_account: Callable[[int], AccountForExecution],
    log_service: ExecutionLogService,
    event_type: str = "copier_dispatch_plan",
) -> CopierPlanRunResult:
    """
    Исполняет список CopierPlanExecutionItem через execution_engine.
    run_id передаётся явно (при пустом execution_items результат всё равно имеет run_id).
    get_account(account_id) должен возвращать объект с полями для sizing/simulated path.
    """
    results: list[CopierDispatchItem] = []

    for item in execution_items:
        account = get_account(item.account_id)
        result = execute_order_for_account(
            account=account,
            execution_request=item.execution_request,
        )

        log_service.create_log(
            run_id=run_id,
            event_type=event_type,
            symbol=item.symbol,
            side=item.side,
            account_id=item.account_id,
            exchange=item.exchange,
            status=result.order_result.status or "unknown",
            message=result.order_result.message,
            payload=result.log_payload,
        )

        results.append(
            CopierDispatchItem(
                account_id=item.account_id,
                exchange=item.exchange,
                symbol=item.symbol,
                side=item.side,
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

    return CopierPlanRunResult(run_id=run_id, results=results)
