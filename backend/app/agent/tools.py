from typing import List, Optional
from langchain_core.tools import tool

from app.services.vector_search import search_by_text


@tool
async def retrieve_similar_entries(
    query: str,
    user_id: str,
    db,
    embedding_service,
    limit: int = 5,
) -> List[dict]:
    """
    Retrieve journal entries similar to the query using vector similarity search.
    Use this to find past entries that relate to what the user is currently discussing.

    Args:
        query: The text to find similar entries for
        user_id: The user's ID
        limit: Maximum number of entries to return

    Returns:
        List of similar entries with content, date, and similarity score
    """
    return await search_by_text(db, query, user_id, embedding_service, limit=limit)


@tool
async def get_user_goals(
    user_id: str,
    db,
    status: Optional[str] = "active",
) -> List[dict]:
    """
    Retrieve user's goals. Use this to understand what the user is working toward
    and to ask about their progress.

    Args:
        user_id: The user's ID
        status: Filter by goal status (active, completed, paused, abandoned)

    Returns:
        List of goals with title, description, status, and target_date
    """
    from app.crud.goal import goal_crud

    goals = await goal_crud.get_multi(db, user_id, status=status)
    return [
        {
            "id": str(g.id),
            "title": g.title,
            "description": g.description,
            "status": g.status,
            "target_date": g.target_date.isoformat() if g.target_date else None,
        }
        for g in goals
    ]


@tool
async def get_recent_entries(
    user_id: str,
    db,
    days: int = 7,
    limit: int = 5,
) -> List[dict]:
    """
    Retrieve user's recent journal entries. Use this to understand what the user
    has been thinking about lately.

    Args:
        user_id: The user's ID
        days: Number of days to look back
        limit: Maximum entries to return

    Returns:
        List of recent entries with title, content preview, mood, and date
    """
    from app.crud.entry import entry_crud

    entries = await entry_crud.get_recent(db, user_id, days=days, limit=limit)
    return [
        {
            "id": str(e.id),
            "title": e.title,
            "content": e.content[:200] + "..." if len(e.content) > 200 else e.content,
            "mood": e.mood,
            "created_at": e.created_at.isoformat(),
        }
        for e in entries
    ]
