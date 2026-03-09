from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.exchange_account import ExchangeAccount
from app.models.user import User


class UserService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_user(self, email: str, password: str) -> User:
        existing_user = self.db.execute(
            select(User).where(User.email == email)
        ).scalar_one_or_none()

        if existing_user is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists.",
            )

        hashed_password = hash_password(password)

        user = User(
            email=email,
            hashed_password=hashed_password,
            is_active=True,
            is_superuser=False,
        )

        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        return user

    def get_user_by_id(self, user_id: int) -> User:
        user = self.db.execute(
            select(User).where(User.id == user_id)
        ).scalar_one_or_none()

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        return user

    def get_user_exchange_accounts(self, user_id: int) -> list[ExchangeAccount]:
        self.get_user_by_id(user_id)

        accounts = self.db.execute(
            select(ExchangeAccount).where(ExchangeAccount.user_id == user_id)
        ).scalars().all()

        return list(accounts)