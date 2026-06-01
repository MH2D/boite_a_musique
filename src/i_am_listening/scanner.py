import platform
from collections.abc import Generator

_AZERTY_TO_QWERTY = str.maketrans(
    "&é\"'(§è!çà" "aqzwAQZW",
    "1234567890" "qawzQAWZ",
)

# HID keycode → character (US layout), used by evdev reader
_KEY_MAP = {
    2: "1", 3: "2", 4: "3", 5: "4", 6: "5",
    7: "6", 8: "7", 9: "8", 10: "9", 11: "0",
    16: "q", 17: "w", 18: "e", 19: "r", 20: "t",
    21: "y", 22: "u", 23: "i", 24: "o", 25: "p",
    30: "a", 31: "s", 32: "d", 33: "f", 34: "g",
    35: "h", 36: "j", 37: "k", 38: "l",
    44: "z", 45: "x", 46: "c", 47: "v", 48: "b",
    49: "n", 50: "m",
    12: "-", 13: "=", 26: "[", 27: "]", 39: ";",
    40: "'", 43: "\\", 51: ",", 52: ".", 53: "/",
}
_KEY_ENTER = 28


def fix_azerty(raw: str) -> str:
    return raw.translate(_AZERTY_TO_QWERTY)


def stdin_reader() -> Generator[str, None, None]:
    while True:
        try:
            raw = input()
            raw = raw.strip()
            if raw:
                yield fix_azerty(raw)
        except EOFError:
            break


def _find_scanner_device():
    import evdev
    devices = [evdev.InputDevice(p) for p in evdev.list_devices()]
    for dev in devices:
        if dev.info.bustype == 3:
            return dev
    for dev in devices:
        if "barcode" in dev.name.lower() or "scanner" in dev.name.lower():
            return dev
    for dev in devices:
        if "keyboard" in dev.name.lower() and "hdmi" not in dev.name.lower():
            return dev
    return None


def evdev_reader() -> Generator[str, None, None]:
    import time
    import evdev
    while True:
        dev = _find_scanner_device()
        if dev is None:
            print("Waiting for barcode scanner...")
            time.sleep(2)
            continue
        print(f"Reading from device: {dev.name} ({dev.path})")
        try:
            dev.grab()
        except OSError:
            time.sleep(1)
            continue
        buffer = []
        shift = False
        try:
            for event in dev.read_loop():
                if event.type != evdev.ecodes.EV_KEY:
                    continue
                is_shift = event.code in (42, 54)
                if is_shift:
                    shift = event.value != 0
                    continue
                if event.value != 1:
                    continue
                if event.code == _KEY_ENTER:
                    barcode = "".join(buffer).strip()
                    buffer.clear()
                    if barcode:
                        yield barcode.upper()
                elif event.code in _KEY_MAP:
                    ch = _KEY_MAP[event.code]
                    buffer.append(ch.upper() if shift else ch)
        except OSError:
            print("Scanner disconnected, reconnecting...", flush=True)
            try:
                dev.ungrab()
            except Exception:
                pass
            time.sleep(1)


def barcode_reader() -> Generator[str, None, None]:
    if platform.system() == "Linux":
        try:
            yield from evdev_reader()
        except ImportError:
            yield from stdin_reader()
    else:
        yield from stdin_reader()
