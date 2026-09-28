#!/usr/bin/env python3
"""Rebuild the site icons: favicon.svg, favicon.ico (32 + 16, PNG frames) and apple-touch-icon.png (180).

The mark is a typewriter "z." in blue ink (#2F33C6) on a greige tile (#DDD7CB): the glyph outlines come from the
macOS system font Courier New Bold, so the SVG needs no web font. The PNGs are rasterised from the SVG by headless
Chrome at 512px and downsampled with Lanczos.

  python3 tools/og/make_icons.py        (needs fontTools, Pillow, Google Chrome; run from anywhere)
"""
import os, subprocess, tempfile
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.boundsPen import BoundsPen
from PIL import Image

SITE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "site")
FONT = "/System/Library/Fonts/Supplemental/Courier New Bold.ttf"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
XH, GAP = 14, 2.2          # x-height of the z and the gap before the period, in the 32-unit grid


def mark_path():
    f = TTFont(FONT)
    gs, cmap = f.getGlyphSet(), f.getBestCmap()

    def bounds(g):
        b = BoundsPen(gs); gs[g].draw(b); return b.bounds

    z, p = cmap[ord("z")], cmap[ord(".")]
    zb, pb = bounds(z), bounds(p)
    s = XH / (zb[3] - zb[1])
    zw, pw = (zb[2] - zb[0]) * s, (pb[2] - pb[0]) * s
    x0, base = (32 - (zw + GAP + pw)) / 2, 16 + XH / 2

    def path(g, dx):
        sp = SVGPathPen(gs, ntos=lambda v: ("%.2f" % v).rstrip("0").rstrip("."))
        gs[g].draw(TransformPen(sp, (s, 0, 0, -s, dx, base)))
        return sp.getCommands()

    return path(z, x0 - zb[0] * s) + path(p, x0 + zw + GAP - pb[0] * s)


def svg(d, rx=True):
    tile = '<rect width="32" height="32" rx="6" fill="#DDD7CB"/>' if rx else '<rect width="32" height="32" fill="#DDD7CB"/>'
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">{tile}<path fill="#2F33C6" d="{d}"/></svg>\n'


def raster(svg_text, tmp, name):
    src = os.path.join(tmp, name + ".svg"); open(src, "w").write(svg_text)
    page = os.path.join(tmp, name + ".html")
    open(page, "w").write('<!doctype html><style>html,body{margin:0;background:transparent}img{display:block;width:512px;height:512px}</style>'
                          f'<img src="file://{src}">')
    out = os.path.join(tmp, name + ".png")
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--default-background-color=00000000",
                    "--window-size=512,512", f"--screenshot={out}", f"file://{page}"],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return Image.open(out).convert("RGBA")


if __name__ == "__main__":
    d = mark_path()
    open(os.path.join(SITE, "favicon.svg"), "w").write(svg(d))
    with tempfile.TemporaryDirectory() as tmp:
        rounded, square = raster(svg(d), tmp, "round"), raster(svg(d, rx=False), tmp, "square")
        # iOS rounds the corners itself and turns transparency black, so the touch icon is an opaque full-bleed square
        square.convert("RGB").resize((180, 180), Image.LANCZOS).save(os.path.join(SITE, "apple-touch-icon.png"), optimize=True)
        i32, i16 = rounded.resize((32, 32), Image.LANCZOS), rounded.resize((16, 16), Image.LANCZOS)
        i32.save(os.path.join(SITE, "favicon.ico"), format="ICO", sizes=[(32, 32), (16, 16)], append_images=[i16])
    print("wrote favicon.svg, favicon.ico, apple-touch-icon.png in", os.path.normpath(SITE))
