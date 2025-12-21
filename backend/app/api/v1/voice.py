import asyncio
import json
import logging
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_user_from_token
from app.services.deepgram_service import DeepgramStreamManager
from app.services.cartesia_service import CartesiaStreamManager
from app.agent.voice_agent import voice_agent
from app.crud.chat import chat_crud

logger = logging.getLogger(__name__)
router = APIRouter()


class VoiceChatSession:
    def __init__(self, websocket: WebSocket, user_id: str, db: AsyncSession, journal_type: Optional[str] = None):
        self.websocket = websocket
        self.user_id = user_id
        self.db = db
        self.journal_type = journal_type
        self.deepgram = DeepgramStreamManager()
        self.cartesia = CartesiaStreamManager()
        self.chat_history: list[dict] = []
        self.is_speaking = False
        self.current_generation_task: Optional[asyncio.Task] = None
        self._cancelled = False
        self._last_interrupt_time: float = 0
        self._interrupt_cooldown: float = 1.0
        self.db_session_id: Optional[UUID] = None
        self.should_end_conversation = False

    async def create_db_session(self):
        session = await chat_crud.create_session(
            self.db,
            UUID(self.user_id),
            session_type="voice",
        )
        self.db_session_id = session.id
        logger.info(f"Created voice chat session: {self.db_session_id}")

    async def save_message(self, role: str, content: str):
        if self.db_session_id and content.strip():
            try:
                await chat_crud.add_message(
                    self.db,
                    self.db_session_id,
                    role,
                    content,
                )
            except Exception as e:
                logger.warning(f"Failed to save message, rolling back: {e}")
                await self.db.rollback()

    async def send_message(self, msg_type: str, data: dict = None):
        try:
            await self.websocket.send_json({"type": msg_type, "data": data or {}})
        except Exception as e:
            logger.warning(f"Failed to send WebSocket message: {e}")

    async def handle_user_audio(self, audio_data: bytes):
        if self.deepgram.is_connected:
            await self.deepgram.send_audio(audio_data)

    async def handle_user_speech_end(self, transcript: str):
        if not transcript.strip():
            return

        logger.info(f"User said: {transcript}")

        if self.is_speaking:
            await self.interrupt()
            return

        current_time = asyncio.get_event_loop().time()
        time_since_interrupt = current_time - self._last_interrupt_time
        if time_since_interrupt < self._interrupt_cooldown:
            logger.info(f"In cooldown period, waiting... ({time_since_interrupt:.1f}s since interrupt)")
            return

        self.chat_history.append({"role": "user", "content": transcript})
        await self.save_message("user", transcript)

        await self.send_message("user_transcript", {"text": transcript})
        await self.send_message("assistant_thinking")

        self.current_generation_task = asyncio.create_task(
            self.generate_response(transcript)
        )

    async def generate_response(self, user_message: str):
        try:
            self.is_speaking = True
            self._cancelled = False
            self.cartesia.reset()

            full_response = ""
            end_signal_received = False
            has_sent_text = False

            async def text_generator():
                nonlocal full_response, end_signal_received, has_sent_text
                async for chunk in voice_agent.chat_stream(
                    self.db,
                    self.user_id,
                    str(self.db_session_id) if self.db_session_id else "",
                    user_message,
                    self.chat_history[:-1],
                    journal_type=self.journal_type,
                ):
                    if self._cancelled:
                        return
                    if chunk == "\n__END_CONVERSATION__":
                        end_signal_received = True
                        self.should_end_conversation = True
                        return
                    if chunk.startswith("__TOOL_START:") and chunk.endswith("__"):
                        tool_name = chunk.replace("__TOOL_START:", "").replace("__", "")
                        await self.send_message("tool_call", {"tool": tool_name, "status": "start"})
                        continue
                    if chunk.startswith("__TOOL_DONE:") and chunk.endswith("__"):
                        tool_name = chunk.replace("__TOOL_DONE:", "").replace("__", "")
                        await self.send_message("tool_call", {"tool": tool_name, "status": "done"})
                        continue
                    if chunk.startswith("__EMOTION:") and chunk.endswith("__"):
                        emotion = chunk.replace("__EMOTION:", "").replace("__", "")
                        await self.send_message("emotion", {"emotion": emotion})
                        continue
                    if chunk and chunk.strip():
                        full_response += chunk
                        has_sent_text = True
                        logger.info(f"Sending assistant_text chunk: {chunk[:50]}...")
                        await self.send_message("assistant_text", {"text": chunk, "is_final": False})
                        yield chunk

            await self.send_message("assistant_speaking")

            async for audio_chunk in self.cartesia.synthesize_streaming(text_generator()):
                if self._cancelled:
                    break
                try:
                    await self.websocket.send_bytes(audio_chunk)
                except Exception as e:
                    logger.warning(f"Failed to send audio chunk: {e}")
                    break

            if not self._cancelled:
                logger.info(f"Response complete. full_response length: {len(full_response)}, has_sent_text: {has_sent_text}")
                if full_response.strip():
                    self.chat_history.append({"role": "assistant", "content": full_response})
                    await self.save_message("assistant", full_response)

                if has_sent_text:
                    logger.info("Sending is_final=True")
                    await self.send_message("assistant_text", {"text": "", "is_final": True})
                await self.send_message("assistant_done")

                if end_signal_received:
                    await self.send_message("conversation_ended")

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            try:
                await self.db.rollback()
            except Exception:
                pass
            await self.send_message("error", {"message": str(e)})
        finally:
            self.is_speaking = False
            self.current_generation_task = None

    async def interrupt(self):
        logger.info("Interrupting current response")
        self._cancelled = True
        self._last_interrupt_time = asyncio.get_event_loop().time()
        self.cartesia.cancel()

        if self.current_generation_task and not self.current_generation_task.done():
            self.current_generation_task.cancel()
            try:
                await self.current_generation_task
            except asyncio.CancelledError:
                pass

        try:
            await self.db.rollback()
        except Exception as e:
            logger.debug(f"Rollback during interrupt: {e}")

        self.is_speaking = False
        await self.send_message("interrupted")

    async def start_deepgram(self):
        if await self.deepgram.connect():
            asyncio.create_task(self.process_transcripts())
            return True
        return False

    async def process_transcripts(self):
        accumulated_transcript = ""
        last_speech_time = asyncio.get_event_loop().time()
        last_process_time = 0.0
        silence_threshold = 1.5
        min_process_interval = 0.5

        while self.deepgram.is_connected:
            try:
                transcript, is_final = await asyncio.wait_for(
                    self.deepgram.get_transcript(),
                    timeout=0.1
                )

                current_time = asyncio.get_event_loop().time()

                if transcript:
                    last_speech_time = current_time

                    if is_final:
                        accumulated_transcript += " " + transcript
                        accumulated_transcript = accumulated_transcript.strip()

                    await self.send_message("interim_transcript", {
                        "text": (accumulated_transcript + " " + transcript).strip() if not is_final else accumulated_transcript,
                        "is_final": False
                    })

                    if self.is_speaking:
                        await self.interrupt()

            except asyncio.TimeoutError:
                current_time = asyncio.get_event_loop().time()
                time_since_speech = current_time - last_speech_time
                time_since_interrupt = current_time - self._last_interrupt_time
                time_since_process = current_time - last_process_time

                if accumulated_transcript and time_since_speech > silence_threshold:
                    if time_since_interrupt > self._interrupt_cooldown and time_since_process > min_process_interval:
                        logger.info(f"Silence detected, processing: {accumulated_transcript[:50]}...")
                        await self.handle_user_speech_end(accumulated_transcript)
                        accumulated_transcript = ""
                        last_process_time = current_time

            except Exception as e:
                logger.error(f"Error processing transcripts: {e}")
                break

    async def save_session_summary_on_close(self):
        if not self.db_session_id or len(self.chat_history) < 2:
            return

        try:
            from app.models.chat import ChatSession
            from app.models.entry import Entry
            from app.services.embedding import embedding_service
            from sqlalchemy import select

            session = await self.db.get(ChatSession, self.db_session_id)
            if session and session.entry_id:
                logger.info(f"Entry already exists for session {self.db_session_id}, skipping auto-save")
                return

            conversation_text = "\n".join(
                f"{msg['role'].upper()}: {msg['content']}"
                for msg in self.chat_history
            )

            from langchain_groq import ChatGroq
            from app.config import settings

            llm = ChatGroq(
                api_key=settings.groq_api_key,
                model=settings.groq_model,
                temperature=0.3,
                max_tokens=500,
            )

            prompt = f"""Analyze this voice conversation and create a journal entry summary.

Conversation:
{conversation_text}

Provide your response in this exact format:
TITLE: [A meaningful 3-8 word title capturing what was discussed]
CONTENT: [2-3 paragraphs flowing summary of what the user shared, written in third person as a journal entry]
MOOD: [One of: great, good, okay, bad, terrible - based on user's overall sentiment]
TOPICS: [comma-separated key topics, max 5]"""

            response = await llm.ainvoke(prompt)
            content = response.content

            title = "Voice Conversation"
            entry_content = ""
            mood = "okay"
            topics = ""

            current_field = None
            for line in content.split("\n"):
                line = line.strip()
                if line.startswith("TITLE:"):
                    title = line.replace("TITLE:", "").strip()
                    current_field = None
                elif line.startswith("CONTENT:"):
                    entry_content = line.replace("CONTENT:", "").strip()
                    current_field = "content"
                elif line.startswith("MOOD:"):
                    mood = line.replace("MOOD:", "").strip().lower()
                    current_field = None
                elif line.startswith("TOPICS:"):
                    topics = line.replace("TOPICS:", "").strip()
                    current_field = None
                elif current_field == "content" and line:
                    entry_content += " " + line

            valid_moods = ["great", "good", "okay", "bad", "terrible"]
            if mood not in valid_moods:
                mood = "okay"

            if entry_content:
                transcript_lines = []
                for msg in self.chat_history:
                    role = "You" if msg["role"] == "user" else "JournalBuddy"
                    transcript_lines.append(f"{role}: {msg['content']}")
                transcript = "\n\n".join(transcript_lines)

                entry = Entry(
                    user_id=self.user_id,
                    title=title,
                    content=entry_content,
                    transcript=transcript,
                    mood=mood,
                    journal_type=self.journal_type,
                )
                self.db.add(entry)
                await self.db.flush()

                if session:
                    session.entry_id = entry.id
                    session.summary = entry_content[:500]
                    session.key_topics = topics

                await self.db.commit()
                logger.info(f"Auto-created journal entry {entry.id} for session {self.db_session_id}")

                try:
                    embedding = await embedding_service.generate_embedding(entry_content)
                    entry.embedding = embedding
                    await self.db.commit()
                except Exception as emb_err:
                    logger.error(f"Failed to generate embedding: {emb_err}")

        except Exception as e:
            logger.error(f"Failed to auto-save session summary: {e}")
            try:
                await self.db.rollback()
            except Exception:
                pass

    async def close(self):
        await self.save_session_summary_on_close()
        await self.deepgram.close()


