"""
Единый copier orchestration: master position -> plan -> execution items -> runner.
Объединяет planning, execution preparation и runner без изменения routes.
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import uuid4

from app.schemas.copier import CopierDispatchItem
from app.services.copier_plan_execution_service import (
    CopierPlanExecutionItem,
    build_execution_items_from_copier_plan,
)
from app.services.copier_plan_runner_service import execute_copier_plan_items
from app.services.copier_planning_service import (
    CopierPlanItem,
    build_copier_plan_for_accounts,
)
from app.services.execution_log_service import ExecutionLogService


@dataclass(slots=True)
class CopierOrchestrationResult:
    """Результат полного copier flow: plan, execution items и результаты исполнения."""
    run_id: str
    plan_items: list[CopierPlanItem]
    execution_items: list[CopierPlanExecutionItem]
    results: list[CopierDispatchItem]


def execute_copier_from_master_position(
    *,
    master_symbol: str,
    master_side: str,
    master_quantity,
    execution_mode: str,
    current_price,
    risk_percent,
    leverage,
    follower_accounts,
    follower_positions: dict[int, Decimal] | None = None,
    get_account,
    log_service: ExecutionLogService,
    run_id: str | None = None,
    event_type: str = "copier_dispatch_plan",
) -> CopierOrchestrationResult:
    """
    End-to-end: план по master position -> execution items -> исполнение через runner.
    run_id опционален: если не передан, генерируется через uuid4.
    """
    run_id = run_id or str(uuid4())

    plan_items = build_copier_plan_for_accounts(
        master_symbol=master_symbol,
        master_side=master_side,
        master_quantity=master_quantity,
        execution_mode=execution_mode,
        follower_accounts=follower_accounts,
        follower_positions=follower_positions,
    )

    execution_items = build_execution_items_from_copier_plan(
        plan_items=plan_items,
        current_price=current_price,
        risk_percent=risk_percent,
        leverage=leverage,
        execution_mode=execution_mode,
        run_id=run_id,
    )

    run_result = execute_copier_plan_items(
        execution_items=execution_items,
        run_id=run_id,
        get_account=get_account,
        log_service=log_service,
        event_type=event_type,
    )

    return CopierOrchestrationResult(
        run_id=run_id,
        plan_items=plan_items,
        execution_items=execution_items,
        results=run_result.results,
    )
