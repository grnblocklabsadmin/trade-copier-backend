from decimal import Decimal

from pydantic import BaseModel


class TradePreviewRequest(BaseModel):
    account_id: int
    symbol: str
    risk_percent: Decimal
    leverage: Decimal
    current_price: Decimal


class TradePreviewResponse(BaseModel):
    account_id: int
    exchange: str
    symbol: str
    current_price: Decimal
    available_balance: Decimal
    allocated_margin: Decimal
    target_notional: Decimal
    raw_quantity: Decimal
    rounded_quantity: Decimal
    final_notional: Decimal
    quantity_step: Decimal
    min_quantity: Decimal | None
    min_notional: Decimal | None
    is_valid: bool
    validation_errors: list[str]


class DryRunTradePreviewRequest(BaseModel):
    symbol: str
    available_balance: Decimal
    risk_percent: Decimal
    leverage: Decimal
    current_price: Decimal
    quantity_step: Decimal
    min_quantity: Decimal | None = None
    min_notional: Decimal | None = None


class DryRunTradePreviewResponse(BaseModel):
    symbol: str
    current_price: Decimal
    available_balance: Decimal
    allocated_margin: Decimal
    target_notional: Decimal
    raw_quantity: Decimal
    rounded_quantity: Decimal
    final_notional: Decimal
    quantity_step: Decimal
    min_quantity: Decimal | None
    min_notional: Decimal | None
    is_valid: bool
    validation_errors: list[str]