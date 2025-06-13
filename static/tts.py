from fastapi import APIRouter
import pyttsx3
import io
import sounddevice as sd
import numpy as np
from config import TTS_ENABLED

router = APIRouter()

@router.get("/speak")
async def speak_endpoint(text: str):
    if not TTS_ENABLED:
        return {"error": "TTS відключено"}
    try:
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
        return StreamingResponse(buffer, media_type="audio/wav")
    except Exception as e:
        return {"error": str(e)}