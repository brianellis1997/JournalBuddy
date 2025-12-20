import json
import logging
from typing import Annotated, TypedDict, Literal, AsyncGenerator
from uuid import UUID

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.crud.goal import goal_crud
from app.crud.chat import chat_crud
from app.crud.entry import entry_crud
from app.models.goal import GoalProgressUpdate
from app.services.embedding import embedding_service
from app.services.vector_search import search_by_text

logger = logging.getLogger(__name__)

VOICE_SYSTEM_PROMPT = """You are JournalBuddy, a warm and friendly AI companion having a natural voice conversation.

CRITICAL: Keep responses SHORT - 1-2 sentences max. This is voice chat, not text.

YOUR PRIMARY JOB: Help the user check in on their goals and reflect on their day.

CONVERSATION STRUCTURE:
1. First, check in on how they're feeling today
2. Then, go through their goals one by one - ask what progress they made today
3. If they want to talk about something else, that's fine - be supportive
4. Once you've covered their goals (or they don't want to), ask if there's anything else
5. If nothing else, use the end_conversation tool to wrap up

AVAILABLE TOOLS:
- update_goal_progress: When user reports progress on a goal, update it (0-100%)
- save_session_summary: At the end, summarize what you discussed
- end_conversation: When conversation is complete, use this to sign off

RULES:
- ONE question max per response
- No bullet points, lists, or markdown
- Be warm but efficient - respect their time
- When goals are provided, reference them specifically by name
- Use tools when appropriate - don't just talk about using them

Remember: Goal-focused, concise, natural. Help them reflect, then wrap up."""

JOURNAL_SYSTEM_PROMPT = """You are JournalBuddy, a warm and friendly AI companion helping the user with their {journal_type} journal.

CRITICAL: Keep responses SHORT - 1-2 sentences max. This is voice chat, not text.

YOUR PRIMARY JOB: Help the user reflect and create a meaningful journal entry.

CONVERSATION STRUCTURE:
1. Ask how they're feeling (this will become their mood)
2. Ask about their thoughts, experiences, or intentions
3. Listen actively and ask follow-up questions
4. When they're done, use create_journal_entry to save their reflection

MOOD DETECTION:
Based on what the user says, detect their mood:
- "great" - Very positive, excited, happy
- "good" - Positive, content, satisfied
- "okay" - Neutral, neither good nor bad
- "bad" - Negative, frustrated, sad
- "terrible" - Very negative, awful day

AVAILABLE TOOLS:
- create_journal_entry: When ready to save, create the entry with a title, content summary, and mood
- end_conversation: After creating the entry, use this to wrap up

RULES:
- ONE question max per response
- No bullet points, lists, or markdown
- Be warm and encouraging
- Generate a meaningful title that captures the essence of their reflection
- The content should be a flowing summary of what they shared

Remember: Help them reflect meaningfully, then save their entry."""


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    user_id: str
    session_id: str
    goals: list
    context: str
    should_end: bool
    summary_saved: bool


class VoiceAgentTools:
    def __init__(self, db: AsyncSession, user_id: str, session_id: str, journal_type: str = None):
        self.db = db
        self.user_id = UUID(user_id)
        self.session_id = UUID(session_id) if session_id else None
        self.journal_type = journal_type
        self._goals_cache = {}

    async def load_goals(self):
        goals = await goal_crud.get_multi(self.db, self.user_id, status="active")
        self._goals_cache = {str(g.id): g for g in goals}
        return [{"id": str(g.id), "title": g.title, "progress": g.progress} for g in goals]

    async def update_goal_progress(self, goal_title: str, new_progress: int, notes: str = "") -> str:
        goal = None
        for g in self._goals_cache.values():
            if goal_title.lower() in g.title.lower():
                goal = g
                break

        if not goal:
            return f"Could not find goal matching '{goal_title}'"

        if new_progress < 0 or new_progress > 100:
            return "Progress must be between 0 and 100"

        previous_progress = goal.progress
        goal.progress = new_progress

        progress_update = GoalProgressUpdate(
            goal_id=goal.id,
            session_id=self.session_id,
            previous_progress=previous_progress,
            new_progress=new_progress,
            notes=notes,
        )
        self.db.add(progress_update)
        await self.db.commit()

        logger.info(f"Updated goal '{goal.title}' progress: {previous_progress}% -> {new_progress}%")
        return f"Updated '{goal.title}' progress from {previous_progress}% to {new_progress}%"

    async def save_session_summary(self, summary: str, key_topics: str, goal_updates: str) -> str:
        if not self.session_id:
            return "No session to save"

        session = await self.db.get(
            __import__('app.models.chat', fromlist=['ChatSession']).ChatSession,
            self.session_id
        )
        if session:
            session.summary = summary
            session.key_topics = key_topics
            session.goal_updates = goal_updates
            await self.db.commit()
            logger.info(f"Saved session summary for {self.session_id}")
            return "Session summary saved"
        return "Session not found"

    async def end_conversation(self, farewell_message: str) -> str:
        return f"END_CONVERSATION:{farewell_message}"

    async def create_journal_entry(self, title: str, content: str, mood: str) -> str:
        from app.schemas.entry import EntryCreate

        valid_moods = ["great", "good", "okay", "bad", "terrible"]
        if mood.lower() not in valid_moods:
            mood = "okay"

        entry_data = EntryCreate(
            title=title,
            content=content,
            mood=mood.lower(),
            journal_type=self.journal_type,
        )

        try:
            entry = await entry_crud.create(self.db, entry_data, self.user_id)
            logger.info(f"Created journal entry: {entry.id} with title '{title}'")
            return f"Journal entry created: '{title}'"
        except Exception as e:
            logger.error(f"Failed to create journal entry: {e}")
            return f"Failed to create journal entry: {e}"


