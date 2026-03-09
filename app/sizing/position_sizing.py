from dataclasses import dataclass, field
from decimal import Decimal, ROUND_DOWN


@dataclass(slots=True)
class PositionSizingInput:
    available_balance: Decimal
    risk_percent: Decimal
    leverage: Decimal
    current_price: Decimal
    quantity_step: Decimal
    min_quantity: Decimal | None = None
    min_notional: Decimal | None = None


@dataclass(slots=True)
class PositionSizingResult:
    allocated_margin: Decimal
    target_notional: Decimal
    raw_quantity: Decimal
    rounded_quantity: Decimal
    final_notional: Decimal
    is_valid: bool
    validation_errors: list[str] = field(default_factory=list)


def round_down_to_step(value: Decimal, step: Decimal) -> Decimal:
    if step <= 0:
        raise ValueError("quantity_step must be greater than zero.")

    steps = (value / step).to_integral_value(rounding=ROUND_DOWN)
    return steps * step


def calculate_position_size(data: PositionSizingInput) -> PositionSizingResult:
    validation_errors: list[str] = []

    if data.available_balance <= 0:
        validation_errors.append("available_balance must be greater than zero.")

    if data.risk_percent <= 0:
        validation_errors.append("risk_percent must be greater than zero.")

    if data.leverage <= 0:
        validation_errors.append("leverage must be greater than zero.")

    if data.current_price <= 0:
        validation_errors.append("current_price must be greater than zero.")

    if data.quantity_step <= 0:
        validation_errors.append("quantity_step must be greater than zero.")

    if validation_errors:
        return PositionSizingResult(
            allocated_margin=Decimal("0"),
            target_notional=Decimal("0"),
            raw_quantity=Decimal("0"),
            rounded_quantity=Decimal("0"),
            final_notional=Decimal("0"),
            is_valid=False,
            validation_errors=validation_errors,
        )

    allocated_margin = data.available_balance * data.risk_percent
    target_notional = allocated_margin * data.leverage
    raw_quantity = target_notional / data.current_price
    rounded_quantity = round_down_to_step(raw_quantity, data.quantity_step)
    final_notional = rounded_quantity * data.current_price

    if data.min_quantity is not None and rounded_quantity < data.min_quantity:
        validation_errors.append("rounded_quantity is below min_quantity.")

    if data.min_notional is not None and final_notional < data.min_notional:
        validation_errors.append("final_notional is below min_notional.")

    return PositionSizingResult(
        allocated_margin=allocated_margin,
        target_notional=target_notional,
        raw_quantity=raw_quantity,
        rounded_quantity=rounded_quantity,
        final_notional=final_notional,
        is_valid=len(validation_errors) == 0,
        validation_errors=validation_errors,
    )