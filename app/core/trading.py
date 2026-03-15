from fastapi import HTTPException, status


VALID_ORDER_SIDES = {"buy", "sell"}


def normalize_order_side(side: str) -> str:
    normalized = side.strip().lower()

    if normalized in {"buy", "long"}:
        return "buy"

    if normalized in {"sell", "short"}:
        return "sell"

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid side. Use buy/sell or long/short.",
    )