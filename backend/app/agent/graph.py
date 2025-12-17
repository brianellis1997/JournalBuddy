from typing import AsyncGenerator
from groq import AsyncGroq

from app.config import settings
from app.services.embedding import embedding_service
from app.services.vector_search import search_by_text
from app.crud.goal import goal_crud
from app.crud.entry import entry_crud

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
        context = {
            "similar_entries": [],
            "goals": [],
            "recent_entries": [],
        }

        try:
            context["similar_entries"] = await search_by_text(
                db, user_message, user_id, embedding_service, limit=3
            )
        except Exception:
            pass

        try:
            goals = await goal_crud.get_multi(db, user_id, status="active")
            context["goals"] = [
                {"title": g.title, "description": g.description}
                for g in goals[:5]
            ]
        except Exception:
            pass

        try:
            entries = await entry_crud.get_recent(db, user_id, days=7, limit=3)
            context["recent_entries"] = [
                {
                    "title": e.title,
                    "content": e.content[:150] + "..." if len(e.content) > 150 else e.content,
                    "mood": e.mood,
                    "date": e.created_at.strftime("%B %d"),
                }
                for e in entries
            ]
        except Exception:
            pass

        return context

    def build_context_message(self, context: dict) -> str:
        parts = []

        if context["goals"]:
            goals_text = "\n".join(
                f"- {g['title']}" + (f": {g['description']}" if g.get('description') else "")
                for g in context["goals"]
            )
            parts.append(f"User's active goals:\n{goals_text}")

        if context["similar_entries"]:
            entries_text = "\n".join(
                f"- On {e.get('created_at', 'unknown date')[:10]}: \"{e['content'][:100]}...\""
                for e in context["similar_entries"]
            )
            parts.append(f"Related past journal entries:\n{entries_text}")

        if context["recent_entries"]:
            recent_text = "\n".join(
                f"- {e['date']}: \"{e['content'][:80]}...\" (mood: {e.get('mood', 'not specified')})"
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
    ) -> str:
        context = await self.get_context(db, user_id, user_message)
        context_message = self.build_context_message(context)
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
    ) -> AsyncGenerator[str, None]:
        context = await self.get_context(db, user_id, user_message)
        context_message = self.build_context_message(context)
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
