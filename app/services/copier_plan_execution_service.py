"""
Bridge from copier plan (CopierPlanItem) to execution pipeline (ExecutionRequest).
Builds execution items for open/increase/reduce; hold items are excluded (no execution needed).
"""
from dataclasses import dataclass

from app.core.execution_request import ExecutionRequest
from app.services.copier_planning_service import CopierPlanItem


@dataclass(slots=True)
class CopierPlanExecutionItem:
    """Элемент плана с готовым ExecutionRequest для передачи в execution pipeline."""
    account_id: int
    exchange: str
    symbol: str
    side: str
    action: str
    execution_request: ExecutionRequest
    reason: str


def build_execution_items_from_copier_plan(
    *,
    plan_items: list[CopierPlanItem],
    current_price,
    risk_percent,
    leverage,
    execution_mode: str,
    run_id: str,
) -> list[CopierPlanExecutionItem]:
    """
    Строит список execution items из плана синхронизации.
    Элементы с action=="hold" не включаются в результат (исполнять нечего).
    Для open, increase, reduce создаётся ExecutionRequest с переданными параметрами.
    """
    result: list[CopierPlanExecutionItem] = []
    for item in plan_items:
        if item.action == "hold":
            continue
        execution_request = ExecutionRequest(
            execution_mode=execution_mode,
            account_id=item.account_id,
            exchange=item.exchange,
            symbol=item.symbol,
            side=item.side,
            current_price=current_price,
            risk_percent=risk_percent,
            leverage=leverage,
            run_id=run_id,
        )
        result.append(CopierPlanExecutionItem(
            account_id=item.account_id,
            exchange=item.exchange,
            symbol=item.symbol,
            side=item.side,
            action=item.action,
            execution_request=execution_request,
            reason=item.reason,
        ))
    return result
