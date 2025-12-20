import asyncio
import json
import logging
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_user_from_token
from app.services.deepgram_service import DeepgramStreamManager
from app.services.cartesia_service import CartesiaStreamManager
from app.agent.graph import journal_agent

logger = logging.getLogger(__name__)
router = APIRouter()


class VoiceChatSession:
    def __init__(self, websocket: WebSocket, user_id: str, db: AsyncSession):
        self.websocket = websocket
        self.user_id = user_id
        self.db = db
        self.deepgram = DeepgramStreamManager()
        self.cartesia = CartesiaStreamManager()
        self.chat_history: list[dict] = []
        self.is_speaking = False
        self.current_generation_task: Optional[asyncio.Task] = None
        self._cancelled = False

    async def send_message(self, msg_type: str, data: dict = None):
        await self.websocket.send_json({"type": msg_type, "data": data or {}})

    async def handle_user_audio(self, audio_data: bytes):
        if self.deepgram.is_connected:
            await self.deepgram.send_audio(audio_data)

    async def handle_user_speech_end(self, transcript: str):
        if not transcript.strip():
            return

        logger.info(f"User said: {transcript}")

        if self.is_speaking:
            await self.interrupt()

        self.chat_history.append({"role": "user", "content": transcript})

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

            async def text_generator():
                nonlocal full_response
                async for chunk in journal_agent.chat_stream(
                    self.db,
                    self.user_id,
                    user_message,
                    self.chat_history[:-1],
                ):
                    if self._cancelled:
                        return
                    full_response += chunk
                    await self.send_message("assistant_text", {"text": chunk, "is_final": False})
                    yield chunk

            await self.send_message("assistant_speaking")

            async for audio_chunk in self.cartesia.synthesize_streaming(text_generator()):
                if self._cancelled:
                    break
                await self.websocket.send_bytes(audio_chunk)

            if not self._cancelled:
                self.chat_history.append({"role": "assistant", "content": full_response})
                await self.send_message("assistant_text", {"text": "", "is_final": True})
                await self.send_message("assistant_done")

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            await self.send_message("error", {"message": str(e)})
        finally:
            self.is_speaking = False
            self.current_generation_task = None

    async def interrupt(self):
        logger.info("Interrupting current response")
        self._cancelled = True
        self.cartesia.cancel()

        if self.current_generation_task and not self.current_generation_task.done():
            self.current_generation_task.cancel()
            try:
                await self.current_generation_task
            except asyncio.CancelledError:
                pass

        self.is_speaking = False
        await self.send_message("interrupted")

    async def start_deepgram(self):
        if await self.deepgram.connect():
            asyncio.create_task(self.process_transcripts())
            return True
        return False

    async def process_transcripts(self):
        accumulated_transcript = ""
        last_final_time = asyncio.get_event_loop().time()

        while self.deepgram.is_connected:
            try:
                transcript, is_final = await asyncio.wait_for(
                    self.deepgram.get_transcript(),
                    timeout=0.1
                )

                if transcript:
                    if is_final:
                        accumulated_transcript += " " + transcript
                        accumulated_transcript = accumulated_transcript.strip()
                        last_final_time = asyncio.get_event_loop().time()

                        await self.send_message("interim_transcript", {
                            "text": accumulated_transcript,
                            "is_final": True
                        })
                    else:
                        await self.send_message("interim_transcript", {
                            "text": accumulated_transcript + " " + transcript,
                            "is_final": False
                        })

            except asyncio.TimeoutError:
                current_time = asyncio.get_event_loop().time()
                if accumulated_transcript and (current_time - last_final_time) > 1.5:
                    await self.handle_user_speech_end(accumulated_transcript)
                    accumulated_transcript = ""
            except Exception as e:
                logger.error(f"Error processing transcripts: {e}")
                break

    async def close(self):
        await self.deepgram.close()


@router.websocket("/chat")
async def voice_chat(
    websocket: WebSocket,
    token: str = None,
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

    session = VoiceChatSession(websocket, str(user.id), db)

    try:
        await session.send_message("connected", {"user_id": str(user.id)})

        if not await session.start_deepgram():
            await session.send_message("error", {"message": "Failed to connect to speech recognition"})
            await websocket.close(code=4002)
            return

        await session.send_message("ready")

        greeting = "Hey there! I'm your JournalBuddy. How are you doing today?"
        await session.send_message("assistant_text", {"text": greeting, "is_final": False})
        await session.send_message("assistant_speaking")

        async for audio_chunk in session.cartesia.synthesize_streaming(async_generator_from_string(greeting)):
            await websocket.send_bytes(audio_chunk)

        session.chat_history.append({"role": "assistant", "content": greeting})
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
        await session.send_message("error", {"message": str(e)})
    finally:
        await session.close()


async def async_generator_from_string(text: str):
    yield text
