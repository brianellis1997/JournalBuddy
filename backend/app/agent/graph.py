from typing import AsyncGenerator, Optional
from groq import AsyncGroq
import logging

from app.config import settings
from app.services.embedding import embedding_service
from app.services.vector_search import search_by_text
from app.crud.goal import goal_crud
from app.crud.entry import entry_crud

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are JournalBuddy, a thoughtful and empathetic AI journaling companion. Your role is to:

1. **Understand & Reflect**: Read the user's journal entry or message carefully. Acknowledge their feelings and thoughts with genuine empathy.

2. **Connect to Past**: When relevant context from past entries is provided, reference these connections naturally: "I noticed you wrote something similar last month about..." or "This reminds me of what you shared on [date]..."

3. **Track Goals**: When the user's goals are provided, gently check in on goal progress when relevant. Ask questions like "How's your progress on [goal]?" or "Does this relate to your goal of [goal]?"

4. **Ask Meaningful Questions**: Always end with 1-2 thoughtful follow-up questions that encourage deeper reflection. Focus on:
   - Emotions: "How did that make you feel?"
   - Growth: "What do you think you learned from this?"
   - Connections: "Does this remind you of any past experiences?"
   - Goals: "How does this relate to your goal of [goal]?"
   - Action: "What's one small step you could take?"

5. **Be Supportive, Not Directive**: Offer observations and questions, not advice unless explicitly asked. Your job is to help the user explore their own thoughts and feelings.

Remember: Be warm, curious, and genuinely interested in the user's journey. You're a trusted companion, not a therapist or coach."""


class JournalAgent:
    def __init__(self):
        self.client = AsyncGroq(api_key=settings.groq_api_key)
        self.model = settings.groq_model

    async def get_context(self, db, user_id: str, user_message: str) -> dict:
        from uuid import UUID
        user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id

        context = {
            "similar_entries": [],
            "goals": [],
            "recent_entries": [],
        }

        try:
            context["similar_entries"] = await search_by_text(
                db, user_message, user_id, embedding_service, limit=3
            )
            logger.info(f"Found {len(context['similar_entries'])} similar entries")
        except Exception as e:
            logger.error(f"Error fetching similar entries: {e}")

        try:
            goals = await goal_crud.get_multi(db, user_uuid, status="active")
            context["goals"] = [
                {"title": g.title, "description": g.description}
                for g in goals[:5]
            ]
            logger.info(f"Found {len(context['goals'])} goals")
        except Exception as e:
            logger.error(f"Error fetching goals: {e}")

        try:
            entries = await entry_crud.get_recent(db, user_uuid, days=7, limit=3)
            context["recent_entries"] = [
                {
                    "title": e.title,
                    "content": e.content[:1000] + "..." if len(e.content) > 1000 else e.content,
                    "mood": e.mood,
                    "date": e.created_at.strftime("%B %d"),
                }
                for e in entries
            ]
            logger.info(f"Found {len(context['recent_entries'])} recent entries")
        except Exception as e:
            logger.error(f"Error fetching recent entries: {e}")

        return context

    def build_context_message(self, context: dict, entry_context: Optional[dict] = None) -> str:
        parts = []

        if entry_context:
            entry_text = f"The user is discussing this specific journal entry:\n"
            entry_text += f"Title: {entry_context.get('title', 'Untitled')}\n"
            entry_text += f"Date: {entry_context.get('created_at', 'Unknown')}\n"
            if entry_context.get('mood'):
                entry_text += f"Mood: {entry_context['mood']}\n"
            entry_text += f"Content:\n{entry_context.get('content', '')}"
            parts.append(entry_text)

        if context["goals"]:
            goals_text = "\n".join(
                f"- {g['title']}" + (f": {g['description']}" if g.get('description') else "")
                for g in context["goals"]
            )
            parts.append(f"User's active goals:\n{goals_text}")

        if context["similar_entries"]:
            entries_text = "\n\n".join(
                f"Entry from {e.get('created_at', 'unknown date')[:10]}:\n{e['content']}"
                for e in context["similar_entries"]
            )
            parts.append(f"Related past journal entries:\n{entries_text}")

        if context["recent_entries"]:
            recent_text = "\n\n".join(
                f"Entry from {e['date']} (mood: {e.get('mood', 'not specified')}):\n{e['content']}"
                for e in context["recent_entries"]
            )
            parts.append(f"Recent journal entries:\n{recent_text}")

        if parts:
            return "Here's some context about this user:\n\n" + "\n\n".join(parts)
        return ""

    def _build_messages(self, context_message: str, chat_history: list, user_message: str) -> list:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        if context_message:
            messages.append({"role": "system", "content": context_message})

        for msg in chat_history[-10:]:
            messages.append({"role": msg["role"], "content": msg["content"]})

        messages.append({"role": "user", "content": user_message})
        return messages

    async def chat(
        self,
        db,
        user_id: str,
        user_message: str,
        chat_history: list,
        entry_context: Optional[dict] = None,
    ) -> str:
        context = await self.get_context(db, user_id, user_message)
        context_message = self.build_context_message(context, entry_context)
        messages = self._build_messages(context_message, chat_history, user_message)

        completion = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=1,
            max_tokens=8192,
            top_p=1,
            stream=False,
        )
        return completion.choices[0].message.content

    async def chat_stream(
        self,
        db,
        user_id: str,
        user_message: str,
        chat_history: list,
        entry_context: Optional[dict] = None,
    ) -> AsyncGenerator[str, None]:
        context = await self.get_context(db, user_id, user_message)
        context_message = self.build_context_message(context, entry_context)
        logger.info(f"Context message length: {len(context_message)}")
        messages = self._build_messages(context_message, chat_history, user_message)

        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=1,
            max_tokens=8192,
            top_p=1,
            stream=True,
        )

        async for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield content


journal_agent = JournalAgent()