class VoiceAgent:
    def __init__(self):
        self.llm = ChatGroq(
            api_key=settings.groq_api_key,
            model=settings.groq_model,
            temperature=0.8,
            max_tokens=200,
        )

    async def get_context(self, db: AsyncSession, user_id: str, user_message: str) -> tuple[list, str]:
        user_uuid = UUID(user_id)

        goals = await goal_crud.get_multi(db, user_uuid, status="active")
        goals_list = [{"id": str(g.id), "title": g.title, "progress": g.progress, "description": g.description} for g in goals[:5]]

        context_parts = []
        if goals_list:
            goals_text = "\n".join(f"- {g['title']} ({g['progress']}% complete)" for g in goals_list)
            context_parts.append(f"User's active goals:\n{goals_text}")

        try:
            similar_entries = await search_by_text(db, user_message, user_id, embedding_service, limit=2)
            if similar_entries:
                entries_text = "\n".join(f"- {e.get('created_at', '')[:10]}: {e.get('content', '')[:100]}..." for e in similar_entries)
                context_parts.append(f"Related past entries:\n{entries_text}")
        except Exception as e:
            logger.error(f"Error fetching similar entries: {e}")

        return goals_list, "\n\n".join(context_parts)

    def _create_tools(self, tool_handler: VoiceAgentTools, is_journal: bool = False):
        @tool
        async def update_goal_progress(goal_title: str, new_progress: int, notes: str = "") -> str:
            """Update the progress percentage for a user's goal.

            Args:
                goal_title: The name/title of the goal to update
                new_progress: New progress percentage (0-100)
                notes: Optional notes about the progress
            """
            return await tool_handler.update_goal_progress(goal_title, new_progress, notes)

        @tool
        async def save_session_summary(summary: str, key_topics: str, goal_updates: str) -> str:
            """Save a summary of this conversation for future reference.

            Args:
                summary: Brief summary of what was discussed
                key_topics: Main topics covered (comma-separated)
                goal_updates: Any goal progress updates made (comma-separated)
            """
            return await tool_handler.save_session_summary(summary, key_topics, goal_updates)

        @tool
        async def end_conversation(farewell_message: str) -> str:
            """End the conversation with a farewell message. Use this when the user is done talking.

            Args:
                farewell_message: A brief, warm goodbye message
            """
            return await tool_handler.end_conversation(farewell_message)

        @tool
        async def create_journal_entry(title: str, content: str, mood: str) -> str:
            """Create a journal entry from the conversation.

            Args:
                title: A meaningful title that captures the essence of their reflection (3-8 words)
                content: A flowing summary of what the user shared during the conversation
                mood: The user's mood - must be one of: great, good, okay, bad, terrible
            """
            return await tool_handler.create_journal_entry(title, content, mood)

        if is_journal:
            return [create_journal_entry, end_conversation]
        return [update_goal_progress, save_session_summary, end_conversation]

    async def chat_stream(
        self,
        db: AsyncSession,
        user_id: str,
        session_id: str,
        user_message: str,
        chat_history: list,
        journal_type: str = None,
    ) -> AsyncGenerator[str, None]:
        is_journal = journal_type in ["morning", "evening"]
        tool_handler = VoiceAgentTools(db, user_id, session_id, journal_type=journal_type)
        await tool_handler.load_goals()

        goals, context = await self.get_context(db, user_id, user_message)
        tools = self._create_tools(tool_handler, is_journal=is_journal)
        llm_with_tools = self.llm.bind_tools(tools, tool_choice="auto")

        if is_journal:
            system_prompt = JOURNAL_SYSTEM_PROMPT.format(journal_type=journal_type)
        else:
            system_prompt = VOICE_SYSTEM_PROMPT

        messages = [SystemMessage(content=system_prompt)]
        if context and not is_journal:
            messages.append(SystemMessage(content=f"Context about this user:\n{context}"))

        for msg in chat_history[-10:]:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            else:
                messages.append(AIMessage(content=msg["content"]))

        messages.append(HumanMessage(content=user_message))

        max_iterations = 3
        for _ in range(max_iterations):
            try:
                response = await llm_with_tools.ainvoke(messages)
            except Exception as e:
                logger.error(f"LLM error: {e}")
                yield "Sorry, I had trouble processing that. What were you saying?"
                return

            if not response.tool_calls:
                if response.content:
                    yield response.content
                return

            end_conversation_called = False
            farewell_message = ""

            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]

                logger.info(f"Tool call: {tool_name} with args: {tool_args}")

                if tool_name == "update_goal_progress":
                    result = await tool_handler.update_goal_progress(**tool_args)
                elif tool_name == "save_session_summary":
                    result = await tool_handler.save_session_summary(**tool_args)
                elif tool_name == "create_journal_entry":
                    result = await tool_handler.create_journal_entry(**tool_args)
                elif tool_name == "end_conversation":
                    result = await tool_handler.end_conversation(**tool_args)
                    if result.startswith("END_CONVERSATION:"):
                        end_conversation_called = True
                        farewell_message = result.replace("END_CONVERSATION:", "")
                        result = "Conversation ended"
                else:
                    result = "Unknown tool"

                messages.append(AIMessage(content="", tool_calls=[tool_call]))
                messages.append(ToolMessage(content=result, tool_call_id=tool_call["id"]))

            if end_conversation_called:
                yield farewell_message
                yield "\n__END_CONVERSATION__"
                return

        if response.content:
            yield response.content


voice_agent = VoiceAgent()
