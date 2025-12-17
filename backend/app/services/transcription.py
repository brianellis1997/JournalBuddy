from groq import Groq
from fastapi import UploadFile
import tempfile
import os

from app.config import settings


class TranscriptionService:
    def __init__(self):
        self.client = Groq(api_key=settings.groq_api_key)
        self.model = "whisper-large-v3-turbo"

    async def transcribe(self, audio_file: UploadFile) -> str:
        with tempfile.NamedTemporaryFile(delete=False, suffix=self._get_suffix(audio_file.filename)) as tmp:
            content = await audio_file.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
            with open(tmp_path, "rb") as file:
                transcription = self.client.audio.transcriptions.create(
                    file=(audio_file.filename, file),
                    model=self.model,
                    response_format="text",
                )
            return transcription
        finally:
            os.unlink(tmp_path)

    def _get_suffix(self, filename: str | None) -> str:
        if filename and "." in filename:
            return "." + filename.rsplit(".", 1)[1]
        return ".webm"


transcription_service = TranscriptionService()
