import asyncio
import logging
from typing import AsyncGenerator
import httpx

from app.config import settings

logger = logging.getLogger(__name__)

CARTESIA_TTS_URL = "https://api.cartesia.ai/tts/bytes"
CARTESIA_VOICES_URL = "https://api.cartesia.ai/voices"


class CartesiaService:
    def __init__(self):
        self.api_key = settings.cartesia_api_key
        self.voice_id = settings.cartesia_voice_id
        self.model_id = "sonic-english"
        self.output_format = {
            "container": "raw",
            "encoding": "pcm_s16le",
            "sample_rate": 24000,
        }

    async def synthesize(self, text: str) -> bytes:
        if not self.api_key:
            raise ValueError("Cartesia API key not configured")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                CARTESIA_TTS_URL,
                headers={
                    "X-API-Key": self.api_key,
                    "Cartesia-Version": "2024-06-10",
                    "Content-Type": "application/json",
                },
                json={
                    "model_id": self.model_id,
                    "transcript": text,
                    "voice": {
                        "mode": "id",
                        "id": self.voice_id,
                    },
                    "output_format": self.output_format,
                },
                timeout=30.0,
            )
            response.raise_for_status()
            return response.content

    async def synthesize_stream(self, text: str) -> AsyncGenerator[bytes, None]:
        if not self.api_key:
            raise ValueError("Cartesia API key not configured")

        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                CARTESIA_TTS_URL,
                headers={
                    "X-API-Key": self.api_key,
                    "Cartesia-Version": "2024-06-10",
                    "Content-Type": "application/json",
                },
                json={
                    "model_id": self.model_id,
                    "transcript": text,
                    "voice": {
                        "mode": "id",
                        "id": self.voice_id,
                    },
                    "output_format": self.output_format,
                },
                timeout=30.0,
            ) as response:
                response.raise_for_status()
                async for chunk in response.aiter_bytes(chunk_size=4096):
                    yield chunk

    async def get_voices(self) -> list[dict]:
        if not self.api_key:
            raise ValueError("Cartesia API key not configured")

        async with httpx.AsyncClient() as client:
            response = await client.get(
                CARTESIA_VOICES_URL,
                headers={
                    "X-API-Key": self.api_key,
                    "Cartesia-Version": "2024-06-10",
                },
                timeout=30.0,
            )
            response.raise_for_status()
            return response.json()


class CartesiaStreamManager:
    def __init__(self):
        self.api_key = settings.cartesia_api_key
        self.voice_id = settings.cartesia_voice_id
        self.model_id = "sonic-english"
        self.sample_rate = 24000
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def reset(self):
        self._cancelled = False

    async def synthesize_streaming(
        self,
        text_generator: AsyncGenerator[str, None],
        chunk_size: int = 4096,
    ) -> AsyncGenerator[bytes, None]:
        if not self.api_key:
            raise ValueError("Cartesia API key not configured")

        buffer = ""
        sentence_endings = ".!?,"
        min_chars = 25

        async for text_chunk in text_generator:
            if self._cancelled:
                logger.info("TTS cancelled")
                return

            buffer += text_chunk

            last_ending = -1
            for i, char in enumerate(buffer):
                if char in sentence_endings:
                    last_ending = i

            if last_ending >= min_chars:
                segment = buffer[:last_ending + 1].strip()
                buffer = buffer[last_ending + 1:]

                if segment:
                    async for audio_chunk in self._synthesize_sentence(segment, chunk_size):
                        if self._cancelled:
                            return
                        yield audio_chunk

        if buffer.strip() and not self._cancelled:
            async for audio_chunk in self._synthesize_sentence(buffer.strip(), chunk_size):
                if self._cancelled:
                    return
                yield audio_chunk

    async def _synthesize_sentence(self, text: str, chunk_size: int) -> AsyncGenerator[bytes, None]:
        # Skip empty or invalid text
        if not text or len(text.strip()) == 0:
            logger.warning("Skipping TTS for empty text")
            return

        # Skip JSON-like content that shouldn't be spoken
        stripped = text.strip()
        if stripped.startswith('{') and stripped.endswith('}'):
            logger.warning(f"Skipping TTS for JSON-like content: {text[:50]}")
            return

        # Skip control messages
        if stripped.startswith('__') and stripped.endswith('__'):
            logger.warning(f"Skipping TTS for control message: {text[:50]}")
            return

        logger.info(f"Synthesizing: {text[:50]}...")

        async with httpx.AsyncClient() as client:
            try:
                async with client.stream(
                    "POST",
                    CARTESIA_TTS_URL,
                    headers={
                        "X-API-Key": self.api_key,
                        "Cartesia-Version": "2024-06-10",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model_id": self.model_id,
                        "transcript": text,
                        "voice": {
                            "mode": "id",
                            "id": self.voice_id,
                        },
                        "output_format": {
                            "container": "raw",
                            "encoding": "pcm_s16le",
                            "sample_rate": self.sample_rate,
                        },
                    },
                    timeout=30.0,
                ) as response:
                    response.raise_for_status()
                    async for chunk in response.aiter_bytes(chunk_size=chunk_size):
                        yield chunk
            except Exception as e:
                logger.error(f"TTS error: {e}")
                raise


cartesia_service = CartesiaService()
