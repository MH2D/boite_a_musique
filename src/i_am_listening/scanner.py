from collections.abc import Generator

# Mac French AZERTY: the barcode scanner sends US HID keycodes, but macOS
# interprets them through the active keyboard layout.  Characters that land on
# different physical keys between QWERTY and Mac-French AZERTY get mangled.
#
# This table maps what we *receive* (AZERTY interpretation) back to the
# character the scanner *intended* (QWERTY).
_AZERTY_TO_QWERTY = str.maketrans(
    # digits (AZERTY unshifted number row → QWERTY digits)
    "&é\"'(§è!çà"
    # letters that move between the two layouts
    "aqzwAQZW",
    "1234567890"
    "qawzQAWZ",
)


def fix_azerty(raw: str) -> str:
    """Translate AZERTY-mangled scanner output back to QWERTY."""
    return raw.translate(_AZERTY_TO_QWERTY)


def stdin_reader() -> Generator[str, None, None]:
    """Read barcodes from stdin (the scanner types barcode + Enter).

    Applies AZERTY→QWERTY correction automatically.
    """
    while True:
        try:
            raw = input()
            raw = raw.strip()
            if raw:
                yield fix_azerty(raw)
        except EOFError:
            break
