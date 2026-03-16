"""
Реестр exchange adapters для выбора по названию биржи.
"""
from app.exchanges.binance_adapter import BinanceAdapter
from app.exchanges.bingx_adapter import BingXAdapter
from app.exchanges.bitget_adapter import BitgetAdapter
from app.exchanges.bybit_adapter import BybitAdapter
from app.exchanges.okx_adapter import OKXAdapter
from app.exchanges.stub_live_adapter import StubLiveAdapter

EXCHANGE_ADAPTERS: dict[str, type] = {
    "binance": BinanceAdapter,
    "bybit": BybitAdapter,
    "okx": OKXAdapter,
    "bitget": BitgetAdapter,
    "bingx": BingXAdapter,
    "stub": StubLiveAdapter,
}


def get_exchange_adapter(exchange: str):
    """
    Возвращает класс/фабрику адаптера для биржи из реестра.
    Если биржа неизвестна, выбрасывает ValueError.
    """
    if exchange not in EXCHANGE_ADAPTERS:
        raise ValueError(f"Unknown exchange: {exchange!r}")
    return EXCHANGE_ADAPTERS[exchange]
