#!/usr/bin/env python3
"""Generate printable barcode labels with portrait thumbnails, and an HTML dashboard."""

import base64
import json
from io import BytesIO
from pathlib import Path

import barcode
from barcode.writer import ImageWriter
from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_JSON = PROJECT_ROOT / "data.json"
MAPPINGS_JSON = PROJECT_ROOT / "mappings.json"
PORTRAITS_DIR = PROJECT_ROOT / "portraits"
OUTPUT_DIR = PROJECT_ROOT / "barcodes"
DASHBOARD_HTML = PROJECT_ROOT / "dashboard.html"
PRINT_SHEET_PDF = PROJECT_ROOT / "barcodes_print_sheet.pdf"


def load_data() -> list[dict]:
    with open(DATA_JSON) as f:
        return json.load(f)["items"]


def name_from_photo(photo: str) -> str:
    return Path(photo).stem


def generate_barcode_value(index: int) -> str:
    """Unique barcode string for each person."""
    return f"IAL{index:04d}"


def create_barcode_image(value: str) -> Image.Image:
    """Render a Code128 barcode to a PIL Image (sized for reliable scanning)."""
    writer = ImageWriter()
    code = barcode.get("code128", value, writer=writer)
    buf = BytesIO()
    code.write(
        buf,
        options={
            "write_text": True,
            "module_height": 25,
            "module_width": 0.4,
            "font_size": 14,
            "text_distance": 7,
            "quiet_zone": 10,
        },
    )
    buf.seek(0)
    return Image.open(buf).convert("RGB")


def create_label(barcode_value: str, portrait_path: Path, name: str) -> Image.Image:
    """Barcode on top, small portrait + name below."""
    barcode_img = create_barcode_image(barcode_value)

    portrait = Image.open(portrait_path).convert("RGB")
    portrait.thumbnail((100, 100))

    padding = 14
    name_height = 26
    width = max(barcode_img.width, portrait.width + padding * 2)
    height = barcode_img.height + portrait.height + name_height + padding

    label = Image.new("RGB", (width, height), "white")

    # Centre barcode
    x_bc = (width - barcode_img.width) // 2
    label.paste(barcode_img, (x_bc, 0))

    # Centre portrait below barcode
    y_portrait = barcode_img.height + 4
    x_portrait = (width - portrait.width) // 2
    label.paste(portrait, (x_portrait, y_portrait))

    # Name text below portrait
    draw = ImageDraw.Draw(label)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 18)
    except OSError:
        font = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), name, font=font)
    tw = bbox[2] - bbox[0]
    x_text = (width - tw) // 2
    y_text = y_portrait + portrait.height + 2
    draw.text((x_text, y_text), name, fill="black", font=font)

    return label


def image_to_data_uri(img: Image.Image, max_width: int = 0) -> str:
    """Convert PIL Image to a base64 data URI."""
    if max_width and img.width > max_width:
        ratio = max_width / img.width
        img = img.resize((max_width, int(img.height * ratio)), Image.LANCZOS)
    buf = BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/png;base64,{b64}"


def file_to_data_uri(path: Path) -> str:
    """Read an image file and return a base64 data URI."""
    suffix = path.suffix.lower()
    mime = "image/jpeg" if suffix in (".jpg", ".jpeg") else "image/png"
    b64 = base64.b64encode(path.read_bytes()).decode()
    return f"data:{mime};base64,{b64}"


