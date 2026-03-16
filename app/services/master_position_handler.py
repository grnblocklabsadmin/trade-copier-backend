"""
Bridge: MasterPositionEvent -> copier orchestration.
Calls execute_copier_from_master_position with event fields; no websocket/stream/worker.
"""
from __future__ import annotations

from decimal import Decimal

from app.core.master_position import MasterPositionEvent
from app.services.copier_orchestration_service import (
    CopierOrchestrationResult,
    execute_copier_from_master_position,
)
from app.services.execution_log_service import ExecutionLogService


def handle_master_position_event(
    *,
    event: MasterPositionEvent,
    current_price,
    risk_percent,
    leverage,
    follower_accounts,
    follower_positions: dict[int, Decimal] | None = None,
    get_account,
    log_service: ExecutionLogService,
    run_id: str | None = None,
) -> CopierOrchestrationResult:
    """
    Запускает copier orchestration по входящему master position event.
    Пробрасывает event.symbol, event.side, event.quantity в execute_copier_from_master_position;
    execution_mode всегда "simulated".
    """
    return execute_copier_from_master_position(
        master_symbol=event.symbol,
        master_side=event.side,
        master_quantity=event.quantity,
        execution_mode="simulated",
        current_price=current_price,
        risk_percent=risk_percent,
        leverage=leverage,
        follower_accounts=follower_accounts,
        follower_positions=follower_positions,
        get_account=get_account,
        log_service=log_service,
        run_id=run_id,
    )
