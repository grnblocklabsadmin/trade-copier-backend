"""
Типизированная структура credentials для adapter layer.
"""
from dataclasses import dataclass


@dataclass(slots=True)
class ExchangeAdapterCredentials:
    """
    Контейнер для adapter-layer exchange credentials, используемый при live execution.
    """
    exchange: str
    api_key: str | None
    api_secret: str | None
    passphrase: str | None = None
