from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.crypto import decrypt_value
from app.exchanges.base import BaseExchangeAdapter, ExchangeCredentials
from app.exchanges.factory import ExchangeAdapterFactory
from app.models.exchange_account import ExchangeAccount


class ExchangeClientService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_adapter_for_account(self, account_id: int) -> BaseExchangeAdapter:
        exchange_account = self.db.execute(
            select(ExchangeAccount).where(ExchangeAccount.id == account_id)
        ).scalar_one_or_none()

        if exchange_account is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exchange account not found.",
            )

        credentials = ExchangeCredentials(
            api_key=decrypt_value(exchange_account.api_key),
            api_secret=decrypt_value(exchange_account.api_secret),
        )

        return ExchangeAdapterFactory.create_adapter(
            exchange=exchange_account.exchange,
            credentials=credentials,
        )