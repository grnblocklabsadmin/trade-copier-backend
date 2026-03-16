from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.api.guards import ensure_live_execution_enabled
from app.core.execution_modes import ExecutionMode
from app.core.risk import (
    validate_account_ids,
    validate_manual_accounts,
    validate_risk_inputs,
)
from app.core.trading import normalize_order_side
from app.schemas.copier import (
    CopierDispatchItem,
    CopierDispatchRequest,
    CopierDispatchResponse,
    CopierExecutionItem,
    CopierExecutionRequest,
    CopierExecutionResponse,
    CopierPlanDispatchRequest,
    CopierPlanDispatchResponse,
    CopierPlanItemSchema,
    ManualCopierDispatchAccount,
    ManualCopierDispatchRequest,
    ManualCopierDispatchResponse,
    ManualCopierExecutionRequest,
    ManualCopierExecutionResponse,
)
from app.services.copier_execution_service import execute_copier_for_accounts
from app.services.copier_orchestration_service import execute_copier_from_master_position
from app.services.exchange_client_service import ExchangeClientService
from app.services.execution_log_service import ExecutionLogService
from app.services.trade_copier_execution_engine import TradeCopierExecutionEngine
from app.services.trade_copier_service import TradeCopierService
from app.sizing.position_sizing import (
    PositionSizingInput,
    calculate_position_size,
)

router = APIRouter(prefix="/copier", tags=["copier"])


@router.post("/execute", response_model=CopierExecutionResponse)
def execute_copier_plan(
    payload: CopierExecutionRequest,
    db: Session = Depends(get_db),
) -> CopierExecutionResponse:
    validate_account_ids(payload.account_ids)
    validate_risk_inputs(
        risk_percent=payload.risk_percent,
        leverage=payload.leverage,
        accounts_count=len(payload.account_ids),
    )

    exchange_client_service = ExchangeClientService(db)
    copier_service = TradeCopierService(exchange_client_service)
    normalized_side = normalize_order_side(payload.side)

    results: list[CopierExecutionItem] = []

    for account_id in payload.account_ids:
        exchange_name, balance, market_spec, sizing_result = (
            copier_service.build_execution_plan_for_account(
                account_id=account_id,
                symbol=payload.symbol,
                risk_percent=payload.risk_percent,
                leverage=payload.leverage,
                current_price=payload.current_price,
            )
        )

        results.append(
            CopierExecutionItem(
                account_id=account_id,
                exchange=exchange_name,
                symbol=payload.symbol,
                side=normalized_side,
                available_balance=balance.available_balance,
                allocated_margin=sizing_result.allocated_margin,
                target_notional=sizing_result.target_notional,
                raw_quantity=sizing_result.raw_quantity,
                rounded_quantity=sizing_result.rounded_quantity,
                final_notional=sizing_result.final_notional,
                quantity_step=market_spec.quantity_step,
                min_quantity=market_spec.min_quantity,
                min_notional=market_spec.min_notional,
                is_valid=sizing_result.is_valid,
                validation_errors=sizing_result.validation_errors,
            )
        )

    return CopierExecutionResponse(
        symbol=payload.symbol,
        side=normalized_side,
        current_price=payload.current_price,
        results=results,
    )


@router.post("/execute/manual", response_model=ManualCopierExecutionResponse)
def execute_manual_copier_plan(
    payload: ManualCopierExecutionRequest,
) -> ManualCopierExecutionResponse:
    validate_manual_accounts(payload.accounts)
    validate_risk_inputs(
        risk_percent=payload.risk_percent,
        leverage=payload.leverage,
        accounts_count=len(payload.accounts),
    )

    normalized_side = normalize_order_side(payload.side)
    results: list[CopierExecutionItem] = []

    for account in payload.accounts:
        sizing_result = calculate_position_size(
            PositionSizingInput(
                available_balance=account.available_balance,
                risk_percent=payload.risk_percent,
                leverage=payload.leverage,
                current_price=payload.current_price,
                quantity_step=account.quantity_step,
                min_quantity=account.min_quantity,
                min_notional=account.min_notional,
            )
        )

        results.append(
            CopierExecutionItem(
                account_id=account.account_id,
                exchange=account.exchange,
                symbol=payload.symbol,
                side=normalized_side,
                available_balance=account.available_balance,
                allocated_margin=sizing_result.allocated_margin,
                target_notional=sizing_result.target_notional,
                raw_quantity=sizing_result.raw_quantity,
                rounded_quantity=sizing_result.rounded_quantity,
                final_notional=sizing_result.final_notional,
                quantity_step=account.quantity_step,
                min_quantity=account.min_quantity,
                min_notional=account.min_notional,
                is_valid=sizing_result.is_valid,
                validation_errors=sizing_result.validation_errors,
            )
        )

    return ManualCopierExecutionResponse(
        symbol=payload.symbol,
        side=normalized_side,
        current_price=payload.current_price,
        results=results,
    )


