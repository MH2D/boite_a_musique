import json
from pathlib import Path

from .config import DATA_JSON, MAPPINGS_JSON


def load_mappings() -> dict[str, dict]:
    """Load barcode→{name, song} mappings from mappings.json."""
    if not MAPPINGS_JSON.exists():
        return {}
    with open(MAPPINGS_JSON) as f:
        return json.load(f)


def save_mappings(mappings: dict[str, dict]) -> None:
    """Write mappings to mappings.json."""
    with open(MAPPINGS_JSON, "w") as f:
        json.dump(mappings, f, indent=2, ensure_ascii=False)


def add_mapping(barcode: str, name: str, song: str) -> None:
    """Add a barcode→song mapping."""
    mappings = load_mappings()
    mappings[barcode] = {"name": name, "song": song}
    save_mappings(mappings)


def remove_mapping(barcode: str) -> bool:
    """Remove a mapping by barcode. Returns True if it existed."""
    mappings = load_mappings()
    if barcode not in mappings:
        return False
    del mappings[barcode]
    save_mappings(mappings)
    return True


def load_data_json() -> list[dict]:
    """Load the original data.json (photo→song list)."""
    with open(DATA_JSON) as f:
        return json.load(f)["items"]


def get_available_people() -> list[dict]:
    """Return data.json entries not yet mapped to a barcode."""
    items = load_data_json()
    mappings = load_mappings()
    mapped_songs = {m["song"] for m in mappings.values()}
    return [item for item in items if item["song"] not in mapped_songs]


def name_from_photo(photo_filename: str) -> str:
    """Extract a display name from the photo filename (strip extension)."""
    return Path(photo_filename).stem
