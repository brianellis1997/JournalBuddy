from typing import List, Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def search_similar_entries(
    db: AsyncSession,
    query_embedding: List[float],
    user_id: str,
    limit: int = 5,
    exclude_id: Optional[str] = None,
) -> List[dict]:
    embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

    exclude_clause = ""
    params = {
        "user_id": user_id,
        "limit": limit,
    }

    if exclude_id:
        exclude_clause = "AND id != :exclude_id"
        params["exclude_id"] = exclude_id

    query = text(f"""
        SELECT
            id,
            title,
            content,
            mood,
            created_at,
            1 - (embedding <=> '{embedding_str}'::vector) as similarity
        FROM entries
        WHERE user_id = :user_id
        AND embedding IS NOT NULL
        {exclude_clause}
        ORDER BY embedding <=> '{embedding_str}'::vector
        LIMIT :limit
    """)

    result = await db.execute(query, params)
    rows = result.fetchall()

    return [
        {
            "id": str(row.id),
            "title": row.title,
            "content": row.content[:300] + "..." if len(row.content) > 300 else row.content,
            "mood": row.mood,
            "created_at": row.created_at.isoformat(),
            "similarity": float(row.similarity),
        }
        for row in rows
    ]


async def search_by_text(
    db: AsyncSession,
    query_text: str,
    user_id: str,
    embedding_service,
    limit: int = 5,
) -> List[dict]:
    embedding = await embedding_service.generate_embedding(query_text)
    return await search_similar_entries(db, embedding, user_id, limit=limit)
