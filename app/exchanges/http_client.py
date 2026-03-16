"""
Async HTTP client abstraction для exchange adapters.
Реальный transport на базе httpx; stub_response сохраняет режим заглушки для тестов.
"""
from decimal import Decimal

import httpx

DEFAULT_TIMEOUT = 30.0


def _to_json_serializable(obj):
    """Приводит payload к виду, пригодному для JSON (в т.ч. Decimal -> str)."""
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, dict):
        return {k: _to_json_serializable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_json_serializable(v) for v in obj]
    return obj


class ExchangeHTTPClient:
    """
    Async HTTP client abstraction для exchange adapters.
    post: httpx.AsyncClient с timeout и json payload; при stub_response возвращает заглушку.
    """

    def __init__(self, stub_response: dict | None = None) -> None:
        self._stub_response = stub_response

    async def post(
        self,
        url: str,
        payload: dict,
        headers: dict | None = None,
    ) -> dict:
        if self._stub_response is not None:
            return self._stub_response
        request_headers = headers or {}
        body = _to_json_serializable(payload)
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            response = await client.post(
                url,
                json=body,
                headers=request_headers,
            )
            response.raise_for_status()
            return response.json()

    async def get(
        self,
        url: str,
        params: dict | None = None,
        headers: dict | None = None,
    ) -> dict:
        if self._stub_response is not None:
            return self._stub_response
        request_headers = headers or {}
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            response = await client.get(
                url,
                params=params or {},
                headers=request_headers,
            )
            response.raise_for_status()
            return response.json()
