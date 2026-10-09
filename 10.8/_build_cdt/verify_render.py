# -*- coding: utf-8 -*-
"""Verify a rendered deck against the layout plan.

Checks (all in PowerPoint points, scale derived from the actual render width):
  * per visual line  : measured ink top/bottom vs planned ascent/descent
  * per visual line  : measured ink must stay inside the planned x-span
  * per element      : ink must actually be present where it was placed
  * per page         : nothing may be drawn below the planned content bottom
                       (the >=60% blank handwriting area must be untouched)
"""
import json, os, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import layout
import metrics

THRESH = 140


def load_gray(path, slide_w_pt):
    im = Image.open(path).convert("RGBA")
    bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
    im = Image.alpha_composite(bg, im).convert("L")
    return im, im.size[0] / float(slide_w_pt)


def ink_bbox(px, K, W, H, x0, y0, x1, y1):
    a = max(0, int(x0 * K))
    b = max(0, int(y0 * K))
    c = min(W, int(x1 * K) + 1)
    d = min(H, int(y1 * K) + 1)
    found = None
    for y in range(b, d):
        row = None
        for x in range(a, c):
            if px[x, y] < THRESH:
                row = x
                if found is None:
                    found = [x, y, x, y]
                else:
                    found[0] = min(found[0], x)
                    found[5 if False else 1] = min(found[1], y)
                # keep scanning to find max x cheaply
        if row is not None:
            for x in range(c - 1, a - 1, -1):
                if px[x, y] < THRESH:
                    found[2] = max(found[2], x)
                    break
            found[3] = max(found[3], y)
    if found is None:
        return None
    return (found[0] / K, found[1] / K, (found[2] + 1) / K, (found[3] + 1) / K)


def main(render_dir, tol_v=2.0, tol_h=2.0):
    C, L, man, plans = layout.build()
    sw, sh = L["slide_w"], L["slide_h"]
    probs = []
    print("page | lines | maxdTop maxdBot | maxdLeft maxdRight | elemsPresent | worst")
    for p in plans:
        png = os.path.join(render_dir, "page-%04d.png" % p["n"])
        g, K = load_gray(png, sw)
        W, H = g.size
        px = g.load()
        dts, dbs, dls, drs = [], [], [], []
        nline = 0
        for ln in p["lines"]:
            nline += 1
            x0, x1 = ln["left"], ln["right"]
            y0 = ln["base"] - ln["A"]
            y1 = ln["base"] + ln["D"]
            # exact y-band, full slide width: no contamination from neighbouring lines
            got = ink_bbox(px, K, W, H, 0.0, y0, sw, y1)
            if got is None:
                probs.append("slide %d line@%.1f MISSING" % (p["n"], ln["base"]))
                continue
            gv = ink_bbox(px, K, W, H, x0 + 0.2, y0, x1 - 0.2, y1)
            if gv:
                dts.append(gv[1] - y0)
                dbs.append(gv[3] - y1)
            dls.append(got[0] - x0)
            drs.append(got[2] - x1)
        # every placed element must have ink where it sits
        missing = 0
        for t in p["texts"]:
            up, dn, ix0, ix1 = metrics.ink(t["s"], t["size"], t["bold"])
            adv = metrics.advance(t["s"], t["size"], t["bold"])
            if ink_bbox(px, K, W, H, t["x"], t["base"] - up - 3, t["x"] + adv,
                        t["base"] + dn + 3) is None:
                missing += 1
                probs.append("slide %d text %r has no ink" % (p["n"], t["s"][:12]))
        for m in p["math"]:
            md = man[m["name"]]
            if ink_bbox(px, K, W, H, m["x"], m["base"] - md["ht_disp"] - 3,
                        m["x"] + md["wd_disp"], m["base"] + md["dp_disp"] + 3) is None:
                missing += 1
                probs.append("slide %d math %s has no ink" % (p["n"], m["name"]))
        # blank area must be untouched
        ink = ink_bbox(px, K, W, H, 0, 0, sw, sh)
        if ink and ink[3] > p["content_bottom"] + 2.0:
            probs.append("slide %d ink below planned bottom: %.2f > %.2f"
                         % (p["n"], ink[3], p["content_bottom"]))
        if ink and ink[2] > sw - L["margin_r"] + 4:
            probs.append("slide %d ink past right margin: %.2f" % (p["n"], ink[2]))
        mt, mb = max(map(abs, dts or [0])), max(map(abs, dbs or [0]))
        ml, mr = max(map(abs, dls or [0])), max(map(abs, drs or [0]))
        print("%4d | %5d | %6.2f %6.2f | %7.2f %8.2f | %d/%d | %s"
              % (p["n"], nline, mt, mb, ml, mr,
                 len(p["texts"]) + len(p["math"]) - missing,
                 len(p["texts"]) + len(p["math"]),
                 "%.2f" % max(mt, mb, ml, mr) if probs else "-"))
        for d in dts:
            if abs(d) > tol_v:
                probs.append("slide %d ink top off by %+.2f" % (p["n"], d))
        for d in dbs:
            if abs(d) > tol_v:
                probs.append("slide %d ink bottom off by %+.2f" % (p["n"], d))
        for ln, dl, dr in zip(p["lines"], dls, drs):
            # ink may start later than the pen origin (left side bearing) but must
            # never start before it, and must never pass the planned pen end.
            if dl < -1.0 or dl > 8.0:
                probs.append("slide %d line@%.1f ink left %+.2f vs plan" % (p["n"], ln["base"], dl))
            if dr > 1.0:
                probs.append("slide %d line@%.1f ink right %+.2f past plan" % (p["n"], ln["base"], dr))
            if ln["right"] + dr > sw - L["margin_r"] + 0.5:
                probs.append("slide %d line@%.1f crosses right margin (%.2f)"
                             % (p["n"], ln["base"], ln["right"] + dr))
    print("\nproblems: %d" % len(probs))
    for x in probs:
        print("   " + x)
    return 1 if probs else 0


if __name__ == "__main__":
    d = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "render1")
    sys.exit(main(d))
