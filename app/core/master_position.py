"""
Typed contract for incoming master position event.
Used by future real copier pipeline: master position event -> planning -> execution.
"""
from dataclasses import dataclass
from decimal import Decimal


@dataclass(slots=True)
class MasterPositionEvent:
    """Входящее событие позиции master для copier flow."""
    source_exchange: str
    source_account_id: int | None
    symbol: str
    side: str
    quantity: Decimal
    entry_price: Decimal
    event_type: str
