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


class CopierDispatchRequest(BaseModel):
    account_ids: list[int]
    symbol: str
    side: str
    risk_percent: Decimal
    leverage: Decimal
    current_price: Decimal


class CopierDispatchItem(BaseModel):
    account_id: int
    exchange: str
    symbol: str
    side: str
    rounded_quantity: Decimal
    final_notional: Decimal
    is_valid: bool
    validation_errors: list[str]
    dispatched: bool
    dispatch_status: str
    exchange_order_id: str | None = None
    message: str | None = None


class CopierDispatchResponse(BaseModel):
    run_id: str | None
    symbol: str
    side: str
    current_price: Decimal
    results: list[CopierDispatchItem]


class ManualCopierDispatchAccount(BaseModel):
    account_id: int
    exchange: str
    available_balance: Decimal
    quantity_step: Decimal
    min_quantity: Decimal | None = None
    min_notional: Decimal | None = None


class ManualCopierDispatchRequest(BaseModel):
    symbol: str
    side: str
    current_price: Decimal
    risk_percent: Decimal
    leverage: Decimal
    accounts: list[ManualCopierDispatchAccount]


class ManualCopierDispatchResponse(BaseModel):
    run_id: str | None
    symbol: str
    side: str
    current_price: Decimal
    results: list[CopierDispatchItem]


# --- Plan dispatch (dry-run copier orchestration) ---


class CopierPlanItemSchema(BaseModel):
    """Pydantic mirror of CopierPlanItem for API response."""
    account_id: int
    exchange: str
    symbol: str
    side: str
    action: str
    target_quantity: Decimal
    delta_quantity: Decimal
    reason: str


class CopierPlanDispatchRequest(BaseModel):
    """Request for POST /copier/plan/dispatch (dry-run copier from master position)."""
    symbol: str
    side: str
    master_quantity: Decimal
    current_price: Decimal
    risk_percent: Decimal
    leverage: Decimal
    follower_accounts: list[ManualCopierDispatchAccount]
    follower_positions: dict[str, Decimal] | None = None


class CopierPlanDispatchResponse(BaseModel):
    """Response for POST /copier/plan/dispatch."""
    run_id: str
    plan_items: list[CopierPlanItemSchema]
    execution_items_count: int
    results: list[CopierDispatchItem]