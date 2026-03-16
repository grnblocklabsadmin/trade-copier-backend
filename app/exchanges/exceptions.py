"""
Типизированные исключения для exchange adapter / client layer.
"""


class ExchangeError(Exception):
    """Базовое исключение слоя биржи."""


class ExchangeAdapterNotImplementedError(ExchangeError):
    """Адаптер для данной биржи ещё не реализован."""


class ExchangeOrderPlacementError(ExchangeError):
    """Ошибка размещения ордера на бирже."""


class ExchangeRateLimitError(ExchangeError):
    """Превышен лимит запросов к бирже."""


class ExchangeAuthenticationError(ExchangeError):
    """Ошибка аутентификации с биржей."""


class ExchangeTransportError(ExchangeError):
    """Временная сетевая/transport ошибка (retryable)."""
