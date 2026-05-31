import platform
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_JSON = PROJECT_ROOT / "data.json"
MAPPINGS_JSON = PROJECT_ROOT / "mappings.json"
MUSIC_DIR = PROJECT_ROOT / "musique_portrait"


def get_play_command() -> list[str]:
    """Return the platform-appropriate audio playback command prefix."""
    if platform.system() == "Darwin":
        return ["afplay"]
    if shutil.which("mpv"):
        return ["mpv", "--no-video"]
    raise RuntimeError(
        "No audio player found. Install mpv (apt install mpv) or run on macOS."
    )
