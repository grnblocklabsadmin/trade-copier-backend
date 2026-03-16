"""
Planning layer for copier logic: master position -> per-account sync decisions.
Uses position_sync contract; does not perform execution.
"""
from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from app.core.position_sync import (
    PositionSyncInput,
    build_position_sync_decision,
)


class FollowerAccountRef(Protocol):
    """Minimal ref: account_id and exchange (e.g. ManualCopierDispatchAccount)."""
    account_id: int
    exchange: str


@dataclass(slots=True)
class CopierPlanItem:
    """Один элемент плана синхронизации для follower-аккаунта."""
    account_id: int
    exchange: str
    symbol: str
    side: str
    action: str
    target_quantity: Decimal
    delta_quantity: Decimal
    reason: str


def build_copier_plan_for_accounts(
    *,
    master_symbol: str,
    master_side: str,
    master_quantity: Decimal,
    execution_mode: str,
    follower_accounts: list[FollowerAccountRef],
    follower_positions: dict[int, Decimal] | None = None,
) -> list[CopierPlanItem]:
    """
    Строит план синхронизации: для каждого follower — action (open/hold/increase/reduce).
    follower_positions: account_id -> текущий объём позиции по символу/стороне; если нет — 0.
    """
    positions = follower_positions or {}
    zero = Decimal("0")
    plan: list[CopierPlanItem] = []

    for account in follower_accounts:
        current_qty = positions.get(account.account_id, zero)
        sync_input = PositionSyncInput(
            master_symbol=master_symbol,
            master_side=master_side,
            master_quantity=master_quantity,
            follower_account_id=account.account_id,
            follower_exchange=account.exchange,
            follower_current_position_quantity=current_qty,
            execution_mode=execution_mode,
        )
        decision = build_position_sync_decision(sync_input)
        plan.append(CopierPlanItem(
            account_id=account.account_id,
            exchange=account.exchange,
            symbol=master_symbol,
            side=master_side,
            action=decision.action,
            target_quantity=decision.target_quantity,
            delta_quantity=decision.delta_quantity,
            reason=decision.reason,
        ))
    return plan
