from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import pyttsx3
import io
import sounddevice as sd
import numpy as np
import pydub
import asyncio
import os
from config import BASE_DIR, TTS_ENABLED, TTS_ENGINE
from database import save_interaction
from utils.notify_user import notify_user

router = APIRouter()

@router.get("/speak")
async def speak_endpoint(text: str, user_id: str = "web_user"):
    """FastAPI ендпоінт для TTS."""
    if not TTS_ENABLED:
        await notify_user(user_id, "TTS відключено")
        return {"error": "TTS відключено"}
    try:
        if TTS_ENGINE == "espeak":
            audio_file = os.path.join(BASE_DIR, "temp_audio.wav")
            os.system(f'espeak -v uk "{text}" -w {audio_file}')
            audio = pydub.AudioSegment.from_wav(audio_file)
            buffer = io.BytesIO()
            audio.export(buffer, format="wav")
            buffer.seek(0)
            await save_interaction(user_id, f"TTS: {text}", "eSpeak audio generated")
            return StreamingResponse(buffer, media_type="audio/wav")
        else:
            engine = pyttsx3.init()
            engine.setProperty('rate', 150)
            buffer = io.BytesIO()
            def callback(data, frames, time, status):
                buffer.write(data)
            stream = sd.RawOutputStream(
                samplerate=22050,
                blocksize=1024,
                channels=1,
                dtype='int16',
                callback=callback
            )
            with stream:
                engine.save_to_file(text, buffer)
                engine.runAndWait()
            buffer.seek(0)
            audio = pydub.AudioSegment.from_wav(buffer)
            buffer = io.BytesIO()
            audio.export(buffer, format="wav")
            buffer.seek(0)
            await save_interaction(user_id, f"TTS: {text}", "pyttsx3 audio generated")
            return StreamingResponse(buffer, media_type="audio/wav")
    except Exception as e:
        logger.error(f"TTS error: {str(e)}")
        from plugins.self_improvement import handle_error
        await handle_error(str(e))
        await notify_user(user_id, f"Помилка TTS: {str(e)}")
        return {"error": str(e)}