def generate_print_pdf(labels: list[Image.Image], output_path: Path, cols: int = 2) -> int:
    """Assemble barcode labels into a multi-page A4 PDF (300 DPI).

    Returns the number of pages generated.
    """
    if not labels:
        return 0

    # A4 at 300 DPI
    page_w, page_h = 2480, 3508
    margin = 80
    spacing = 40

    usable_w = page_w - 2 * margin
    usable_h = page_h - 2 * margin
    cell_w = (usable_w - (cols - 1) * spacing) // cols

    # Scale each label to fit cell width, preserving aspect ratio
    scaled: list[Image.Image] = []
    for lbl in labels:
        ratio = cell_w / lbl.width
        new_h = int(lbl.height * ratio)
        scaled.append(lbl.resize((cell_w, new_h), Image.LANCZOS))

    cell_h = max(s.height for s in scaled)

    # How many rows fit on one page?
    rows_per_page = max(1, (usable_h + spacing) // (cell_h + spacing))
    labels_per_page = rows_per_page * cols

    # Build pages
    pages: list[Image.Image] = []
    for page_start in range(0, len(scaled), labels_per_page):
        page = Image.new("RGB", (page_w, page_h), "white")
        batch = scaled[page_start : page_start + labels_per_page]
        for idx, img in enumerate(batch):
            r, c = divmod(idx, cols)
            x = margin + c * (cell_w + spacing)
            y = margin + r * (cell_h + spacing)
            page.paste(img, (x, y))
        pages.append(page)

    # Save as multi-page PDF
    pages[0].save(
        str(output_path),
        format="PDF",
        resolution=300,
        save_all=True,
        append_images=pages[1:],
    )
    return len(pages)


def generate_dashboard_html(entries: list[dict], mappings: dict[str, dict]) -> str:
    """Build a self-contained HTML dashboard with two views:
    1. Overview — cards showing portrait, name, song, barcode
    2. Print sheet — compact grid of barcode labels for cutting
    """
    cards_html = []
    print_cells_html = []

    for entry in entries:
        name = entry["name"]
        barcode_value = entry["barcode"]
        song_name = Path(entry["song"]).stem
        portrait_uri = entry["portrait_uri"]
        label_uri = entry["label_uri"]

        cards_html.append(f"""
      <div class="card">
        <img class="portrait" src="{portrait_uri}" alt="{name}">
        <div class="info">
          <h3>{name}</h3>
          <p class="song" title="{song_name}">&#9835; {song_name}</p>
          <code>{barcode_value}</code>
        </div>
      </div>""")

        print_cells_html.append(f"""
      <div class="label">
        <img src="{label_uri}" alt="{name}">
      </div>""")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Boite a Musique — Dashboard</title>
<style>
  :root {{
    --bg: #f5f0eb; --card-bg: #fff; --accent: #c46f41;
    --text: #2c2420; --muted: #8a7e76;
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: "Segoe UI", system-ui, -apple-system, sans-serif;
    background: var(--bg); color: var(--text);
  }}

  /* ── NAV ── */
  nav {{
    background: var(--text); color: #fff; padding: 14px 24px;
    display: flex; align-items: center; gap: 18px;
    position: sticky; top: 0; z-index: 10;
  }}
  nav h1 {{ font-size: 1.15rem; font-weight: 600; }}
  nav button {{
    background: transparent; color: #fff; border: 1px solid rgba(255,255,255,.3);
    padding: 6px 14px; border-radius: 6px; cursor: pointer; font-size: .85rem;
  }}
  nav button:hover {{ background: rgba(255,255,255,.12); }}
  nav button.active {{ background: var(--accent); border-color: var(--accent); }}

  /* ── SEARCH ── */
  .search-bar {{
    max-width: 420px; margin: 20px auto 8px; padding: 0 20px;
  }}
  .search-bar input {{
    width: 100%; padding: 10px 14px; border-radius: 8px;
    border: 1px solid #d3cbc3; font-size: .95rem; outline: none;
  }}
  .search-bar input:focus {{ border-color: var(--accent); }}

  /* ── OVERVIEW GRID ── */
  .grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
    gap: 16px; padding: 16px 20px 40px;
    max-width: 1200px; margin: 0 auto;
  }}
  .card {{
    background: var(--card-bg); border-radius: 10px;
    overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,.08);
    display: flex; align-items: center; gap: 14px; padding: 12px;
  }}
  .card .portrait {{
    width: 72px; height: 72px; border-radius: 8px; object-fit: cover; flex-shrink: 0;
  }}
  .card .info {{ min-width: 0; }}
  .card h3 {{ font-size: 1rem; margin-bottom: 2px; }}
  .card .song {{
    color: var(--muted); font-size: .8rem;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    max-width: 170px;
  }}
  .card code {{
    font-size: .72rem; background: #f0ebe6; padding: 2px 6px; border-radius: 4px;
    margin-top: 4px; display: inline-block;
  }}

  /* ── PRINT GRID ── */
  .print-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 10px; padding: 20px;
    max-width: 1100px; margin: 0 auto;
  }}
  .label {{ text-align: center; }}
  .label img {{ max-width: 100%; height: auto; }}

  /* hide/show views */
  .view {{ display: none; }}
  .view.active {{ display: block; }}

  /* ── PRINT MEDIA ── */
  @media print {{
    nav, .search-bar {{ display: none !important; }}
    .view {{ display: none !important; }}
    .view.print-view {{ display: block !important; }}
    .print-grid {{ padding: 0; gap: 6px; }}
    .label img {{ max-height: 160px; }}
  }}
