from datetime import datetime

from pydantic import BaseModel

from decimal import Decimal


class ExchangeAccountCreate(BaseModel):
    user_id: int
    exchange: str
    account_name: str
    api_key: str
    api_secret: str


class ExchangeAccountRead(BaseModel):
    id: int
    user_id: int
    exchange: str
    account_name: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ExchangeConnectionTestResult(BaseModel):
    account_id: int
    exchange: str
    success: bool


class ExchangeBalanceRead(BaseModel):
    account_id: int
    exchange: str
    total_balance: Decimal
    available_balance: Decimal
    margin_balance: Decimal | None


class ExchangePositionRead(BaseModel):
    symbol: str
    side: str
    quantity: Decimal
    entry_price: Decimal
    leverage: Decimal | None
    unrealized_pnl: Decimal | None


class ExchangeMarketSpecRead(BaseModel):
    account_id: int
    exchange: str
    symbol: str
    price_tick_size: Decimal | None
    quantity_step: Decimal | None
    min_quantity: Decimal | None
    min_notional: Decimal | None