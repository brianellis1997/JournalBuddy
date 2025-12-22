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


AVAILABLE_VOICES = {
    "carson": "a0e99841-438c-4a64-b679-ae501e7d6091",
    "brooke": "e07c00bc-4134-4eae-9ea4-1a55fb45746b",
    "caroline": "f9836c6e-a0bd-460e-9d3c-f7299fa60f94",
    "blake": "a167e0f3-df7e-4d52-a9c3-f949145efdab",
    "theo": "79f8b5fb-2cc8-479a-80df-29f7a7cf1a3e",
    "daniela": "5c5ad5e7-1020-476b-8b91-fdcbe9cc313c",
    "ayush": "791d5162-d5eb-40f0-8189-f19db44611d8",
}

DEFAULT_VOICE = "carson"


class CartesiaStreamManager:
    def __init__(self, voice_id: str = None):
        self.api_key = settings.cartesia_api_key
        self.voice_id = voice_id or settings.cartesia_voice_id
        self.model_id = "sonic-english"
        self.sample_rate = 24000
        self._cancelled = False
        self._tts_available = True
        self._tts_error_message = None

    def cancel(self):
        self._cancelled = True

    def reset(self):
        self._cancelled = False

    @property
    def is_tts_available(self) -> bool:
        return self._tts_available

    @property
    def tts_error(self) -> str | None:
        return self._tts_error_message

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
        if not self._tts_available:
            return

        if not text or len(text.strip()) == 0:
            logger.warning("Skipping TTS for empty text")
            return

        stripped = text.strip()
        if stripped.startswith('{') and stripped.endswith('}'):
            logger.warning(f"Skipping TTS for JSON-like content: {text[:50]}")
            return

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
            except httpx.HTTPStatusError as e:
                if e.response.status_code in (402, 429, 403):
                    self._tts_available = False
                    self._tts_error_message = f"TTS unavailable: {e.response.status_code}"
                    logger.warning(f"TTS credits exhausted or rate limited ({e.response.status_code}). Continuing in text-only mode.")
                else:
                    logger.error(f"TTS HTTP error: {e}")
            except Exception as e:
                logger.error(f"TTS error: {e}")


cartesia_service = CartesiaService()
