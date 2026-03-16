from decimal import Decimal

from app.core.execution_modes import ExecutionMode
from app.core.execution_request import ExecutionRequest
from app.exchanges.base import OrderExecutionResult
from app.services.execution_idempotency import (
    build_execution_idempotency_key,
    key_inputs_from_execution_request,
)
from app.services.live_execution_service import execute_live_order_for_account
from app.services.manual_dispatch_service import (
    ManualDispatchAccountProcessingResult,
    process_manual_simulated_dispatch_for_account,
)
from app.sizing.position_sizing import PositionSizingResult

_executed_idempotency_keys: set[str] = set()


def _idempotent_skip_result() -> ManualDispatchAccountProcessingResult:
    """Минимальный result при пропуске по idempotency (без вызова execution)."""
    zero = Decimal("0")
    sizing = PositionSizingResult(
        allocated_margin=zero,
        target_notional=zero,
        raw_quantity=zero,
        rounded_quantity=zero,
        final_notional=zero,
        is_valid=True,
        validation_errors=[],
    )
    order_result = OrderExecutionResult(
        success=False,
        status="idempotent_skip",
        exchange_order_id=None,
        executed_quantity=None,
        message="Execution skipped: duplicate idempotency key.",
    )
    return ManualDispatchAccountProcessingResult(
        sizing_result=sizing,
        order_result=order_result,
        log_payload={"idempotent_skip": True},
    )


def execute_order_for_account(
    *,
    account,
    execution_request: ExecutionRequest,
) -> ManualDispatchAccountProcessingResult:
    """
    Execution Engine: выполняет ордер для одного аккаунта в зависимости от execution_mode.
    SIMULATED — manual_dispatch_service; LIVE — live_execution_service.
    In-memory idempotency guard: ключ фиксируется только после успешного возврата из execution;
    при исключении ключ не добавляется, повторная попытка не блокируется.
    """
    idempotency_key: str | None = None
    if execution_request.account_id is not None:
        try:
            inputs = key_inputs_from_execution_request(execution_request)
            idempotency_key = build_execution_idempotency_key(inputs)
            if idempotency_key in _executed_idempotency_keys:
                return _idempotent_skip_result()
        except ValueError:
            pass

    try:
        if execution_request.execution_mode == ExecutionMode.SIMULATED.value:
            result = process_manual_simulated_dispatch_for_account(
                account=account,
                execution_request=execution_request,
            )
        elif execution_request.execution_mode == ExecutionMode.LIVE.value:
            result = execute_live_order_for_account(execution_request=execution_request)
        else:
            raise ValueError(
                f"Unsupported execution_mode: {execution_request.execution_mode!r}"
            )
        if idempotency_key is not None:
            _executed_idempotency_keys.add(idempotency_key)
        return result
    except Exception:
        # Не фиксируем ключ при исключении — повторная попытка не должна блокироваться.
        raise
