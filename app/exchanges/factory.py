from fastapi import HTTPException, status

from app.exchanges.adapters.binance_futures import BinanceFuturesAdapter
from app.exchanges.base import BaseExchangeAdapter, ExchangeCredentials


class ExchangeAdapterFactory:
    @staticmethod
    def create_adapter(
        exchange: str,
        credentials: ExchangeCredentials,
    ) -> BaseExchangeAdapter:
        normalized_exchange = exchange.strip().lower()

        if normalized_exchange == "binance":
            return BinanceFuturesAdapter(credentials=credentials)

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported exchange: {exchange}",
        )