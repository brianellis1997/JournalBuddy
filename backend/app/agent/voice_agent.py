import json
import logging
from typing import Annotated, TypedDict, Literal, AsyncGenerator, List, Dict
from uuid import UUID

import tiktoken
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage, BaseMessage
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

MAX_CONTEXT_TOKENS = 64000
RESPONSE_RESERVE_TOKENS = 1000


class ConversationMemory:
    def __init__(self, max_tokens: int = MAX_CONTEXT_TOKENS):
        self.max_tokens = max_tokens
        try:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
        except Exception:
            self.tokenizer = tiktoken.get_encoding("gpt2")

    def count_tokens(self, text: str) -> int:
        if not text:
            return 0
        return len(self.tokenizer.encode(text))

    def count_message_tokens(self, message: BaseMessage) -> int:
        content = message.content if isinstance(message.content, str) else str(message.content)
        tokens = self.count_tokens(content) + 4
        if hasattr(message, 'tool_calls') and message.tool_calls:
            tokens += 50
        return tokens

    def trim_messages_to_fit(
        self,
        system_messages: List[BaseMessage],
        chat_history: List[Dict],
        current_message: str,
        reserve_tokens: int = RESPONSE_RESERVE_TOKENS
    ) -> List[BaseMessage]:
        available_tokens = self.max_tokens - reserve_tokens

        system_tokens = sum(self.count_message_tokens(m) for m in system_messages)
        current_msg_tokens = self.count_tokens(current_message) + 4

        remaining_tokens = available_tokens - system_tokens - current_msg_tokens

        if remaining_tokens <= 0:
            logger.warning(f"System prompt too large: {system_tokens} tokens, available: {available_tokens}")
            return system_messages + [HumanMessage(content=current_message)]

        history_messages = []
        total_history_tokens = 0

        for msg in reversed(chat_history):
            content = msg.get("content", "")
            role = msg.get("role", "user")
            msg_tokens = self.count_tokens(content) + 4

            if total_history_tokens + msg_tokens > remaining_tokens:
                break

            if role == "user":
                history_messages.insert(0, HumanMessage(content=content))
            else:
                history_messages.insert(0, AIMessage(content=content))

            total_history_tokens += msg_tokens

        logger.info(f"Token-based memory: {len(chat_history)} msgs -> {len(history_messages)} kept. "
                   f"Tokens: system={system_tokens}, history={total_history_tokens}, "
                   f"current={current_msg_tokens}, total={system_tokens + total_history_tokens + current_msg_tokens}/{available_tokens}")

        return system_messages + history_messages + [HumanMessage(content=current_message)]


conversation_memory = ConversationMemory()

VOICE_SYSTEM_PROMPT = """You are JournalBuddy, a warm and friendly AI companion having a natural voice conversation.

CRITICAL: Keep responses SHORT - 1-2 sentences max. This is voice chat, not text.

YOUR PRIMARY JOB: Help the user reflect on their day and create a journal entry.

CONVERSATION STRUCTURE:
1. First, check in on how they're feeling today
2. If they have goals, ask about progress on each one
3. Ask about anything else on their mind - be supportive
4. When they're done, use create_journal_entry to save the conversation as a journal entry
5. After creating the entry, use end_conversation to say goodbye

MOOD DETECTION:
Based on what the user says, detect their mood:
- "great" - Very positive, excited, happy
- "good" - Positive, content, satisfied
- "okay" - Neutral, neither good nor bad
- "bad" - Negative, frustrated, sad
- "terrible" - Very negative, awful day

AVAILABLE TOOLS:
- update_goal_progress: When user reports progress on a goal, update it (0-100%)
- recall_memory: Search past journal entries when user mentions something from before
- create_journal_entry: ALWAYS use this when conversation is ending to save as journal entry
- end_conversation: After creating the entry, use this to sign off

RULES:
- ONE question max per response
- No bullet points, lists, or markdown
- Be warm but efficient - respect their time
- When goals are provided, reference them specifically by name
- ALWAYS create a journal entry before ending - this is essential!

Remember: Help them reflect, save their thoughts as a journal entry, then wrap up."""

