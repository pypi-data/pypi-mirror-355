# cellnotifier/sound.py

from gtts import gTTS
from playsound import playsound
import tempfile
import os

def tts(message):
    """Speak the message using Google Text-to-Speech."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        tts = gTTS(text=message, lang='en')
        tts.save(tmp.name)
        playsound(tmp.name)
        os.remove(tmp.name)

def beep():
    pass  # You said we don't want beep for now

def play_custom_sound(path):
    playsound(path)
