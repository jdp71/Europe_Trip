#!/usr/bin/env python3
"""Generate simple PNG icons for the PWA."""
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    import subprocess, sys
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pillow", "-q"])
    from PIL import Image, ImageDraw, ImageFont

ICONS = Path(__file__).parent / "icons"
ICONS.mkdir(exist_ok=True)


def make_icon(size: int):
    img = Image.new("RGB", (size, size), "#1a365d")
    draw = ImageDraw.Draw(img)
    # Simple globe + plane motif
    cx, cy = size // 2, size // 2
    r = int(size * 0.28)
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline="#ffffff", width=max(2, size // 40))
    draw.arc([cx - r, cy - r, cx + r, cy + r], 200, 340, fill="#ffffff", width=max(2, size // 50))
    draw.line([cx - r, cy, cx + r, cy], fill="#ffffff", width=max(1, size // 60))
    # EU stars hint
    for i in range(5):
        sx = cx - r + (i + 1) * (2 * r) // 6
        sy = cy - r // 3
        draw.ellipse([sx - 3, sy - 3, sx + 3, sy + 3], fill="#fbbf24")
    img.save(ICONS / f"icon-{size}.png", "PNG")
    print(f"Created icon-{size}.png")


if __name__ == "__main__":
    make_icon(192)
    make_icon(512)
