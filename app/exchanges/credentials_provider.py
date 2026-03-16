"""
Credentials provider skeleton for exchange adapters.
"""
from app.exchanges.credentials import ExchangeAdapterCredentials


def get_exchange_credentials(
    exchange: str,
    account_id: int | None = None,
) -> ExchangeAdapterCredentials | None:
    """
    Возвращает credentials для адаптера биржи (stub или из хранилища).
    Пока только stub для bingx; остальные биржи → None.
    """
    if exchange == "bingx":
        return ExchangeAdapterCredentials(
            exchange="bingx",
            api_key="",
            api_secret="",
            passphrase=None,
        )
    return None
