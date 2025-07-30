# cellnotifier/__init__.py

from .sound import beep, tts, play_custom_sound

def notify(sound=True, tts_message=None):
    if sound:
        beep()
    
    if tts_message:
        tts(tts_message)
