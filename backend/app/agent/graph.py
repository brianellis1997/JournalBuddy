from typing import AsyncGenerator, Optional
from groq import AsyncGroq
import logging

from app.config import settings
from app.services.embedding import embedding_service
from app.services.vector_search import search_by_text
from app.services.token_manager import token_manager
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

VOICE_SYSTEM_PROMPT = """You are JournalBuddy, a warm and friendly AI companion having a natural voice conversation.

CRITICAL: Keep responses SHORT - 1-2 sentences max. This is voice chat, not text.

YOUR PRIMARY JOB: Help the user check in on their goals and reflect on their day.

CONVERSATION STRUCTURE:
1. First, check in on how they're feeling today
2. Then, go through their goals one by one - ask what progress they made today
3. If they want to talk about something else, that's fine - be supportive
4. Once you've covered their goals (or they don't want to), ask if there's anything else
5. If nothing else, offer a brief encouraging sign-off

ADAPTIVE BEHAVIOR:
- If user wants to vent or talk about feelings → listen supportively, ask one follow-up
- If user wants to discuss goals → help them reflect on progress
- If user seems done → wrap up naturally: "Sounds good! Anything else on your mind, or should we wrap up?"
- If user says they're done → "Great chat! Have a good one." (keep it brief)

RULES:
- ONE question max per response
- No bullet points, lists, or markdown
- Don't repeat what they just said back to them
- Be warm but efficient - respect their time
- When goals are provided, reference them specifically by name

Example good responses:
- "Nice! How'd that go with your goal of exercising more?"
- "That's tough. What do you think you could try tomorrow?"
- "Got it. Anything else you want to talk about, or should we wrap up?"
- "Great progress today! Talk soon."

Remember: Goal-focused, concise, natural. Help them reflect, then wrap up."""


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
                    "content": e.content,
                    "mood": e.mood,
                    "date": e.created_at.strftime("%B %d"),
                }
                for e in entries
            ]
            logger.info(f"Found {len(context['recent_entries'])} recent entries")
        except Exception as e:
            logger.error(f"Error fetching recent entries: {e}")

        return context

    def build_context_message(
        self,
        context: dict,
        entry_context: Optional[dict] = None,
        chat_history_tokens: int = 0,
        user_message_tokens: int = 0,
    ) -> str:
        system_tokens = token_manager.count_tokens(SYSTEM_PROMPT)
        budget = token_manager.allocate_context_budget(
            system_prompt_tokens=system_tokens,
            chat_history_tokens=chat_history_tokens,
            user_message_tokens=user_message_tokens,
        )

        parts = []

        if entry_context:
            content = entry_context.get('content', '')
            if token_manager.count_tokens(content) > budget["entry_context"]:
                content = token_manager.truncate_to_tokens(
                    content,
                    budget["entry_context"],
                    suffix="\n[Entry truncated...]"
                )

            entry_text = f"The user is discussing this specific journal entry:\n"
            entry_text += f"Title: {entry_context.get('title', 'Untitled')}\n"
            entry_text += f"Date: {entry_context.get('created_at', 'Unknown')}\n"
            if entry_context.get('mood'):
                entry_text += f"Mood: {entry_context['mood']}\n"
            entry_text += f"Content:\n{content}"
            parts.append(entry_text)

        if context["goals"]:
            goals_text = "\n".join(
                f"- {g['title']}" + (f": {g['description']}" if g.get('description') else "")
                for g in context["goals"]
            )
            truncated_goals = token_manager.truncate_to_tokens(
                goals_text, budget["goals"], suffix="\n[More goals...]"
            )
            parts.append(f"User's active goals:\n{truncated_goals}")

        if context["similar_entries"]:
            truncated_similar = token_manager.truncate_entries(
                context["similar_entries"],
                budget["similar_entries"],
                content_key="content",
            )
            if truncated_similar:
                entries_text = "\n\n".join(
                    f"Entry from {e.get('created_at', 'unknown date')[:10]}:\n{e['content']}"
                    for e in truncated_similar
                )
                parts.append(f"Related past journal entries:\n{entries_text}")

        if context["recent_entries"]:
            truncated_recent = token_manager.truncate_entries(
                context["recent_entries"],
                budget["recent_entries"],
                content_key="content",
            )
            if truncated_recent:
                recent_text = "\n\n".join(
                    f"Entry from {e['date']} (mood: {e.get('mood', 'not specified')}):\n{e['content']}"
                    for e in truncated_recent
                )
                parts.append(f"Recent journal entries:\n{recent_text}")

        if parts:
            context_msg = "Here's some context about this user:\n\n" + "\n\n".join(parts)
            logger.info(f"Built context message: {token_manager.count_tokens(context_msg)} tokens")
            return context_msg
        return ""

    def _build_messages(
        self,
        context_message: str,
        chat_history: list,
        user_message: str,
        max_history_tokens: int = 16000,
    ) -> list:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        if context_message:
            messages.append({"role": "system", "content": context_message})

        if chat_history:
            truncated_history = self._truncate_chat_history(chat_history, max_history_tokens)
            for msg in truncated_history:
                messages.append({"role": msg["role"], "content": msg["content"]})

        messages.append({"role": "user", "content": user_message})

        total_tokens = token_manager.count_messages_tokens(messages)
        logger.info(f"Total message tokens: {total_tokens}")

        return messages

    def _truncate_chat_history(self, chat_history: list, max_tokens: int) -> list:
        if not chat_history:
            return []

        total_tokens = 0
        result = []

        for msg in reversed(chat_history):
            msg_tokens = token_manager.count_tokens(msg.get("content", "")) + 4
            if total_tokens + msg_tokens > max_tokens:
                break
            result.insert(0, msg)
            total_tokens += msg_tokens

        if len(result) < len(chat_history):
            logger.info(f"Truncated chat history from {len(chat_history)} to {len(result)} messages ({total_tokens} tokens)")

        return result

    async def chat(
        self,
        db,
        user_id: str,
        user_message: str,
        chat_history: list,
        entry_context: Optional[dict] = None,
    ) -> str:
        context = await self.get_context(db, user_id, user_message)

        chat_history_tokens = sum(
            token_manager.count_tokens(msg.get("content", "")) + 4
            for msg in chat_history
        )
        user_message_tokens = token_manager.count_tokens(user_message)

        context_message = self.build_context_message(
            context,
            entry_context,
            chat_history_tokens=chat_history_tokens,
            user_message_tokens=user_message_tokens,
        )
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

        chat_history_tokens = sum(
            token_manager.count_tokens(msg.get("content", "")) + 4
            for msg in chat_history
        )
        user_message_tokens = token_manager.count_tokens(user_message)

        context_message = self.build_context_message(
            context,
            entry_context,
            chat_history_tokens=chat_history_tokens,
            user_message_tokens=user_message_tokens,
        )
        logger.info(f"Context message: {token_manager.count_tokens(context_message)} tokens")
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

    async def voice_chat_stream(
        self,
        db,
        user_id: str,
        user_message: str,
        chat_history: list,
    ) -> AsyncGenerator[str, None]:
        context = await self.get_context(db, user_id, user_message)

        chat_history_tokens = sum(
            token_manager.count_tokens(msg.get("content", "")) + 4
            for msg in chat_history
        )
        user_message_tokens = token_manager.count_tokens(user_message)

        context_message = self.build_context_message(
            context,
            None,
            chat_history_tokens=chat_history_tokens,
            user_message_tokens=user_message_tokens,
        )

        messages = [{"role": "system", "content": VOICE_SYSTEM_PROMPT}]
        if context_message:
            messages.append({"role": "system", "content": context_message})

        if chat_history:
            truncated_history = self._truncate_chat_history(chat_history, 4000)
            for msg in truncated_history:
                messages.append({"role": msg["role"], "content": msg["content"]})

        messages.append({"role": "user", "content": user_message})

        logger.info(f"Voice chat - Total tokens: {token_manager.count_messages_tokens(messages)}")

        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.8,
            max_tokens=150,
            top_p=1,
            stream=True,
        )

        async for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield content


journal_agent = JournalAgent()
