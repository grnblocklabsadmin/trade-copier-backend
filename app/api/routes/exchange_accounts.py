from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.exchange_account import (
    ExchangeAccountCreate,
    ExchangeAccountRead,
    ExchangeBalanceRead,
    ExchangeConnectionTestResult,
    ExchangeMarketSpecRead,
    ExchangePositionRead,
)
from app.services.exchange_account_service import ExchangeAccountService
from app.services.exchange_client_service import ExchangeClientService

router = APIRouter(prefix="/exchange-accounts", tags=["exchange-accounts"])


@router.post("", response_model=ExchangeAccountRead)
def create_exchange_account(
    payload: ExchangeAccountCreate,
    db: Session = Depends(get_db),
) -> ExchangeAccountRead:
    service = ExchangeAccountService(db)
    account = service.create_exchange_account(
        user_id=payload.user_id,
        exchange=payload.exchange,
        account_name=payload.account_name,
        api_key=payload.api_key,
        api_secret=payload.api_secret,
    )
    return account


@router.get("/{account_id}", response_model=ExchangeAccountRead)
def get_exchange_account(
    account_id: int,
    db: Session = Depends(get_db),
) -> ExchangeAccountRead:
    service = ExchangeAccountService(db)
    account = service.get_exchange_account_by_id(account_id)
    return account


@router.post("/{account_id}/test-connection", response_model=ExchangeConnectionTestResult)
def test_exchange_connection(
    account_id: int,
    db: Session = Depends(get_db),
) -> ExchangeConnectionTestResult:
    client_service = ExchangeClientService(db)
    adapter = client_service.get_adapter_for_account(account_id)

    success = adapter.test_connection()

    return ExchangeConnectionTestResult(
        account_id=account_id,
        exchange=adapter.get_exchange_name(),
        success=success,
    )


@router.get("/{account_id}/balance", response_model=ExchangeBalanceRead)
def get_exchange_balance(
    account_id: int,
    db: Session = Depends(get_db),
) -> ExchangeBalanceRead:
    client_service = ExchangeClientService(db)
    adapter = client_service.get_adapter_for_account(account_id)

    balance = adapter.fetch_balance()

    return ExchangeBalanceRead(
        account_id=account_id,
        exchange=adapter.get_exchange_name(),
        total_balance=balance.total_balance,
        available_balance=balance.available_balance,
        margin_balance=balance.margin_balance,
    )


@router.get("/{account_id}/positions", response_model=list[ExchangePositionRead])
def get_exchange_positions(
    account_id: int,
    db: Session = Depends(get_db),
) -> list[ExchangePositionRead]:
    client_service = ExchangeClientService(db)
    adapter = client_service.get_adapter_for_account(account_id)

    positions = adapter.fetch_positions()

    return [
        ExchangePositionRead(
            symbol=position.symbol,
            side=position.side,
            quantity=position.quantity,
            entry_price=position.entry_price,
            leverage=position.leverage,
            unrealized_pnl=position.unrealized_pnl,
        )
        for position in positions
    ]


@router.get("/{account_id}/market-specs", response_model=ExchangeMarketSpecRead)
def get_exchange_market_spec(
    account_id: int,
    symbol: str = Query(...),
    db: Session = Depends(get_db),
) -> ExchangeMarketSpecRead:
    client_service = ExchangeClientService(db)
    adapter = client_service.get_adapter_for_account(account_id)

    market_spec = adapter.fetch_market_spec(symbol)

    return ExchangeMarketSpecRead(
        account_id=account_id,
        exchange=adapter.get_exchange_name(),
        symbol=market_spec.symbol,
        price_tick_size=market_spec.price_tick_size,
        quantity_step=market_spec.quantity_step,
        min_quantity=market_spec.min_quantity,
        min_notional=market_spec.min_notional,
    )