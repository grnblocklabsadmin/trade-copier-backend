"""
HTTP client provider для exchange adapters.
Runtime: реальный transport (httpx). Тесты инжектируют client со stub_response сами.
"""
from app.exchanges.http_client import ExchangeHTTPClient


def get_exchange_http_client(
    exchange: str,
    account_id: int | None = None,
) -> ExchangeHTTPClient | None:
    """
    Возвращает HTTP client для адаптера биржи (реальный transport для bingx).
    Тесты без сетевых вызовов: передают ExchangeHTTPClient(stub_response=...) напрямую.
    """
    if exchange == "bingx":
        return ExchangeHTTPClient()
    return None
