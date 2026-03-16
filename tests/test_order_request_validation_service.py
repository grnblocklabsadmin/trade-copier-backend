from decimal import Decimal

from app.core.order_validation import OrderRequestValidationResult
from app.services.order_request_validation_service import (
    build_manual_simulated_order_result,
)
from app.sizing.position_sizing import PositionSizingResult


def _valid_sizing_result() -> PositionSizingResult:
    return PositionSizingResult(
        allocated_margin=Decimal("10"),
        target_notional=Decimal("20"),
        raw_quantity=Decimal("0.0004"),
        rounded_quantity=Decimal("0.0004"),
        final_notional=Decimal("20"),
        is_valid=True,
        validation_errors=[],
    )


def _invalid_sizing_result() -> PositionSizingResult:
    return PositionSizingResult(
        allocated_margin=Decimal("0"),
        target_notional=Decimal("0"),
        raw_quantity=Decimal("0"),
        rounded_quantity=Decimal("0"),
        final_notional=Decimal("0"),
        is_valid=False,
        validation_errors=["available_balance must be greater than zero."],
    )


def test_build_manual_simulated_order_result_sizing_invalid():
    sizing_result = _invalid_sizing_result()
    order_request_validation = OrderRequestValidationResult(
        is_valid=True,
        status="validation_ok",
        errors=[],
    )
    result = build_manual_simulated_order_result(
        sizing_result=sizing_result,
        order_request_validation=order_request_validation,
    )
    assert result.success is False
    assert result.status == "validation_failed"
    assert result.executed_quantity is None


def test_build_manual_simulated_order_result_order_request_invalid():
    sizing_result = _valid_sizing_result()
    order_request_validation = OrderRequestValidationResult(
        is_valid=False,
        status="validation_failed",
        errors=["invalid_side"],
    )
    result = build_manual_simulated_order_result(
        sizing_result=sizing_result,
        order_request_validation=order_request_validation,
    )
    assert result.success is False
    assert result.status == "order_request_validation_failed"
    assert result.executed_quantity is None


def test_build_manual_simulated_order_result_both_valid():
    sizing_result = _valid_sizing_result()
    order_request_validation = OrderRequestValidationResult(
        is_valid=True,
        status="validation_ok",
        errors=[],
    )
    result = build_manual_simulated_order_result(
        sizing_result=sizing_result,
        order_request_validation=order_request_validation,
    )
    assert result.success is True
    assert result.status == "simulated_dispatched"
    assert result.executed_quantity == sizing_result.rounded_quantity
