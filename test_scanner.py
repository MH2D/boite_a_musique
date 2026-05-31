"""Quick test: verify the barcode scanner sends data correctly.

Run with:  python test_scanner.py
Then scan any barcode (pasta box, etc.) — the script prints what it receives.
Ctrl+C to quit.
"""

import urllib.request
import json

# Mac French AZERTY: the scanner sends US keycodes, but macOS interprets them
# through the French layout.  This table maps received chars back to QWERTY.
AZERTY_TO_QWERTY = str.maketrans(
    "&é\"'(§è!çà" "aqzwAQZW",
    "1234567890" "qawzQAWZ",
)


def fix_azerty(raw: str) -> str:
    """Translate AZERTY-mangled characters back to QWERTY."""
    return raw.translate(AZERTY_TO_QWERTY)


def lookup_product(barcode: str) -> str | None:
    """Look up a barcode on Open Food Facts (free, no key needed)."""
    url = f"https://world.openfoodfacts.org/api/v2/product/{barcode}.json"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read())
            if data.get("status") == 1:
                product = data["product"]
                name = product.get("product_name", "???")
                brand = product.get("brands", "")
                return f"{name} ({brand})" if brand else name
    except Exception:
        pass
    return None


def main() -> None:
    print("=== Scanner test ===")
    print("Scan a barcode (or type one manually + Enter).")
    print("AZERTY auto-correction is ON.")
    print("Press Ctrl+C to quit.\n")

    while True:
        try:
            raw = input()
        except (EOFError, KeyboardInterrupt):
            print("\nDone.")
            break

        raw = raw.strip()
        if not raw:
            continue

        barcode = fix_azerty(raw)

        if barcode != raw:
            print(f"  Raw:      {raw!r}")
            print(f"  Fixed:    {barcode}  (AZERTY -> digits)")
        else:
            print(f"  Received: {barcode!r}  (length={len(barcode)})")

        product = lookup_product(barcode)
        if product:
            print(f"  Product:  {product}")
        else:
            print(f"  (not found on Open Food Facts)")
        print()


if __name__ == "__main__":
    main()
