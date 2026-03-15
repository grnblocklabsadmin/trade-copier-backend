from dataclasses import dataclass
from decimal import Decimal

from fastapi import HTTPException, status


@dataclass(slots=True)
class CopierRiskLimits:
    max_risk_percent: Decimal = Decimal("0.05")
    max_leverage: Decimal = Decimal("20")
    max_accounts_per_dispatch: int = 20


def validate_account_ids(account_ids: list[int]) -> None:
    if not account_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="account_ids must not be empty.",
        )

    if len(set(account_ids)) != len(account_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="account_ids contains duplicates.",
        )


def validate_manual_accounts(accounts: list[object]) -> None:
    if not accounts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="accounts must not be empty.",
        )

    account_ids = [account.account_id for account in accounts]

    if len(set(account_ids)) != len(account_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="accounts contains duplicate account_id values.",
        )


def validate_risk_inputs(
    risk_percent: Decimal,
    leverage: Decimal,
    accounts_count: int,
    limits: CopierRiskLimits | None = None,
) -> None:
    limits = limits or CopierRiskLimits()

    if risk_percent <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="risk_percent must be greater than zero.",
        )

    if risk_percent > limits.max_risk_percent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"risk_percent exceeds max allowed value of {limits.max_risk_percent}.",
        )

    if leverage <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="leverage must be greater than zero.",
        )

    if leverage > limits.max_leverage:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"leverage exceeds max allowed value of {limits.max_leverage}.",
        )

    if accounts_count > limits.max_accounts_per_dispatch:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"accounts count exceeds max allowed value of "
                f"{limits.max_accounts_per_dispatch}."
            ),
        )