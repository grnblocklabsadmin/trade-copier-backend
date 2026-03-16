"""Unit tests for execution idempotency key builder."""
from decimal import Decimal

import pytest

from app.core.execution_request import ExecutionRequest
from app.services.execution_idempotency import (
    ExecutionIdempotencyKeyInputs,
    build_execution_idempotency_key,
    key_inputs_from_execution_request,
)


def _base_inputs() -> ExecutionIdempotencyKeyInputs:
    return ExecutionIdempotencyKeyInputs(
        run_id="run-abc",
        account_id=1,
        exchange="bingx",
        symbol="BTCUSDT",
        side="buy",
        execution_mode="live",
    )


def test_same_inputs_produce_same_key():
    """Identical inputs must always yield the same idempotency key."""
    inputs = _base_inputs()
    key1 = build_execution_idempotency_key(inputs)
    key2 = build_execution_idempotency_key(inputs)
    assert key1 == key2


def test_different_run_id_produces_different_key():
    """Different run_id must yield different keys."""
    base = _base_inputs()
    other = ExecutionIdempotencyKeyInputs(
        run_id="run-xyz",
        account_id=base.account_id,
        exchange=base.exchange,
        symbol=base.symbol,
        side=base.side,
        execution_mode=base.execution_mode,
    )
    assert build_execution_idempotency_key(base) != build_execution_idempotency_key(other)


def test_different_account_id_produces_different_key():
    """Different account_id must yield different keys."""
    base = _base_inputs()
    other = ExecutionIdempotencyKeyInputs(
        run_id=base.run_id,
        account_id=2,
        exchange=base.exchange,
        symbol=base.symbol,
        side=base.side,
        execution_mode=base.execution_mode,
    )
    assert build_execution_idempotency_key(base) != build_execution_idempotency_key(other)


def test_different_exchange_produces_different_key():
    """Different exchange must yield different keys."""
    base = _base_inputs()
    other = ExecutionIdempotencyKeyInputs(
        run_id=base.run_id,
        account_id=base.account_id,
        exchange="stub",
        symbol=base.symbol,
        side=base.side,
        execution_mode=base.execution_mode,
    )
    assert build_execution_idempotency_key(base) != build_execution_idempotency_key(other)


def test_different_symbol_produces_different_key():
    """Different symbol must yield different keys."""
    base = _base_inputs()
    other = ExecutionIdempotencyKeyInputs(
        run_id=base.run_id,
        account_id=base.account_id,
        exchange=base.exchange,
        symbol="ETHUSDT",
        side=base.side,
        execution_mode=base.execution_mode,
    )
    assert build_execution_idempotency_key(base) != build_execution_idempotency_key(other)


def test_different_side_produces_different_key():
    """Different side must yield different keys."""
    base = _base_inputs()
    other = ExecutionIdempotencyKeyInputs(
        run_id=base.run_id,
        account_id=base.account_id,
        exchange=base.exchange,
        symbol=base.symbol,
        side="sell",
        execution_mode=base.execution_mode,
    )
    assert build_execution_idempotency_key(base) != build_execution_idempotency_key(other)


def test_different_execution_mode_produces_different_key():
    """Different execution_mode must yield different keys."""
    base = _base_inputs()
    other = ExecutionIdempotencyKeyInputs(
        run_id=base.run_id,
        account_id=base.account_id,
        exchange=base.exchange,
        symbol=base.symbol,
        side=base.side,
        execution_mode="simulated",
    )
    assert build_execution_idempotency_key(base) != build_execution_idempotency_key(other)


def test_key_inputs_from_execution_request():
    """key_inputs_from_execution_request builds inputs and key is deterministic."""
    req = ExecutionRequest(
        execution_mode="live",
        account_id=42,
        exchange="bingx",
        symbol="BTCUSDT",
        side="buy",
        current_price=Decimal("50000"),
        risk_percent=Decimal("0.01"),
        leverage=Decimal("2"),
        run_id="run-req",
    )
    inputs = key_inputs_from_execution_request(req)
    assert inputs.run_id == "run-req"
    assert inputs.account_id == 42
    assert inputs.exchange == "bingx"
    assert inputs.symbol == "BTCUSDT"
    assert inputs.side == "buy"
    assert inputs.execution_mode == "live"
    key1 = build_execution_idempotency_key(inputs)
    key2 = build_execution_idempotency_key(key_inputs_from_execution_request(req))
    assert key1 == key2


def test_key_inputs_from_execution_request_without_account_id_raises():
    """key_inputs_from_execution_request raises when account_id is None."""
    req = ExecutionRequest(
        execution_mode="live",
        account_id=None,
        exchange="bingx",
        symbol="BTCUSDT",
        side="buy",
        current_price=Decimal("50000"),
        risk_percent=Decimal("0.01"),
        leverage=Decimal("2"),
        run_id="run-req",
    )
    with pytest.raises(ValueError, match="account_id is required"):
        key_inputs_from_execution_request(req)
