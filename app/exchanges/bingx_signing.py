"""
BingX API request signing helper.
"""
import hashlib
import hmac
import time
import urllib.parse


def build_bingx_signed_params(
    params: dict,
    api_key: str | None = None,
) -> dict:
    """
    Builds BingX request parameters before signing.
    """
    out = dict(params)
    out["timestamp"] = int(time.time() * 1000)
    if api_key is not None:
        out["apiKey"] = api_key
    return out


def sign_bingx_request(api_secret: str, params: dict) -> str:
    """
    Подпись запроса для BingX API: params сортируются по ключам, query string, HMAC SHA256, hex digest.
    """
    sorted_items = sorted(params.items())
    query = urllib.parse.urlencode(sorted_items)
    signature = hmac.new(
        api_secret.encode("utf-8"),
        query.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return signature
