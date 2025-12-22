from fastapi import APIRouter

from app.api.v1 import auth, users, entries, goals, chat, metrics, transcribe, gamification, voice, summaries, observability, insights

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(entries.router, prefix="/entries", tags=["entries"])
api_router.include_router(goals.router, prefix="/goals", tags=["goals"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
api_router.include_router(transcribe.router, prefix="/transcribe", tags=["transcribe"])
api_router.include_router(gamification.router, prefix="/gamification", tags=["gamification"])
api_router.include_router(voice.router, prefix="/voice", tags=["voice"])
api_router.include_router(summaries.router, prefix="/summaries", tags=["summaries"])
api_router.include_router(observability.router, prefix="/observability", tags=["observability"])
api_router.include_router(insights.router, prefix="/insights", tags=["insights"])
