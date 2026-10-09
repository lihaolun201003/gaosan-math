# -*- coding: utf-8 -*-
"""Verify the rendered slides: ink extent, blank area, safe margins, and that no
slide is empty.  Reads the PNGs produced by the LibreOffice kit renderer.

usage:  python verify_render.py <preview_dir> [--expect-blank 0.65]
"""
import os
import sys

from PIL import Image

SLIDE_W, SLIDE_H = 960.0, 540.0
MARGIN = 60.0
DPI_DEFAULT = 200.0
MIN_BLANK = 0.65
INSET = 5                                # px: the rasteriser draws a 1px edge frame


def analyse(path, dpi):
    im = Image.open(path).convert("RGBA")
    bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
    bg.alpha_composite(im)
    im = bg.convert("L")
    W, H = im.size
    k = W / SLIDE_W                      # px per pt (horizontal)
    ky = H / SLIDE_H
    px = im.load()
    x_lo, x_hi, y_lo, y_hi = INSET, W - 1 - INSET, INSET, H - 1 - INSET

    ink_rows = [y for y in range(y_lo, y_hi + 1)
                if any(px[x, y] < 200 for x in range(x_lo, x_hi + 1))]
    if not ink_rows:
        return dict(empty=True, w=W, h=H)

    y_top, y_bot = ink_rows[0], ink_rows[-1]
    ink_cols = [x for x in range(x_lo, x_hi + 1)
                if any(px[x, y] < 200 for y in range(y_top, y_bot + 1))]
    x_l, x_r = ink_cols[0], ink_cols[-1]

    bottom_pt = (y_bot + 1) / ky
    blank = (SLIDE_H - bottom_pt) / SLIDE_H
    return dict(
        empty=False, w=W, h=H,
        top_pt=y_top / ky, bottom_pt=bottom_pt,
        left_pt=x_l / k, right_pt=(x_r + 1) / k,
        blank=blank,
        content_h_pt=bottom_pt - y_top / ky,
        n_ink_rows=len(ink_rows),
    )


def main():
    d = sys.argv[1]
    min_blank = MIN_BLANK
    if "--expect-blank" in sys.argv:
        min_blank = float(sys.argv[sys.argv.index("--expect-blank") + 1])
    files = sorted(f for f in os.listdir(d) if f.lower().endswith(".png"))
    print("%-14s %8s %8s %8s %8s %8s  %s"
          % ("page", "top", "bottom", "left", "right", "blank%", "verdict"))
    fails = 0
    for f in files:
        r = analyse(os.path.join(d, f), DPI_DEFAULT)
        if r.get("empty"):
            print("%-14s  EMPTY SLIDE" % f)
            fails += 1
            continue
        if f == "page-0001.png":                    # cover: whitespace rule N/A
            print("%-14s %8.1f %8.1f %8.1f %8.1f %7.1f%%  %s"
                  % (f, r["top_pt"], r["bottom_pt"], r["left_pt"], r["right_pt"],
                     r["blank"] * 100, "COVER"))
            continue
        problems = []
        if r["blank"] < min_blank:
            problems.append("BLANK<%.0f%%" % (min_blank * 100))
        if r["left_pt"] < MARGIN - 4:
            problems.append("LEFT MARGIN")
        if r["right_pt"] > SLIDE_W - MARGIN + 4:
            problems.append("RIGHT MARGIN")
        if r["top_pt"] < 20:
            problems.append("TOP MARGIN")
        # nothing may be drawn in the bottom 60% at all
        if r["bottom_pt"] > SLIDE_H * 0.40 + 1:
            problems.append("INTRUDES >40%")
        if problems:
            fails += 1
        print("%-14s %8.1f %8.1f %8.1f %8.1f %7.1f%%  %s"
              % (f, r["top_pt"], r["bottom_pt"], r["left_pt"], r["right_pt"],
                 r["blank"] * 100, "OK" if not problems else " + ".join(problems)))
    print("\nslides checked: %d   failures: %d" % (len(files), fails))
    return fails


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
