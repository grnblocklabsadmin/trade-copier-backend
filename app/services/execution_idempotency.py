"""
Minimal idempotency contract for execution pipeline.
Builds a deterministic key from execution context (no storage in this layer).
"""
from __future__ import annotations

from dataclasses import dataclass

from app.core.execution_request import ExecutionRequest

_IDEMPOTENCY_KEY_SEP = "|"


@dataclass(slots=True, frozen=True)
class ExecutionIdempotencyKeyInputs:
    """
    Typed inputs for building an execution idempotency key.
    Used to guard against double-sending the same order for an account.
    """
    run_id: str
    account_id: int
    exchange: str
    symbol: str
    side: str
    execution_mode: str


def build_execution_idempotency_key(inputs: ExecutionIdempotencyKeyInputs) -> str:
    """
    Build a deterministic string key from execution context.
    Same inputs always produce the same key; different inputs produce different keys.
    """
    return _IDEMPOTENCY_KEY_SEP.join([
        inputs.run_id,
        str(inputs.account_id),
        inputs.exchange,
        inputs.symbol,
        inputs.side,
        inputs.execution_mode,
    ])


def key_inputs_from_execution_request(execution_request: ExecutionRequest) -> ExecutionIdempotencyKeyInputs:
    """
    Build idempotency key inputs from ExecutionRequest (for use in execution pipeline).
    """
    if execution_request.account_id is None:
        raise ValueError("account_id is required for idempotency key")
    return ExecutionIdempotencyKeyInputs(
        run_id=execution_request.run_id,
        account_id=execution_request.account_id,
        exchange=execution_request.exchange,
        symbol=execution_request.symbol,
        side=execution_request.side,
        execution_mode=execution_request.execution_mode,
    )
