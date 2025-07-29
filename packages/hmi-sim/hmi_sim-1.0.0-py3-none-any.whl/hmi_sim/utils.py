import pyautogui as pgui

def get_screen_size():
    return pgui.size()

def get_tweening_modes():
    return [
        pgui.easeInOutQuad,
        pgui.easeInBounce,
        pgui.easeInOutBounce,
        pgui.easeInOutElastic,
        pgui.easeInOutSine
    ]

def speak_if_enabled(text, config):
    if config['enable_audio']:
        from win32com.client import Dispatch
        Dispatch("SAPI.SpVoice").Speak(text)
