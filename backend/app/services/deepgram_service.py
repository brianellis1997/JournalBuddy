import asyncio
import json
import logging
from typing import Optional
import websockets

from app.config import settings

logger = logging.getLogger(__name__)

DEEPGRAM_WS_URL = "wss://api.deepgram.com/v1/listen"


class DeepgramStreamManager:
    def __init__(self):
        self.api_key = settings.deepgram_api_key
        self.websocket = None
        self.transcript_queue: asyncio.Queue[tuple[str, bool]] = asyncio.Queue()
        self._connected = False
        self._receive_task = None

    async def connect(self) -> bool:
        if not self.api_key:
            raise ValueError("Deepgram API key not configured")

        try:
            params = (
                "?model=nova-2"
                "&language=en-US"
                "&encoding=linear16"
                "&sample_rate=48000"
                "&channels=1"
                "&smart_format=true"
                "&interim_results=true"
                "&utterance_end_ms=1000"
                "&vad_events=true"
                "&endpointing=300"
            )

            self.websocket = await websockets.connect(
                f"{DEEPGRAM_WS_URL}{params}",
                additional_headers={"Authorization": f"Token {self.api_key}"},
            )
            self._connected = True
            logger.info("Connected to Deepgram")

            self._receive_task = asyncio.create_task(self._receive_messages())
            return True

        except Exception as e:
            logger.error(f"Failed to connect to Deepgram: {e}")
            return False

    async def _receive_messages(self):
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)

                    if data.get("type") == "Results":
                        channel = data.get("channel", {})
                        alternatives = channel.get("alternatives", [])
                        if alternatives:
                            transcript = alternatives[0].get("transcript", "")
                            is_final = data.get("is_final", False)
                            if transcript:
                                await self.transcript_queue.put((transcript, is_final))

                    elif data.get("type") == "UtteranceEnd":
                        pass

                except json.JSONDecodeError:
                    logger.error("Failed to parse Deepgram message")
                except Exception as e:
                    logger.error(f"Error processing Deepgram message: {e}")

        except websockets.exceptions.ConnectionClosed:
            logger.info("Deepgram connection closed")
        except Exception as e:
            logger.error(f"Deepgram receive error: {e}")
        finally:
            self._connected = False

    async def send_audio(self, audio_chunk: bytes) -> None:
        if self.websocket and self._connected:
            try:
                await self.websocket.send(audio_chunk)
            except Exception as e:
                logger.error(f"Error sending audio to Deepgram: {e}")

    async def get_transcript(self) -> tuple[str, bool]:
        return await self.transcript_queue.get()

    async def close(self) -> None:
        self._connected = False
        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass

        if self.websocket:
            await self.websocket.close()
            logger.info("Deepgram connection closed")

    @property
    def is_connected(self) -> bool:
        return self._connected
