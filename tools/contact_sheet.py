"""Build a tiled contact sheet from numbered PNG screenshots."""

import math
import os
import re
import sys
from PIL import Image, ImageDraw, ImageFont

TILE_W = 200
TILE_H = 150


def load_font():
    try:
        return ImageFont.truetype("arial.ttf", 14)
    except OSError:
        try:
            return ImageFont.load_default(size=14)
        except TypeError:
            return ImageFont.load_default()


def is_all_black(img: Image.Image) -> bool:
    extrema = img.convert("RGB").getextrema()
    return all(lo == 0 and hi == 0 for lo, hi in extrema)


def make_tile(path: str | None, idx: int, interval: float | None, font) -> Image.Image:
    if path is None or not os.path.isfile(path):
        return Image.new("RGB", (TILE_W, TILE_H), (0, 0, 0))
    try:
        with Image.open(path) as src:
            rgb = src.convert("RGB")
            if is_all_black(rgb):
                return Image.new("RGB", (TILE_W, TILE_H), (0, 0, 0))
            scale = min(TILE_W / rgb.width, TILE_H / rgb.height)
            nw = max(1, int(round(rgb.width * scale)))
            nh = max(1, int(round(rgb.height * scale)))
            resized = rgb.resize((nw, nh), Image.Resampling.LANCZOS)
    except OSError:
        return Image.new("RGB", (TILE_W, TILE_H), (0, 0, 0))

    tile = Image.new("RGB", (TILE_W, TILE_H), (0, 0, 0))
    tile.paste(resized, ((TILE_W - nw) // 2, (TILE_H - nh) // 2))

    label = f"{idx}" if interval is None else f"{idx} ({idx * interval:g}s)"
    draw = ImageDraw.Draw(tile)
    draw.text(
        (4, 3),
        label,
        font=font,
        fill=(255, 255, 255),
        stroke_width=2,
        stroke_fill=(0, 0, 0),
    )
    return tile


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python tools/contact_sheet.py <prefix> [cols=9] [interval]", file=sys.stderr)
        return 1

    prefix = sys.argv[1]
    cols = int(sys.argv[2]) if len(sys.argv) >= 3 else 9
    interval = float(sys.argv[3]) if len(sys.argv) >= 4 else None

    parent = os.path.dirname(prefix) or "."
    base = os.path.basename(prefix)
    pattern = re.compile(rf"^{re.escape(base)}(\d+)\.png$", re.IGNORECASE)

    found: dict[int, str] = {}
    if os.path.isdir(parent):
        for entry in os.listdir(parent):
            m = pattern.match(entry)
            if m:
                found[int(m.group(1))] = os.path.join(parent, entry)

    if not found:
        print(f"No matching PNGs for prefix: {prefix}", file=sys.stderr)
        return 1

    min_idx = min(found)
    max_idx = max(found)
    indices = range(min_idx, max_idx + 1)

    font = load_font()
    tiles = [make_tile(found.get(i), i, interval, font) for i in indices]

    rows = math.ceil(len(tiles) / cols)
    sheet = Image.new("RGB", (cols * TILE_W, rows * TILE_H), (0, 0, 0))
    for pos, tile in enumerate(tiles):
        r, c = divmod(pos, cols)
        sheet.paste(tile, (c * TILE_W, r * TILE_H))

    out_path = f"{prefix}sheet.png"
    sheet.save(out_path)
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
