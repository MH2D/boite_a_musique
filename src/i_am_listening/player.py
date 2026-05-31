import subprocess
from pathlib import Path

from .config import PROJECT_ROOT, get_play_command


class Player:
    """Audio player using platform-native subprocess commands."""

    def __init__(self) -> None:
        self._process: subprocess.Popen | None = None
        self._command_prefix = get_play_command()

    def play(self, song_path: str) -> None:
        """Play a song file. Stops any currently playing track first."""
        self.stop()
        full_path = PROJECT_ROOT / song_path
        if not full_path.exists():
            print(f"  File not found: {full_path}")
            return
        self._process = subprocess.Popen(
            [*self._command_prefix, str(full_path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def stop(self) -> None:
        """Stop the currently playing track, if any."""
        if self._process is not None:
            self._process.terminate()
            self._process.wait()
            self._process = None

    @property
    def is_playing(self) -> bool:
        if self._process is None:
            return False
        return self._process.poll() is None
