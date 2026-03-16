from dataclasses import dataclass
from decimal import Decimal


@dataclass(slots=True)
class ExecutionRequest:
    """
    Единый typed объект запроса на исполнение в execution pipeline.
    """
    execution_mode: str
    account_id: int | None
    exchange: str
    symbol: str
    side: str
    current_price: Decimal
    risk_percent: Decimal
    leverage: Decimal
    run_id: str
