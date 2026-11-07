"""Gom router của tất cả module. Thêm module mới thì thêm một dòng ở đây."""
from fastapi import APIRouter

from app.modules.auth.presentation.router import router as auth_router
from app.modules.cards.presentation.router import router as cards_router
from app.modules.readings.presentation.router import me_router as me_router
from app.modules.readings.presentation.router import router as readings_router
from app.modules.spreads.presentation.router import router as spreads_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(spreads_router, prefix="/spreads", tags=["spreads"])
api_router.include_router(readings_router, prefix="/readings", tags=["readings"])
api_router.include_router(me_router, prefix="/me", tags=["quota"])  # GET /me/quota (use case của module quota)
api_router.include_router(cards_router, prefix="/admin/cards", tags=["admin"])