JOURNAL_SYSTEM_PROMPT = """You are JournalBuddy, a warm and friendly AI companion helping the user with their {journal_type} journal.

CRITICAL: Keep responses SHORT - 1-2 sentences max. This is voice chat, not text.

YOUR PRIMARY JOB: Help the user reflect and create a meaningful journal entry.

CONVERSATION STRUCTURE:
1. Ask how they're feeling (this will become their mood)
2. Ask about their thoughts, experiences, or intentions
3. Listen actively and ask follow-up questions
4. When they seem done (say "no", "nothing", "that's it", etc.), use create_journal_entry to save their reflection
5. After creating the entry, use end_conversation to say goodbye

MEMORY IS CRITICAL:
- You MUST remember everything the user has shared in this conversation
- Reference specific details they mentioned (names, events, feelings)
- If they ask "do you remember?", summarize what they've told you
- Never ask them to repeat what they already said

HANDLING SHORT RESPONSES:
- If user says "no", "nothing", "nope", "that's all" - they're done, save the entry
- If user says "yes", "yeah", "uh huh" - acknowledge and continue the conversation
- If unsure what they mean, briefly acknowledge and ask a clarifying question

MOOD DETECTION:
Based on what the user says, detect their mood:
- "great" - Very positive, excited, happy
- "good" - Positive, content, satisfied
- "okay" - Neutral, neither good nor bad
- "bad" - Negative, frustrated, sad
- "terrible" - Very negative, awful day

AVAILABLE TOOLS:
- recall_memory: Search past journal entries when the user mentions something from before, or to find patterns
- create_journal_entry: When ready to save, create the entry with a title, content summary, and mood
- end_conversation: After creating the entry, use this to wrap up

RULES:
- ONE question max per response
- No bullet points, lists, or markdown
- Be warm and encouraging
- Generate a meaningful title that captures the essence of their reflection
- The content should be a flowing summary of what they shared
- ALWAYS respond - never return an empty response

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

    async def recall_memory(self, query: str) -> str:
        try:
            similar_entries = await search_by_text(
                self.db, query, str(self.user_id), embedding_service, limit=3
            )
            if not similar_entries:
                return "No relevant past entries found."

            results = []
            for entry in similar_entries:
                date = entry.get('created_at', '')[:10] if entry.get('created_at') else 'Unknown date'
                title = entry.get('title', 'Untitled')
                content = entry.get('content', '')[:200]
                mood = entry.get('mood', '')
                results.append(f"[{date}] {title} (mood: {mood}): {content}...")

            logger.info(f"Recall memory found {len(similar_entries)} entries for query: {query[:50]}")
            return "Past journal entries:\n" + "\n\n".join(results)
        except Exception as e:
            logger.error(f"Error in recall_memory: {e}")
            return "Unable to search past entries."

    async def create_journal_entry(self, title: str, content: str, mood: str) -> str:
        from app.schemas.entry import EntryCreate
        from app.services.gamification import gamification_service
        from app.services.embedding import embedding_service

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

            if self.journal_type == "morning":
                await gamification_service.award_xp(self.db, self.user_id, "morning_journal", entry.id)
            elif self.journal_type == "evening":
                await gamification_service.award_xp(self.db, self.user_id, "evening_journal", entry.id)
            else:
                await gamification_service.award_xp(self.db, self.user_id, "entry_created", entry.id)

            await gamification_service.check_achievements(self.db, self.user_id)
            logger.info(f"Awarded XP for voice journal entry: {entry.id}")

            try:
                embedding = await embedding_service.generate_embedding(content)
                entry.embedding = embedding
                await self.db.commit()
                logger.info(f"Generated embedding for voice journal entry: {entry.id}")
            except Exception as embed_err:
                logger.error(f"Failed to generate embedding: {embed_err}")

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

        @tool
        async def recall_memory(query: str) -> str:
            """Search the user's past journal entries for relevant context. Use this when:
            - The user mentions something from the past
            - You want to reference their previous experiences
            - They ask about patterns or recurring themes
            - You want to provide personalized insights

            Args:
                query: What to search for in past entries (e.g., "feeling anxious", "dad", "work stress")
            """
            return await tool_handler.recall_memory(query)

        # All voice conversations should be able to create journal entries
        # Journal sessions get a focused set, regular sessions get all tools
        if is_journal:
            return [create_journal_entry, recall_memory, end_conversation]
        return [update_goal_progress, create_journal_entry, recall_memory, end_conversation]

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

        system_messages = [SystemMessage(content=system_prompt)]
        if context and not is_journal:
            system_messages.append(SystemMessage(content=f"Context about this user:\n{context}"))

        messages = conversation_memory.trim_messages_to_fit(
            system_messages=system_messages,
            chat_history=chat_history,
            current_message=user_message
        )

        max_iterations = 5
        for iteration in range(max_iterations):
            try:
                logger.info(f"Sending to LLM (iteration {iteration}), message count: {len(messages)}")
                response = await llm_with_tools.ainvoke(messages)
                logger.info(f"LLM response: content_len={len(response.content) if response.content else 0}, tool_calls={len(response.tool_calls) if response.tool_calls else 0}")
            except Exception as e:
                logger.error(f"LLM error on iteration {iteration}: {e}", exc_info=True)
                if iteration < max_iterations - 1:
                    continue
                yield "I'm here listening. Could you tell me more?"
                return

            if not response.tool_calls:
                if response.content and response.content.strip():
                    yield response.content
                else:
                    logger.warning(f"LLM returned empty response on iteration {iteration}, user_message was: {user_message[:50]}")
                    if iteration == 0:
                        if is_journal:
                            yield "I hear you. Would you like to add anything else, or should I save this as your journal entry?"
                        else:
                            yield "I'm with you. Is there anything else on your mind?"
                return

            end_conversation_called = False
            farewell_message = ""

            for tool_call in response.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]

                logger.info(f"Tool call: {tool_name} with args: {tool_args}")

                yield f"__TOOL_START:{tool_name}__"

                if tool_name == "update_goal_progress":
                    result = await tool_handler.update_goal_progress(**tool_args)
                elif tool_name == "save_session_summary":
                    result = await tool_handler.save_session_summary(**tool_args)
                elif tool_name == "create_journal_entry":
                    result = await tool_handler.create_journal_entry(**tool_args)
                elif tool_name == "recall_memory":
                    result = await tool_handler.recall_memory(**tool_args)
                elif tool_name == "end_conversation":
                    result = await tool_handler.end_conversation(**tool_args)
                    if result.startswith("END_CONVERSATION:"):
                        end_conversation_called = True
                        farewell_message = result.replace("END_CONVERSATION:", "")
                        result = "Conversation ended"
                else:
                    result = "Unknown tool"

                yield f"__TOOL_DONE:{tool_name}__"

                messages.append(AIMessage(content=response.content or "", tool_calls=[tool_call]))
                messages.append(ToolMessage(content=result, tool_call_id=tool_call["id"]))

            if end_conversation_called:
                yield farewell_message
                yield "\n__END_CONVERSATION__"
                return

        logger.warning("Max iterations reached without response")
        yield "I'm having a bit of trouble. Could you repeat that?"


voice_agent = VoiceAgent()
