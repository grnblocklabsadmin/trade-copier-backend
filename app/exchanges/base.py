from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal


@dataclass(slots=True)
class ExchangeCredentials:
    api_key: str
    api_secret: str


@dataclass(slots=True)
class BalanceSnapshot:
    total_balance: Decimal
    available_balance: Decimal
    margin_balance: Decimal | None = None


@dataclass(slots=True)
class PositionSnapshot:
    symbol: str
    side: str
    quantity: Decimal
    entry_price: Decimal
    leverage: Decimal | None = None
    unrealized_pnl: Decimal | None = None


@dataclass(slots=True)
class MarketSpecSnapshot:
    symbol: str
    price_tick_size: Decimal | None
    quantity_step: Decimal | None
    min_quantity: Decimal | None
    min_notional: Decimal | None


@dataclass(slots=True)
class MarketOrderRequest:
    symbol: str
    side: str
    quantity: Decimal


@dataclass(slots=True)
class OrderExecutionResult:
    success: bool
    exchange_order_id: str | None = None
    status: str | None = None
    executed_quantity: Decimal | None = None
    message: str | None = None


class BaseExchangeAdapter(ABC):
    def __init__(self, credentials: ExchangeCredentials) -> None:
        self.credentials = credentials

    @abstractmethod
    def get_exchange_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def test_connection(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def fetch_balance(self) -> BalanceSnapshot:
        raise NotImplementedError

    @abstractmethod
    def fetch_positions(self) -> list[PositionSnapshot]:
        raise NotImplementedError

    @abstractmethod
    def fetch_market_spec(self, symbol: str) -> MarketSpecSnapshot:
        raise NotImplementedError

    @abstractmethod
    def place_market_order(self, order: MarketOrderRequest) -> OrderExecutionResult:
        raise NotImplementedError