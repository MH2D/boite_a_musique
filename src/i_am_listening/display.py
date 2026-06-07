import platform
import unicodedata

from .config import LCD_ADDRESS, LCD_COLS, LCD_EXPANDER, LCD_PORT, LCD_ROWS

# Custom 5x8 glyph for CGRAM slot 0: a musical note shown while a song plays.
_NOTE_GLYPH = (
    0b00001,
    0b00011,
    0b00101,
    0b01001,
    0b01001,
    0b01011,
    0b11011,
    0b11000,
)
_NOTE = "\x00"  # writing chr(0) renders the custom glyph above


def _to_lcd_text(text: str) -> str:
    """The HD44780 character ROM only covers ASCII, so strip accents (é -> e)
    to keep French names legible instead of rendering as garbage."""
    normalized = unicodedata.normalize("NFKD", text)
    return normalized.encode("ascii", "ignore").decode("ascii")


class Display:
    """Optional 16x2 I2C LCD wrapper.

    The screen is a *visual extra*: the music box must run fully without it. So
    every interaction with the hardware is guarded, and any failure (no library,
    no screen, wrong wiring, or the LCD being unplugged mid-run) permanently
    disables the display as a silent no-op — playback is never affected.
    """

    def __init__(self) -> None:
        self._lcd = None
        # Non-Linux (e.g. macOS local dev) has no I2C hardware: stay a no-op.
        if platform.system() != "Linux":
            return
        try:
            from RPLCD.i2c import CharLCD

            self._lcd = CharLCD(
                i2c_expander=LCD_EXPANDER,
                address=LCD_ADDRESS,
                port=LCD_PORT,
                cols=LCD_COLS,
                rows=LCD_ROWS,
                backlight_enabled=True,
            )
            self._lcd.create_char(0, _NOTE_GLYPH)
        except Exception as exc:  # missing lib, no screen, bad wiring — all fine
            print(f"  (no LCD, running without it: {exc})", flush=True)
            self._lcd = None

    def _write(self, line1: str, line2: str = "") -> None:
        """Render two lines, truncated to the panel width. Disables the display
        on any I2C error so a screen that vanishes can't take the player down."""
        if self._lcd is None:
            return
        try:
            self._lcd.clear()
            self._lcd.write_string(_to_lcd_text(line1)[:LCD_COLS])
            if line2:
                self._lcd.crlf()
                self._lcd.write_string(line2[:LCD_COLS])
        except Exception:
            self._lcd = None

    def ready(self) -> None:
        """Idle screen shown while waiting for a scan."""
        self._write("Boite a Musique", "Scannez un code")

    def now_playing(self, name: str) -> None:
        """Show the scanned person's name with the musical-note glyph."""
        self._write(_to_lcd_text(name), f"{_NOTE} en lecture")

    def unknown(self) -> None:
        """Shown when a scanned barcode isn't in the mappings."""
        self._write("Code inconnu", "Reessayez")

    def stop(self) -> None:
        """Clear the screen (e.g. on shutdown)."""
        if self._lcd is None:
            return
        try:
            self._lcd.clear()
        except Exception:
            self._lcd = None
