# -*- coding: utf-8 -*-
"""Locate ink bands in a rendered slide PNG and report offsets vs known box tops."""
import os, sys
from PIL import Image

BASE = os.path.dirname(os.path.abspath(__file__))
PNG = sys.argv[1]
SLIDE_W_PT = 960.0

CASES = [("C26", 40, 26), ("C23", 120, 23), ("C32B", 200, 32),
         ("L26", 280, 26), ("L23", 360, 23), ("M26", 440, 26)]

im = Image.open(PNG)
im = im.convert("RGBA")
bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
im = Image.alpha_composite(bg, im).convert("L")
W, H = im.size
K = W / SLIDE_W_PT          # derive scale from actual rendered width (renderer may cap DPI)
print("png %dx%d (%.1f x %.1f pt) scale=%.4f px/pt" % (W, H, W / K, H / K, K))
px = im.load()
THRESH = 100
dark = [[px[x, y] < THRESH for x in range(W)] for y in range(H)]
ink = [any(row) for row in dark]
bands, y = [], 0
while y < H:
    if ink[y]:
        y0 = y
        while y < H and ink[y]:
            y += 1
        bands.append((y0, y - 1))
    else:
        y += 1

info = []
for (a, b) in bands:
    xs = [x for x in range(W) if any(dark[yy][x] for yy in range(a, b + 1))]
    info.append((a / K, b / K, min(xs) / K, max(xs) / K))

for cname, ctop, csize in CASES:
    best, bd = None, 1e9
    for (t, bt, x0, x1) in info:
        d = abs(t - ctop)
        if d < bd:
            bd, best = d, (t, bt, x0, x1)
    if best is None or bd > 40:
        print("  %-6s size=%2d  NO INK near top=%d" % (cname, csize, ctop))
        continue
    t, bt, x0, x1 = best
    print("  %-6s boxTop=%3d size=%2d | inkTop=%8.3f dTop=%+8.3f | inkBot=%8.3f dBot=%+8.3f "
          "| inkH=%6.3f = %6.4f em | inkW=%8.3f x0=%7.3f"
          % (cname, ctop, csize, t, t - ctop, bt, bt - ctop, bt - t, (bt - t) / csize, x1 - x0 + 1, x0))