@router.websocket("/chat")
async def voice_chat(
    websocket: WebSocket,
    token: str = None,
    journal_type: str = None,
    db: AsyncSession = Depends(get_db),
):
    await websocket.accept()

    user = None
    if token:
        user = await get_user_from_token(token, db)

    if not user:
        await websocket.send_json({"type": "error", "data": {"message": "Authentication required"}})
        await websocket.close(code=4001)
        return

    session = VoiceChatSession(websocket, str(user.id), db, journal_type=journal_type)

    try:
        await session.create_db_session()
        await session.send_message("connected", {"user_id": str(user.id)})

        if not await session.start_deepgram():
            await session.send_message("error", {"message": "Failed to connect to speech recognition"})
            await websocket.close(code=4002)
            return

        await session.send_message("ready")

        if journal_type == "morning":
            greeting = "Good morning! Let's start your day with some reflection. How are you feeling this morning?"
        elif journal_type == "evening":
            greeting = "Good evening! Let's reflect on your day. How did things go today?"
        else:
            greeting = "Hey there! How are you doing today?"
        await session.send_message("assistant_text", {"text": greeting, "is_final": False})
        await session.send_message("assistant_speaking")

        async for audio_chunk in session.cartesia.synthesize_streaming(async_generator_from_string(greeting)):
            try:
                await websocket.send_bytes(audio_chunk)
            except Exception as e:
                logger.warning(f"Failed to send greeting audio: {e}")
                break

        session.chat_history.append({"role": "assistant", "content": greeting})
        await session.save_message("assistant", greeting)
        await session.send_message("assistant_text", {"text": "", "is_final": True})
        await session.send_message("assistant_done")

        while True:
            message = await websocket.receive()

            if "bytes" in message:
                await session.handle_user_audio(message["bytes"])

            elif "text" in message:
                data = json.loads(message["text"])
                msg_type = data.get("type")

                if msg_type == "interrupt":
                    await session.interrupt()
                elif msg_type == "speech_end":
                    transcript = data.get("transcript", "")
                    if transcript:
                        await session.handle_user_speech_end(transcript)
                elif msg_type == "ping":
                    await session.send_message("pong")

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for user {user.id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await session.send_message("error", {"message": str(e)})
        except Exception:
            pass
    finally:
        await session.close()


async def async_generator_from_string(text: str):
    yield text
