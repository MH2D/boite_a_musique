import argparse
import sys

from .mappings import (
    add_mapping,
    get_available_people,
    load_mappings,
    name_from_photo,
    remove_mapping,
)
from .player import Player
from .scanner import stdin_reader


def cmd_play() -> None:
    """Main play loop: scan barcode → lookup → play song."""
    mappings = load_mappings()
    if not mappings:
        print("No mappings found. Run 'add' first to assign barcodes to songs.")
        sys.exit(1)

    player = Player()
    print(f"Ready! {len(mappings)} songs mapped. Scan a barcode...")
    print("(Ctrl+C to quit)\n")

    try:
        for barcode in stdin_reader():
            if barcode in mappings:
                entry = mappings[barcode]
                print(f"  {entry['name']} -> {entry['song']}")
                player.play(entry["song"])
            else:
                print(f"  Unknown barcode: {barcode}")
    except KeyboardInterrupt:
        print("\nStopping...")
        player.stop()


def cmd_add() -> None:
    """Interactive: scan a barcode, pick a person from data.json, save mapping."""
    available = get_available_people()
    if not available:
        print("All people from data.json are already mapped!")
        return

    print("Available people (not yet mapped):")
    for i, item in enumerate(available, 1):
        name = name_from_photo(item["photo"])
        song_name = item["song"].removeprefix("musique_portrait/")
        print(f"  {i:>2}. {name:<20} -> {song_name}")

    print()
    barcode = input("Scan a barcode (or type it): ").strip()
    if not barcode:
        print("No barcode entered.")
        return

    # Check if barcode already exists
    existing = load_mappings()
    if barcode in existing:
        print(f"Barcode already mapped to: {existing[barcode]['name']}")
        return

    try:
        choice = int(input("Pick a number: ").strip())
    except (ValueError, EOFError):
        print("Invalid choice.")
        return

    if not (1 <= choice <= len(available)):
        print(f"Choice must be between 1 and {len(available)}.")
        return

    item = available[choice - 1]
    name = name_from_photo(item["photo"])
    add_mapping(barcode, name, item["song"])
    song_name = item["song"].removeprefix("musique_portrait/")
    print(f"\nAdded: {barcode} -> {name} ({song_name})")


def cmd_list() -> None:
    """Print all barcode→song mappings."""
    mappings = load_mappings()
    if not mappings:
        print("No mappings yet. Run 'add' to create some.")
        return

    print(f"{len(mappings)} mapping(s):\n")
    for barcode, entry in mappings.items():
        song_name = entry["song"].removeprefix("musique_portrait/")
        print(f"  {barcode}  ->  {entry['name']:<20} ({song_name})")


def cmd_remove(barcode: str) -> None:
    """Remove a mapping by barcode value."""
    if remove_mapping(barcode):
        print(f"Removed mapping for barcode: {barcode}")
    else:
        print(f"No mapping found for barcode: {barcode}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="i_am_listening",
        description="Barcode-triggered music player",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("play", help="Scan barcodes and play songs (default)")
    sub.add_parser("add", help="Scan a barcode and assign it to a person/song")
    sub.add_parser("list", help="Show all barcode-to-song mappings")

    rm = sub.add_parser("remove", help="Remove a barcode mapping")
    rm.add_argument("barcode", help="Barcode value to remove")

    args = parser.parse_args()

    match args.command:
        case "add":
            cmd_add()
        case "list":
            cmd_list()
        case "remove":
            cmd_remove(args.barcode)
        case _:
            cmd_play()
