#!/usr/bin/env python3
"""Rebuild the site icons from the Bake AI bread mascot (tools/og/bakeai-bread.png, transparent PNG).

Writes into site/:
  favicon.ico            16, 32 and 48 px frames (transparent), for browser tabs
  favicon-32x32.png      32 px, transparent
  icon-192.png           192 px, transparent (web manifest)
  icon-512.png           512 px, transparent (web manifest)
  apple-touch-icon.png   180 px on the site's greige paper (iOS ignores transparency and rounds the corners)

  python3 tools/og/make_icons.py        (needs Pillow; run from anywhere)
"""
import os
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(HERE, "..", "..", "site")
SRC = os.path.join(HERE, "bakeai-bread.png")
PAPER = (0xDD, 0xD7, 0xCB, 255)


def square(img, margin):
    """Crop to the visible pixels, then centre on a transparent square with `margin` (fraction of the side)."""
    img = img.crop(img.getchannel("A").getbbox())
    side = round(max(img.size) / (1 - 2 * margin))
    out = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    out.paste(img, ((side - img.width) // 2, (side - img.height) // 2), img)
    return out


def sized(img, px):
    return img.resize((px, px), Image.LANCZOS)


def main():
    bread = Image.open(SRC).convert("RGBA")
    tab = square(bread, 0.02)       # tab icons: as large as possible so the loaf reads at 16 px
    app = square(bread, 0.14)       # app icons: room for the rounded mask

    sized(tab, 48).save(os.path.join(SITE, "favicon.ico"), format="ICO", sizes=[(16, 16), (32, 32), (48, 48)])
    sized(tab, 32).save(os.path.join(SITE, "favicon-32x32.png"), optimize=True)
    sized(app, 192).save(os.path.join(SITE, "icon-192.png"), optimize=True)
    sized(app, 512).save(os.path.join(SITE, "icon-512.png"), optimize=True)

    touch = Image.new("RGBA", (180, 180), PAPER)
    icon = sized(app, 180)
    touch.alpha_composite(icon)
    touch.convert("RGB").save(os.path.join(SITE, "apple-touch-icon.png"), optimize=True)
    print("wrote favicon.ico, favicon-32x32.png, icon-192.png, icon-512.png, apple-touch-icon.png in",
          os.path.normpath(SITE))


if __name__ == "__main__":
    main()
