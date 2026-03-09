from decimal import Decimal

from pydantic import BaseModel


class DryRunExecutionRequest(BaseModel):
    account_ids: list[int]
    symbol: str
    risk_percent: Decimal
    leverage: Decimal
    current_price: Decimal


class DryRunExecutionItem(BaseModel):
    account_id: int
    exchange: str
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


class DryRunExecutionResponse(BaseModel):
    symbol: str
    current_price: Decimal
    results: list[DryRunExecutionItem]


class ManualDryRunExecutionAccount(BaseModel):
    account_id: int
    exchange: str
    available_balance: Decimal
    quantity_step: Decimal
    min_quantity: Decimal | None = None
    min_notional: Decimal | None = None


class ManualDryRunExecutionRequest(BaseModel):
    symbol: str
    current_price: Decimal
    risk_percent: Decimal
    leverage: Decimal
    accounts: list[ManualDryRunExecutionAccount]


class ManualDryRunExecutionResponse(BaseModel):
    symbol: str
    current_price: Decimal
    results: list[DryRunExecutionItem]