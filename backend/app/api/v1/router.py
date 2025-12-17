from fastapi import APIRouter

from app.api.v1 import auth, users, entries, goals, chat, metrics

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(entries.router, prefix="/entries", tags=["entries"])
api_router.include_router(goals.router, prefix="/goals", tags=["goals"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
