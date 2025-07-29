import configparser
from pathlib import Path
import importlib.resources as resources
import shutil

APP_DIR = Path.home() / ".hmi-sim"
USER_CONFIG_PATH = APP_DIR / "config.ini"
DEFAULT_CONFIG_NAME = "default_config.ini"


def initialize_user_config():
    """Create ~/.hmi-sim/config.ini if it doesn't exist, using packaged default."""
    if not USER_CONFIG_PATH.exists():
        APP_DIR.mkdir(parents=True, exist_ok=True)
        with resources.files("hmi_sim").joinpath(DEFAULT_CONFIG_NAME).open("rb") as src:
            with open(USER_CONFIG_PATH, "wb") as dst:
                shutil.copyfileobj(src, dst)
        print(f"[HMI-Sim] Default config copied to: {USER_CONFIG_PATH}")


def parse_config(config: configparser.ConfigParser) -> dict:
    """Convert the raw config object into parsed Python types."""
    return {
        'enable_audio': config.getboolean('Settings', 'enable_audio'),
        'sleep_time_range': list(map(int, config.get('Settings', 'sleep_time_range').split(','))),
        'taskbar_apps_range': list(map(int, config.get('Settings', 'taskbar_apps_range').split(','))),
        'num_mouse_movements': list(map(int, config.get('Settings', 'num_mouse_movements').split(','))),
        'mouse_movement_speed': list(map(int, config.get('Settings', 'mouse_movement_speed').split(','))),
        'enable_random_clicks': config.getboolean('Settings', 'enable_random_clicks'),
    }


def get_config(cli_path=None):
    config = configparser.ConfigParser()

    if cli_path:
        config.read(Path(cli_path).expanduser())
        return parse_config(config)

    # Ensure user config is initialized
    initialize_user_config()
    if USER_CONFIG_PATH.exists():
        config.read(USER_CONFIG_PATH)
        return parse_config(config)

    # Final fallback: bundled default (read-only)
    with resources.files("hmi_sim").joinpath(DEFAULT_CONFIG_NAME).open("r") as f:
        config.read_file(f)
        print("[HMI-Sim] Loaded default packaged config (read-only).")

    return parse_config(config)