</style>
</head>
<body>

<nav>
  <h1>Boite a Musique</h1>
  <button class="active" onclick="show('overview')">Overview</button>
  <button onclick="show('print')">Print Barcodes</button>
  <button onclick="window.print()">&#128424; Print</button>
</nav>

<div id="overview" class="view active">
  <div class="search-bar">
    <input type="text" id="search" placeholder="Search by name or song..." oninput="filter()">
  </div>
  <div class="grid" id="cards">
    {"".join(cards_html)}
  </div>
</div>

<div id="print" class="view print-view">
  <div class="print-grid">
    {"".join(print_cells_html)}
  </div>
</div>

<script>
function show(id) {{
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  document.querySelectorAll('nav button').forEach(b => b.classList.remove('active'));
  event.target.classList.add('active');
}}
function filter() {{
  const q = document.getElementById('search').value.toLowerCase();
  document.querySelectorAll('.card').forEach(c => {{
    const text = c.textContent.toLowerCase();
    c.style.display = text.includes(q) ? '' : 'none';
  }});
}}
</script>
</body>
</html>"""


def main():
    data = load_data()
    OUTPUT_DIR.mkdir(exist_ok=True)

    mappings: dict[str, dict] = {}
    entries: list[dict] = []
    all_labels: list[Image.Image] = []

    for i, item in enumerate(data, start=1):
        photo = item["photo"]
        song = item["song"]
        name = name_from_photo(photo)
        barcode_value = generate_barcode_value(i)

        portrait_path = PORTRAITS_DIR / photo
        if not portrait_path.exists():
            print(f"  SKIP  {name} — portrait not found ({portrait_path})")
            continue

        # Create and save individual label image
        label = create_label(barcode_value, portrait_path, name)
        label_path = OUTPUT_DIR / f"{name}_{barcode_value}.png"
        label.save(str(label_path))

        # Prepare data URIs for the HTML dashboard
        portrait_uri = file_to_data_uri(portrait_path)
        label_uri = image_to_data_uri(label)

        all_labels.append(label)
        entries.append(
            {
                "name": name,
                "barcode": barcode_value,
                "song": song,
                "portrait_uri": portrait_uri,
                "label_uri": label_uri,
            }
        )
        mappings[barcode_value] = {"name": name, "song": song}
        print(f"  OK    {name:20s} → {barcode_value}")

    # Save mappings
    with open(MAPPINGS_JSON, "w") as f:
        json.dump(mappings, f, indent=2, ensure_ascii=False)

    # Generate print sheet PDF
    num_pages = generate_print_pdf(all_labels, PRINT_SHEET_PDF)

    # Generate dashboard HTML
    html = generate_dashboard_html(entries, mappings)
    DASHBOARD_HTML.write_text(html)

    print(f"\n✓ {len(entries)} barcode labels saved to  {OUTPUT_DIR}/")
    print(f"✓ mappings.json updated")
    print(f"✓ print sheet →  {PRINT_SHEET_PDF}  ({num_pages} page(s))")
    print(f"✓ dashboard →  {DASHBOARD_HTML}")


if __name__ == "__main__":
    main()
