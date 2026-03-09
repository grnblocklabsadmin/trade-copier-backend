from fastapi import APIRouter

from app.api.routes.copier import router as copier_router
from app.api.routes.exchange_accounts import router as exchange_accounts_router
from app.api.routes.execution import router as execution_router
from app.api.routes.health import router as health_router
from app.api.routes.trade import router as trade_router
from app.api.routes.users import router as users_router
from app.core.config import get_settings

settings = get_settings()

api_router = APIRouter(prefix=settings.api_v1_prefix)

api_router.include_router(health_router)
api_router.include_router(users_router)
api_router.include_router(exchange_accounts_router)
api_router.include_router(trade_router)
api_router.include_router(execution_router)
api_router.include_router(copier_router)