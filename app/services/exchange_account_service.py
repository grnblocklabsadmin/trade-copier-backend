from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.crypto import encrypt_value
from app.models.exchange_account import ExchangeAccount
from app.models.user import User


class ExchangeAccountService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_exchange_account(
        self,
        user_id: int,
        exchange: str,
        account_name: str,
        api_key: str,
        api_secret: str,
    ) -> ExchangeAccount:
        user = self.db.execute(
            select(User).where(User.id == user_id)
        ).scalar_one_or_none()

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        encrypted_api_key = encrypt_value(api_key)
        encrypted_api_secret = encrypt_value(api_secret)

        exchange_account = ExchangeAccount(
            user_id=user_id,
            exchange=exchange,
            account_name=account_name,
            api_key=encrypted_api_key,
            api_secret=encrypted_api_secret,
            is_active=True,
        )

        self.db.add(exchange_account)
        self.db.commit()
        self.db.refresh(exchange_account)

        return exchange_account

    def get_exchange_account_by_id(self, account_id: int) -> ExchangeAccount:
        account = self.db.execute(
            select(ExchangeAccount).where(ExchangeAccount.id == account_id)
        ).scalar_one_or_none()

        if account is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exchange account not found.",
            )

        return account