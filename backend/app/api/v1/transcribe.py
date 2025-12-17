from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel

from app.api.deps import CurrentUser
from app.services.transcription import transcription_service

router = APIRouter()


class TranscriptionResponse(BaseModel):
    text: str


@router.post("", response_model=TranscriptionResponse)
async def transcribe_audio(
    current_user: CurrentUser,
    audio: UploadFile = File(...),
):
    if not audio.content_type or not audio.content_type.startswith("audio/"):
        if audio.content_type not in ["video/webm", "application/octet-stream"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type: {audio.content_type}. Expected audio file.",
            )

    try:
        text = await transcription_service.transcribe(audio)
        return TranscriptionResponse(text=text)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Transcription failed: {str(e)}",
        )
