import speech_recognition as sr
import pyttsx3
import asyncio
import os
import logging
import aiofiles
from config import BASE_DIR, TTS_ENABLED, TTS_ENGINE, VOSK_MODEL_PATH
from utils import notify_user
from plugins.xai import request_xai
from vosk import Model, KaldiRecognizer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(BASE_DIR, "sakura.log"), encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

recognizer = sr.Recognizer()

async def recognize_speech_offline():
    """Офлайн розпізнавання через Vosk."""
    try:
        if not os.path.exists(VOSK_MODEL_PATH):
            logger.error("Vosk model not found")
            return None
        model = Model(VOSK_MODEL_PATH)
        rec = KaldiRecognizer(model, 16000)
        with sr.Microphone() as source:
            audio = recognizer.listen(source, timeout=5)
            if rec.AcceptWaveform(audio.get_wav_data()):
                result = rec.Result()
                text = json.loads(result)["text"]
                logger.info(f"Recognized offline speech: {text}")
                return text
            return None
    except Exception as e:
        logger.error(f"Offline speech recognition error: {str(e)}")
        return None

async def recognize_speech():
    """Онлайн розпізнавання через Google Speech API."""
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source, timeout=5)
            text = recognizer.recognize_google(audio, language="uk-UA")
            logger.info(f"Recognized speech: {text}")
            return text
    except Exception as e:
        logger.error(f"Speech recognition error: {str(e)}")
        return await recognize_speech_offline()

async def recognize_telegram_audio(audio_path):
    """Розпізнавання аудіо з Telegram."""
    try:
        async with aiofiles.open(audio_path, "rb") as f:
            audio_file = sr.AudioFile(f)
        with audio_file as source:
            recognizer.adjust_for_ambient_noise(source)
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, language="uk-UA")
            logger.info(f"Recognized Telegram audio: {text}")
            return text
    except Exception as e:
        logger.error(f"Telegram audio recognition error: {str(e)}")
        return None

async def speak(text, user_id=None):
    """TTS через обраний двигун."""
    if not TTS_ENABLED:
        return
    try:
        if TTS_ENGINE == "espeak":
            os.system(f'espeak -v uk "{text}"')
        elif TTS_ENGINE == "xai":
            audio_response = await request_xai(f"Generate audio for text: {text}", mode="voice")
            if audio_response:
                async with aiofiles.open(os.path.join(BASE_DIR, "temp_audio.wav"), "wb") as f:
                    await f.write(audio_response)
                os.startfile(os.path.join(BASE_DIR, "temp_audio.wav"))
        else:
            engine = pyttsx3.init()
            engine.setProperty('rate', 150)
            engine.say(text)
            engine.runAndWait()
        if user_id:
            await notify_user(user_id, f"Спік: {text}")
        logger.info(f"Spoke: {text}")
    except Exception as e:
        logger.error(f"Text-to-speech error: {str(e)}")

async def execute_audio_command(command, user_id, model):
    """Виконання голосової команди."""
    try:
        from main import process_command
        response = await process_command(command, user_id, model)
        await speak(response, user_id)
        return response
    except Exception as e:
        logger.error(f"Audio command execution error: {str(e)}")
        return f"Помилка: {str(e)}"