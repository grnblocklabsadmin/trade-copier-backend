from decimal import Decimal

from app.core.config import get_settings
from app.core.execution_request import ExecutionRequest
from app.exchanges.adapter_models import AdapterOrderRequest, AdapterOrderResult
from app.exchanges.base import OrderExecutionResult
from app.exchanges.credentials_provider import get_exchange_credentials
from app.exchanges.http_client_provider import get_exchange_http_client
from app.services.exchange_client_service import (
    create_exchange_adapter,
    execute_adapter_order_with_rate_limit,
)
from app.services.manual_dispatch_service import ManualDispatchAccountProcessingResult
from app.sizing.position_sizing import PositionSizingResult


def build_order_execution_result_from_adapter_result(
    adapter_result: AdapterOrderResult,
) -> OrderExecutionResult:
    """
    Маппинг AdapterOrderResult → OrderExecutionResult для live execution pipeline.
    """
    return OrderExecutionResult(
        success=adapter_result.success,
        status=adapter_result.status,
        exchange_order_id=adapter_result.exchange_order_id,
        executed_quantity=adapter_result.executed_quantity,
        message=adapter_result.message,
    )


def build_adapter_order_request(execution_request: ExecutionRequest) -> AdapterOrderRequest:
    """
    Маппинг ExecutionRequest → AdapterOrderRequest для adapter layer.
    quantity пока заглушка (live sizing pipeline не реализован).
    """
    return AdapterOrderRequest(
        exchange=execution_request.exchange,
        symbol=execution_request.symbol,
        side=execution_request.side,
        quantity=Decimal("0"),
        price=execution_request.current_price,
        execution_mode=execution_request.execution_mode,
        account_id=execution_request.account_id,
        run_id=execution_request.run_id,
    )


def _build_live_stub_sizing_result(adapter_order_request: AdapterOrderRequest) -> PositionSizingResult:
    """Минимальный sizing_result для stub/bingx stub live path (контракт ManualDispatchAccountProcessingResult)."""
    q = adapter_order_request.quantity
    p = adapter_order_request.price or Decimal("0")
    return PositionSizingResult(
        allocated_margin=Decimal("0"),
        target_notional=q * p,
        raw_quantity=q,
        rounded_quantity=q,
        final_notional=q * p,
        is_valid=True,
        validation_errors=[],
    )


def execute_live_order_for_account(
    *,
    execution_request: ExecutionRequest,
) -> ManualDispatchAccountProcessingResult:
    """
    Live execution path: реальная отправка ордера на биржу для одного аккаунта.
    Для exchange=="stub" выполняется stub path через adapter.place_order(...).
    Для exchange=="bingx" credentials — из credentials_provider, http_client — из http_client_provider.
    """
    adapter_order_request = build_adapter_order_request(execution_request)

    if execution_request.exchange == "stub":
        adapter = create_exchange_adapter(execution_request.exchange)
        adapter_result = execute_adapter_order_with_rate_limit(adapter, adapter_order_request)
        order_result = build_order_execution_result_from_adapter_result(adapter_result)
        sizing_result = _build_live_stub_sizing_result(adapter_order_request)
        log_payload = {"live_stub": True, "status": adapter_result.status}
        return ManualDispatchAccountProcessingResult(
            sizing_result=sizing_result,
            order_result=order_result,
            log_payload=log_payload,
        )

    if execution_request.exchange == "bingx":
        settings = get_settings()
        if not settings.enable_real_trading:
            raise RuntimeError("Real trading is disabled by configuration.")
        http_client = get_exchange_http_client(
            exchange=execution_request.exchange,
            account_id=execution_request.account_id,
        )
        credentials = get_exchange_credentials(
            exchange=execution_request.exchange,
            account_id=execution_request.account_id,
        )
        adapter = create_exchange_adapter(
            execution_request.exchange,
            http_client=http_client,
            credentials=credentials,
        )
        adapter_result = execute_adapter_order_with_rate_limit(adapter, adapter_order_request)
        order_result = build_order_execution_result_from_adapter_result(adapter_result)
        sizing_result = _build_live_stub_sizing_result(adapter_order_request)
        log_payload = {
            "live_stub": True,
            "exchange": "bingx",
            "status": adapter_result.status,
        }
        return ManualDispatchAccountProcessingResult(
            sizing_result=sizing_result,
            order_result=order_result,
            log_payload=log_payload,
        )

    raise NotImplementedError("Live execution is not implemented yet.")
