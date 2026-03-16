"""
Typed contract for position synchronization (copier logic).
Used to decide open/hold/increase/reduce from master vs follower position.
"""
from dataclasses import dataclass
from decimal import Decimal


@dataclass(slots=True)
class PositionSyncInput:
    """Входные данные для решения о синхронизации позиции follower с master."""
    master_symbol: str
    master_side: str
    master_quantity: Decimal
    follower_account_id: int
    follower_exchange: str
    follower_current_position_quantity: Decimal
    execution_mode: str


@dataclass(slots=True)
class PositionSyncDecision:
    """Решение по синхронизации: действие, целевой объём, дельта, причина."""
    action: str
    target_quantity: Decimal
    delta_quantity: Decimal
    reason: str


def build_position_sync_decision(input_data: PositionSyncInput) -> PositionSyncDecision:
    """
    Строит решение по синхронизации позиции follower с master.
    open — позиции нет; hold — уже совпадает; increase/reduce — довести до master_quantity.
    """
    master = input_data.master_quantity
    current = input_data.follower_current_position_quantity

    if current == 0:
        return PositionSyncDecision(
            action="open",
            target_quantity=master,
            delta_quantity=master,
            reason="open_new",
        )
    if current == master:
        return PositionSyncDecision(
            action="hold",
            target_quantity=master,
            delta_quantity=Decimal("0"),
            reason="already_synced",
        )
    if current < master:
        return PositionSyncDecision(
            action="increase",
            target_quantity=master,
            delta_quantity=master - current,
            reason="increase_to_master",
        )
    # current > master
    return PositionSyncDecision(
        action="reduce",
        target_quantity=master,
        delta_quantity=current - master,
        reason="reduce_to_master",
    )
