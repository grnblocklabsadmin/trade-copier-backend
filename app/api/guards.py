from fastapi import HTTPException, status

from app.core.config import get_settings


def ensure_live_execution_enabled() -> None:
    settings = get_settings()

    if not settings.live_execution_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Live execution is disabled.",
        )