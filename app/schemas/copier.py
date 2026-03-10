from decimal import Decimal

from pydantic import BaseModel


class CopierExecutionRequest(BaseModel):
    account_ids: list[int]
    symbol: str
    side: str
    risk_percent: Decimal
    leverage: Decimal
    current_price: Decimal


class CopierExecutionItem(BaseModel):
    account_id: int
    exchange: str
    symbol: str
    side: str
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


class CopierExecutionResponse(BaseModel):
    symbol: str
    side: str
    current_price: Decimal
    results: list[CopierExecutionItem]


class ManualCopierExecutionAccount(BaseModel):
    account_id: int
    exchange: str
    available_balance: Decimal
    quantity_step: Decimal
    min_quantity: Decimal | None = None
    min_notional: Decimal | None = None


class ManualCopierExecutionRequest(BaseModel):
    symbol: str
    side: str
    current_price: Decimal
    risk_percent: Decimal
    leverage: Decimal
    accounts: list[ManualCopierExecutionAccount]


class ManualCopierExecutionResponse(BaseModel):
    symbol: str
    side: str
    current_price: Decimal
    results: list[CopierExecutionItem]