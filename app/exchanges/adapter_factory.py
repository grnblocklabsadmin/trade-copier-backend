"""
Adapter factory: создание экземпляров адаптеров по имени биржи с опциональными http_client и credentials.
"""
from app.exchanges.adapter_registry import get_exchange_adapter
from app.exchanges.credentials import ExchangeAdapterCredentials
from app.exchanges.http_client import ExchangeHTTPClient


def create_exchange_adapter_instance(
    exchange: str,
    http_client: ExchangeHTTPClient | None = None,
    credentials: ExchangeAdapterCredentials | None = None,
):
    """
    Создаёт экземпляр адаптера биржи из реестра.
    Только BingXAdapter получает http_client и credentials; остальные адаптеры создаются без аргументов.
    """
    adapter_class = get_exchange_adapter(exchange)
    if exchange == "bingx":
        return adapter_class(
            http_client=http_client,
            credentials=credentials,
        )
    return adapter_class()
