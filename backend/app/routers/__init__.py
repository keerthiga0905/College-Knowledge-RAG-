from app.routers.auth import router as auth_router
from app.routers.conversations import router as conversations_router
from app.routers.chat import router as chat_router
from app.routers.documents import router as documents_router
from app.routers.admin import router as admin_router

__all__ = ["auth_router", "conversations_router", "chat_router", "documents_router", "admin_router"]
