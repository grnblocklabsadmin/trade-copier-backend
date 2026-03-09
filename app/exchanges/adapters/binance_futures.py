from decimal import Decimal

import ccxt
from ccxt.base.errors import AuthenticationError, BadSymbol, ExchangeError, NetworkError
from fastapi import HTTPException, status

from app.exchanges.base import (
    BalanceSnapshot,
    BaseExchangeAdapter,
    ExchangeCredentials,
    MarketSpecSnapshot,
    PositionSnapshot,
)


class BinanceFuturesAdapter(BaseExchangeAdapter):
    def __init__(self, credentials: ExchangeCredentials) -> None:
        super().__init__(credentials)

    def get_exchange_name(self) -> str:
        return "binance"

    def _build_client(self) -> ccxt.binance:
        return ccxt.binance(
            {
                "apiKey": self.credentials.api_key,
                "secret": self.credentials.api_secret,
                "enableRateLimit": True,
                "options": {
                    "defaultType": "swap",
                },
            }
        )

    def _build_public_client(self) -> ccxt.binance:
        return ccxt.binance(
            {
                "enableRateLimit": True,
                "options": {
                    "defaultType": "swap",
                },
            }
        )

    def test_connection(self) -> bool:
        client = self._build_client()

        try:
            client.fetch_balance()
            return True
        except (AuthenticationError, ExchangeError, NetworkError):
            return False

    def fetch_balance(self) -> BalanceSnapshot:
        client = self._build_client()

        try:
            balance = client.fetch_balance()
        except AuthenticationError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Exchange authentication failed.",
            ) from exc
        except NetworkError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Exchange network error.",
            ) from exc
        except ExchangeError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Exchange rejected the balance request.",
            ) from exc

        total_usdt = Decimal(str(balance.get("total", {}).get("USDT", "0")))
        free_usdt = Decimal(str(balance.get("free", {}).get("USDT", "0")))

        margin_balance = total_usdt

        info = balance.get("info")
        if isinstance(info, dict):
            assets = info.get("assets")
            if isinstance(assets, list):
                usdt_asset = next(
                    (
                        asset
                        for asset in assets
                        if str(asset.get("asset", "")).upper() == "USDT"
                    ),
                    None,
                )
                if usdt_asset is not None:
                    margin_balance = Decimal(
                        str(usdt_asset.get("marginBalance", total_usdt))
                    )

        return BalanceSnapshot(
            total_balance=total_usdt,
            available_balance=free_usdt,
            margin_balance=margin_balance,
        )

    def fetch_positions(self) -> list[PositionSnapshot]:
        client = self._build_client()

        try:
            positions = client.fetch_positions()
        except AuthenticationError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Exchange authentication failed.",
            ) from exc
        except NetworkError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Exchange network error.",
            ) from exc
        except ExchangeError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Exchange rejected the positions request.",
            ) from exc

        normalized_positions: list[PositionSnapshot] = []

        for position in positions:
            contracts = Decimal(str(position.get("contracts") or "0"))
            if contracts == 0:
                continue

            side = str(position.get("side") or "").lower()
            symbol = str(position.get("symbol") or "")
            entry_price = Decimal(str(position.get("entryPrice") or "0"))

            leverage_raw = position.get("leverage")
            leverage = (
                Decimal(str(leverage_raw))
                if leverage_raw not in (None, "")
                else None
            )

            unrealized_pnl_raw = position.get("unrealizedPnl")
            unrealized_pnl = (
                Decimal(str(unrealized_pnl_raw))
                if unrealized_pnl_raw not in (None, "")
                else None
            )

            normalized_positions.append(
                PositionSnapshot(
                    symbol=symbol,
                    side=side,
                    quantity=contracts,
                    entry_price=entry_price,
                    leverage=leverage,
                    unrealized_pnl=unrealized_pnl,
                )
            )

        return normalized_positions

    def fetch_market_spec(self, symbol: str) -> MarketSpecSnapshot:
        client = self._build_public_client()

        try:
            markets = client.load_markets()
        except NetworkError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Exchange network error.",
            ) from exc
        except ExchangeError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Exchange rejected the market specs request.",
            ) from exc

        market = markets.get(symbol)

        if market is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Symbol not found: {symbol}",
            )

        limits = market.get("limits", {})
        precision = market.get("precision", {})

        min_quantity_raw = limits.get("amount", {}).get("min")
        min_notional_raw = limits.get("cost", {}).get("min")
        quantity_step_raw = precision.get("amount")
        price_tick_size_raw = precision.get("price")

        min_quantity = (
            Decimal(str(min_quantity_raw))
            if min_quantity_raw not in (None, "")
            else None
        )
        min_notional = (
            Decimal(str(min_notional_raw))
            if min_notional_raw not in (None, "")
            else None
        )
        quantity_step = (
            Decimal(str(quantity_step_raw))
            if quantity_step_raw not in (None, "")
            else None
        )
        price_tick_size = (
            Decimal(str(price_tick_size_raw))
            if price_tick_size_raw not in (None, "")
            else None
        )

        return MarketSpecSnapshot(
            symbol=str(market.get("symbol", symbol)),
            price_tick_size=price_tick_size,
            quantity_step=quantity_step,
            min_quantity=min_quantity,
            min_notional=min_notional,
        )