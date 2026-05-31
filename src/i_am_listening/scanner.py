from collections.abc import Generator


def stdin_reader() -> Generator[str, None, None]:
    """Read barcodes from stdin (the scanner types barcode + Enter)."""
    while True:
        try:
            barcode = input()
            barcode = barcode.strip()
            if barcode:
                yield barcode
        except EOFError:
            break
