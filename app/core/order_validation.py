from dataclasses import dataclass, field
from decimal import Decimal
from typing import Literal

from app.sizing.position_sizing import round_down_to_step


ExecutionMode = Literal["simulated", "live"]
OrderSide = Literal["buy", "sell"]


@dataclass(slots=True)
class OrderRequestValidationInput:
    execution_mode: str
    side: str
    price: Decimal
    requested_quantity: Decimal
    quantity_step: Decimal | None
    min_quantity: Decimal | None
    min_notional: Decimal | None
    final_notional: Decimal | None = None
    run_id: str | None = None
    account_id: int | None = None
    exchange: str | None = None
    symbol: str | None = None


@dataclass(slots=True)
class OrderRequestValidationResult:
    is_valid: bool
    status: str
    errors: list[str] = field(default_factory=list)


def _is_final_notional_consistent(
    price: Decimal,
    quantity: Decimal,
    final_notional: Decimal,
    *,
    epsilon: Decimal = Decimal("0.00000001"),
) -> bool:
    expected = price * quantity
    diff = expected - final_notional
    if diff < 0:
        diff = -diff
    return diff <= epsilon


def validate_order_request(data: OrderRequestValidationInput) -> OrderRequestValidationResult:
    errors: list[str] = []

    if data.execution_mode not in ("simulated", "live"):
        errors.append("invalid_execution_mode")

    allowed_sides = {"buy", "sell"}
    if data.side.lower() not in allowed_sides:
        errors.append("invalid_side")

    if data.price is None or data.price <= 0:
        errors.append("price_must_be_positive")

    if data.requested_quantity is None or data.requested_quantity <= 0:
        errors.append("requested_quantity_must_be_positive")

    if (
        data.min_quantity is not None
        and data.requested_quantity is not None
        and data.requested_quantity < data.min_quantity
    ):
        errors.append("requested_quantity_below_min_quantity")

    if (
        data.min_notional is not None
        and data.final_notional is not None
        and data.final_notional < data.min_notional
    ):
        errors.append("final_notional_below_min_notional")

    if (
        data.quantity_step is not None
        and data.quantity_step > 0
        and data.requested_quantity is not None
    ):
        try:
            rounded = round_down_to_step(data.requested_quantity, data.quantity_step)
            if rounded != data.requested_quantity:
                errors.append("requested_quantity_not_aligned_to_step")
        except Exception:
            errors.append("quantity_step_validation_error")

    if (
        data.final_notional is not None
        and data.price is not None
        and data.requested_quantity is not None
        and data.price > 0
        and data.requested_quantity > 0
    ):
        if not _is_final_notional_consistent(
            price=data.price,
            quantity=data.requested_quantity,
            final_notional=data.final_notional,
        ):
            errors.append("final_notional_inconsistent_with_price_and_quantity")

    if errors:
        return OrderRequestValidationResult(
            is_valid=False,
            status="validation_failed",
            errors=errors,
        )

    return OrderRequestValidationResult(
        is_valid=True,
        status="validation_ok",
        errors=[],
    )

