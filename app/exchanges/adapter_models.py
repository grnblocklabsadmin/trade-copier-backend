from dataclasses import dataclass
from decimal import Decimal


@dataclass(slots=True)
class AdapterOrderRequest:
    """
    Типизированный запрос на размещение ордера для exchange adapter layer.
    """
    exchange: str
    symbol: str
    side: str
    quantity: Decimal
    price: Decimal | None = None
    execution_mode: str = ""
    account_id: int | None = None
    run_id: str = ""


@dataclass(slots=True)
class AdapterOrderResult:
    """
    Типизированный результат размещения ордера от exchange adapter layer.
    """
    success: bool
    status: str
    exchange_order_id: str | None
    executed_quantity: Decimal | None
    message: str | None = None
