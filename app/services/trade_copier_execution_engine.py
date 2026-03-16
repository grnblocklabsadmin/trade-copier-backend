from app.exchanges.base import MarketOrderRequest, OrderExecutionResult
from app.services.exchange_client_service import ExchangeClientService
from app.sizing.position_sizing import (
    PositionSizingInput,
    PositionSizingResult,
    calculate_position_size,
)

from app.core.order_validation import (
    OrderRequestValidationInput,
    validate_order_request,
)


class TradeCopierExecutionEngine:
    def __init__(self, exchange_client_service: ExchangeClientService) -> None:
        self.exchange_client_service = exchange_client_service

    def build_plan_for_account(
        self,
        account_id: int,
        symbol,
        risk_percent,
        leverage,
        current_price,
    ) -> tuple[object, str, object, object, PositionSizingResult]:
        adapter = self.exchange_client_service.get_adapter_for_account(account_id)

        balance = adapter.fetch_balance()
        market_spec = adapter.fetch_market_spec(symbol)

        if market_spec.quantity_step is None:
            raise ValueError("quantity_step is missing in market specs.")

        sizing_result = calculate_position_size(
            PositionSizingInput(
                available_balance=balance.available_balance,
                risk_percent=risk_percent,
                leverage=leverage,
                current_price=current_price,
                quantity_step=market_spec.quantity_step,
                min_quantity=market_spec.min_quantity,
                min_notional=market_spec.min_notional,
            )
        )

        return adapter, adapter.get_exchange_name(), balance, market_spec, sizing_result

    def dispatch_for_account(
        self,
        account_id: int,
        symbol,
        side,
        risk_percent,
        leverage,
        current_price,
    ) -> tuple[str, object, PositionSizingResult, OrderExecutionResult]:
        adapter, exchange_name, _balance, market_spec, sizing_result = self.build_plan_for_account(
            account_id=account_id,
            symbol=symbol,
            risk_percent=risk_percent,
            leverage=leverage,
            current_price=current_price,
        )

        if not sizing_result.is_valid:
            return (
                exchange_name,
                market_spec,
                sizing_result,
                OrderExecutionResult(
                    success=False,
                    status="validation_failed",
                    executed_quantity=None,
                    message="Order was not dispatched because validation failed.",
                ),
            )

        order_validation_input = OrderRequestValidationInput(
            execution_mode="simulated",
            side=side,
            price=current_price,
            requested_quantity=sizing_result.rounded_quantity,
            quantity_step=market_spec.quantity_step,
            min_quantity=market_spec.min_quantity,
            min_notional=market_spec.min_notional,
            final_notional=sizing_result.final_notional,
            run_id=None,
            account_id=account_id,
            exchange=exchange_name,
            symbol=symbol,
        )

        order_validation_result = validate_order_request(order_validation_input)

        if not order_validation_result.is_valid:
            return (
                exchange_name,
                market_spec,
                sizing_result,
                OrderExecutionResult(
                    success=False,
                    status=order_validation_result.status,
                    executed_quantity=None,
                    message="; ".join(order_validation_result.errors),
                ),
            )

        order_result = adapter.place_market_order(
            MarketOrderRequest(
                symbol=symbol,
                side=side,
                quantity=sizing_result.rounded_quantity,
            )
        )

        return exchange_name, market_spec, sizing_result, order_result