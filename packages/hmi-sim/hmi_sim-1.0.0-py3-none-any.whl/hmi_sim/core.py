import time
import random
import pyautogui as pgui
from datetime import datetime, timedelta
from .config import get_config
from .utils import get_screen_size, get_tweening_modes, speak_if_enabled


def simulate_hmi_interaction(end_time=None):

    config = get_config()
    sWidth, sHeight = get_screen_size()
    tweening_modes = get_tweening_modes()

    master_list = list(range(*config['taskbar_apps_range']))
    current_choice = random.choice(master_list)

    while True:
        if end_time and datetime.now() >= end_time:
            print("Ending hmi interation sim")
            break

        slave_list = master_list.copy()
        slave_list.remove(current_choice)
        current_choice = random.choice(slave_list)
        how_many_mouse_movements = random.randint(*config['num_mouse_movements'])

        speak_if_enabled(f"Choosing application {current_choice} and mouse movements {how_many_mouse_movements}",
                         config)

        with pgui.hold('win'):
            pgui.press(str(current_choice))

        for _ in range(how_many_mouse_movements):
            pgui.moveTo(
                random.randint(0, sWidth),
                random.randint(0, sHeight),
                random.randint(*config['mouse_movement_speed']),
                random.choice(tweening_modes)
            )
            if config['enable_random_clicks']:
                pgui.click()

        time.sleep(random.randint(*config['sleep_time_range']))