@router.post("/dispatch", response_model=CopierDispatchResponse)
def dispatch_copier_plan(
    payload: CopierDispatchRequest,
    db: Session = Depends(get_db),
) -> CopierDispatchResponse:
    ensure_live_execution_enabled()
    validate_account_ids(payload.account_ids)
    validate_risk_inputs(
        risk_percent=payload.risk_percent,
        leverage=payload.leverage,
        accounts_count=len(payload.account_ids),
    )

    exchange_client_service = ExchangeClientService(db)
    execution_engine = TradeCopierExecutionEngine(exchange_client_service)
    normalized_side = normalize_order_side(payload.side)

    results: list[CopierDispatchItem] = []

    for account_id in payload.account_ids:
        exchange_name, market_spec, sizing_result, order_result = (
            execution_engine.dispatch_for_account(
                account_id=account_id,
                symbol=payload.symbol,
                side=normalized_side,
                risk_percent=payload.risk_percent,
                leverage=payload.leverage,
                current_price=payload.current_price,
            )
        )

        results.append(
            CopierDispatchItem(
                account_id=account_id,
                exchange=exchange_name,
                symbol=payload.symbol,
                side=normalized_side,
                rounded_quantity=sizing_result.rounded_quantity,
                final_notional=sizing_result.final_notional,
                is_valid=sizing_result.is_valid,
                validation_errors=sizing_result.validation_errors,
                dispatched=order_result.success,
                dispatch_status=order_result.status or "unknown",
                exchange_order_id=order_result.exchange_order_id,
                message=order_result.message,
            )
        )

    return CopierDispatchResponse(
        run_id=None,
        symbol=payload.symbol,
        side=normalized_side,
        current_price=payload.current_price,
        results=results,
    )


@router.post("/dispatch/manual", response_model=ManualCopierDispatchResponse)
def dispatch_manual_copier_plan(
    payload: ManualCopierDispatchRequest,
    db: Session = Depends(get_db),
) -> ManualCopierDispatchResponse:
    validate_manual_accounts(payload.accounts)
    validate_risk_inputs(
        risk_percent=payload.risk_percent,
        leverage=payload.leverage,
        accounts_count=len(payload.accounts),
    )

    log_service = ExecutionLogService(db)
    normalized_side = normalize_order_side(payload.side)
    exec_result = execute_copier_for_accounts(
        execution_mode=ExecutionMode.SIMULATED.value,
        symbol=payload.symbol,
        side=payload.side,
        current_price=payload.current_price,
        risk_percent=payload.risk_percent,
        leverage=payload.leverage,
        accounts=payload.accounts,
        log_service=log_service,
        event_type="copier_dispatch_manual",
    )

    return ManualCopierDispatchResponse(
        run_id=exec_result.run_id,
        symbol=payload.symbol,
        side=normalized_side,
        current_price=payload.current_price,
        results=exec_result.results,
    )


@router.post("/plan/dispatch", response_model=CopierPlanDispatchResponse)
def dispatch_copier_plan_from_master(
    payload: CopierPlanDispatchRequest,
    db: Session = Depends(get_db),
) -> CopierPlanDispatchResponse:
    """
    Dry-run copier: master position -> plan -> execution items -> simulated run.
    Uses copier_orchestration_service; execution_mode is always SIMULATED.
    """
    validate_manual_accounts(payload.follower_accounts)
    validate_risk_inputs(
        risk_percent=payload.risk_percent,
        leverage=payload.leverage,
        accounts_count=len(payload.follower_accounts),
    )

    follower_positions: dict[int, Decimal] = {}
    if payload.follower_positions:
        for k, v in payload.follower_positions.items():
            try:
                follower_positions[int(k)] = v
            except (ValueError, TypeError):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"follower_positions: invalid account_id key {k!r}.",
                ) from None

    accounts_by_id: dict[int, ManualCopierDispatchAccount] = {
        a.account_id: a for a in payload.follower_accounts
    }

    def get_account(account_id: int) -> ManualCopierDispatchAccount:
        if account_id not in accounts_by_id:
            raise ValueError(f"Account {account_id} not found in follower_accounts.")
        return accounts_by_id[account_id]

    log_service = ExecutionLogService(db)
    normalized_side = normalize_order_side(payload.side)

    try:
        out = execute_copier_from_master_position(
            master_symbol=payload.symbol,
            master_side=normalized_side,
            master_quantity=payload.master_quantity,
            execution_mode=ExecutionMode.SIMULATED.value,
            current_price=payload.current_price,
            risk_percent=payload.risk_percent,
            leverage=payload.leverage,
            follower_accounts=payload.follower_accounts,
            follower_positions=follower_positions or None,
            get_account=get_account,
            log_service=log_service,
            run_id=None,
            event_type="copier_dispatch_plan",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    plan_items_schema = [
        CopierPlanItemSchema(
            account_id=p.account_id,
            exchange=p.exchange,
            symbol=p.symbol,
            side=p.side,
            action=p.action,
            target_quantity=p.target_quantity,
            delta_quantity=p.delta_quantity,
            reason=p.reason,
        )
        for p in out.plan_items
    ]

    return CopierPlanDispatchResponse(
        run_id=out.run_id,
        plan_items=plan_items_schema,
        execution_items_count=len(out.execution_items),
        results=out.results,
    )