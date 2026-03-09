from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.exchange_account import ExchangeAccountRead
from app.schemas.user import UserCreate, UserRead
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserRead)
def create_user(payload: UserCreate, db: Session = Depends(get_db)) -> UserRead:
    service = UserService(db)
    user = service.create_user(
        email=payload.email,
        password=payload.password,
    )
    return user


@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: int, db: Session = Depends(get_db)) -> UserRead:
    service = UserService(db)
    user = service.get_user_by_id(user_id)
    return user


@router.get("/{user_id}/exchange-accounts", response_model=list[ExchangeAccountRead])
def get_user_exchange_accounts(
    user_id: int,
    db: Session = Depends(get_db),
) -> list[ExchangeAccountRead]:
    service = UserService(db)
    accounts = service.get_user_exchange_accounts(user_id)
    return [ExchangeAccountRead.model_validate(account) for account in accounts]