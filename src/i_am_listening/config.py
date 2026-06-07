import platform
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_JSON = PROJECT_ROOT / "data.json"
MAPPINGS_JSON = PROJECT_ROOT / "mappings.json"
MUSIC_DIR = PROJECT_ROOT / "musique_portrait"

# Optional 16x2 I2C character LCD (QAPASS 1602A + PCF8574 backpack).
# The display is a visual extra: if it's absent the player must still work, so
# nothing here is required at runtime — display.py treats any failure as a no-op.
LCD_EXPANDER = "PCF8574"
LCD_ADDRESS = 0x27  # confirmed via `i2cdetect -y 1`
LCD_PORT = 1  # GPIO I2C bus (/dev/i2c-1)
LCD_COLS = 16
LCD_ROWS = 2


def get_play_command() -> list[str]:
    """Return the platform-appropriate audio playback command prefix."""
    if platform.system() == "Darwin":
        return ["afplay"]
    if shutil.which("mpv"):
        return ["mpv", "--no-video", "--audio-device=alsa/plughw:Headphones,0"]
    raise RuntimeError(
        "No audio player found. Install mpv (apt install mpv) or run on macOS."
    )
