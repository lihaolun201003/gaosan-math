# -*- coding: utf-8 -*-
"""Build 集合专题_课堂板书版.pptx -- 9 slides, board-writing layout.

Layout contract (identical template on slides 2..9)
---------------------------------------------------
  title baseline      60 pt   (微软雅黑 Bold 32pt, dark blue #1F3864)
  stem baseline      102 pt   (宋体 25pt, black) + inline LaTeX SVG math
  option row 1       140 pt
  option row 2       176 pt   (only when the option block needs two rows)

Options go on ONE row when they fit with a >=40pt gutter, otherwise a
2-column x 2-row grid.  A stem that cannot fit one line wraps to the second
slot.  Deepest ink therefore lands near y=183 at worst, leaving >=66% of the
540pt page blank; most pages end near y=149 (>72% blank).

Every math snippet is a vector SVG produced by XeLaTeX (see mathlib.py); its
baseline is placed on the line baseline using the measured TeX box height.
Chinese text stays real, editable text, one textbox per segment.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import ImageFont
from pptx import Presentation
from pptx.enum.text import PP_ALIGN
from pptx.util import Pt

from deckkit import add_textbox, add_svg_picture, finalize_pptx
from mathlib import TEX2BP, CLASS_PT

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
OUT_PPTX = os.path.join(ROOT, "集合专题_课堂板书版.pptx")

SLIDE_W, SLIDE_H = 960.0, 540.0
MARGIN_L, MARGIN_R = 60.0, 60.0
AVAIL = SLIDE_W - MARGIN_L - MARGIN_R

# --- vertical rhythm (points from slide top) --------------------------------
TITLE_BL = 60.0
STEM_BL = 102.0
OPT1_BL = 140.0
OPT2_BL = 176.0
BLANK_LIMIT = 0.35 * SLIDE_H          # 189pt: deepest ink allowed

# --- type -------------------------------------------------------------------
TITLE_FONT = "微软雅黑"
TITLE_SIZE = 32.0
TITLE_COLOR = "1F3864"
BODY_FONT = "宋体"
BODY_SIZE = 24.0
MATH_SIZE = 24.0                      # nominal TeX size of inline math
BODY_COLOR = "000000"
GAP = 40.0                            # gutter between options on one row
LABEL_GAP = 5.0                       # gap between the "A." label and its value
COL2_X = MARGIN_L + AVAIL / 2.0

TITLE_BASELINE_EM = 1.0065            # 微软雅黑: measured baseline offset / size
BODY_BASELINE_EM = 0.9915             # 宋体:   measured baseline offset / size

SIMSUN_TTC = (r"C:\Windows\Fonts\simsun.ttc", 0)
_MEASURE_PX = 2000


class Ctx(object):
    def __init__(self, manifest):
        self.man = manifest
        self.font = ImageFont.truetype(SIMSUN_TTC[0], _MEASURE_PX, index=SIMSUN_TTC[1])
        self.report = []
        self.pages = []

    def text_w(self, text, size):
        return self.font.getlength(text) / _MEASURE_PX * size

    def math_geom(self, key, size):
        v = self.man[key]
        s = size / CLASS_PT
        return (v["wd_pt"] * s * TEX2BP,
                (v["ht_pt"] + v["dp_pt"]) * s * TEX2BP,
                v["ht_pt"] * s * TEX2BP)

    def seg_w(self, seg, size):
        kind, val = seg
        if kind == "gap":
            return val
        if kind == "t":
            return self.text_w(val, size)
        if kind == "m":
            return self.math_geom(val, size)[0]
        raise ValueError(kind)

    def line_w(self, segs, size=None):
        size = BODY_SIZE if size is None else size
        return sum(self.seg_w(s, size) for s in segs)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def wrap_segments(ctx, segs, limit):
    """Greedily wrap a segment list into lines that each fit `limit`."""
    lines, cur = [], []
    for seg in segs:
        trial = cur + [seg]
        if cur and ctx.line_w(trial) > limit:
            lines.append(cur)
            cur = [seg]
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def option_label(i):
    """Option label as in the source paper style, rendered as editable text."""
    return [("t", "ABCD"[i] + "."), ("gap", LABEL_GAP)]


def option_layout(ctx, keys):
    """Return [(row_slot, col_x, segments), ...].

    One row of four when it fits with a >=GAP gutter, otherwise a 2-column by
    2-row grid (A B / C D) so the options never crowd each other.
    """
    one = []
    for i, k in enumerate(keys):
        if i:
            one.append(("gap", GAP))
        one.extend(option_label(i))
        one.append(("m", k))
    if ctx.line_w(one) <= AVAIL:
        return [(0, MARGIN_L, one)]

    half = AVAIL / 2.0
    out = []
    for slot, pair in enumerate(((0, 1), (2, 3))):
        for col, i in enumerate(pair):
            segs = option_label(i) + [("m", keys[i])]
            ctx.report.append(("opt-cell-%s" % "ABCD"[i],
                               round(ctx.line_w(segs), 2), round(half, 2),
                               ctx.line_w(segs) <= half, -1))
            out.append((slot, MARGIN_L + col * half, segs))
    return out


def draw_line(ctx, slide, segs, baseline, col_x, tag, limit=AVAIL):
    x = col_x
    for seg in segs:
        kind, val = seg
        if kind == "gap":
            x += val
            continue
        if kind == "t":
            w = ctx.text_w(val, BODY_SIZE)
            add_textbox(slide, x, baseline - BODY_BASELINE_EM * BODY_SIZE,
                        w + 4.0, BODY_SIZE * 2.0, val, BODY_FONT, BODY_SIZE,
                        color=BODY_COLOR)
            x += w
        else:
            w, h, asc = ctx.math_geom(val, MATH_SIZE)
            add_svg_picture(slide,
                            os.path.join(BASE, ctx.man[val]["svg"]),
                            os.path.join(BASE, ctx.man[val]["png"]),
                            x, baseline - asc, w, h,
                            alt="$%s$" % ctx.man[val]["math"])
            x += w
    used = x - col_x
    ctx.report.append((tag, round(used, 2), round(limit, 2), used <= limit + 0.01,
                       round(baseline, 1)))
    return used


# ---------------------------------------------------------------------------
# content -- every problem copied verbatim from 集合专题.pdf
# ---------------------------------------------------------------------------
PAGES = [
    dict(  # slide 2 -- PDF #13
        title="题型一　集合的基本运算",
        stem=[("t", "已知集合 "), ("m", "p2_M"), ("t", "，"), ("m", "p2_N"),
              ("t", "，则 "), ("m", "p2_cap"), ("t", "（　）")],
        opts=["p2_oA", "p2_oB", "p2_oC", "p2_oD"],
    ),
    dict(  # slide 3 -- PDF #7
        title="题型二　不等式与集合运算",
        stem=[("t", "已知集合 "), ("m", "p3_A"), ("t", "，"), ("m", "p3_B"),
              ("t", "，则 "), ("m", "p3_cap"), ("t", "（　）")],
        opts=["p3_oA", "p3_oB", "p3_oC", "p3_oD"],
    ),
    dict(  # slide 4 -- PDF #34
        title="题型三　区间型集合运算",
        stem=[("t", "已知集合 "), ("m", "p4_A"), ("t", "，"), ("m", "p4_B"),
              ("t", "，则 "), ("m", "p4_cup"), ("t", "（　）")],
        opts=["p4_oA", "p4_oB", "p4_oC", "p4_oD"],
    ),
    dict(  # slide 5 -- PDF #9
        title="题型四　函数定义域与值域型集合",
        stem=[("t", "已知集合 "), ("m", "p5_A"), ("t", "，"), ("m", "p5_B"),
              ("t", "，则 "), ("m", "p5_cap"), ("t", "（　）")],
        opts=["p5_oA", "p5_oB", "p5_oC", "p5_oD"],
    ),
    dict(  # slide 6 -- PDF #27
        title="题型五　特殊数集与列举法",
        stem=[("t", "已知集合 "), ("m", "p6_A"), ("t", "，"), ("m", "p6_B"),
              ("t", "，则 "), ("m", "p6_cap"), ("t", "（　）")],
        opts=["p6_oA", "p6_oB", "p6_oC", "p6_oD"],
    ),
    dict(  # slide 7 -- PDF #126
        title="题型六　根据关系生成新集合",
        stem=[("t", "已知集合 "), ("m", "p7_A"), ("t", "，"), ("m", "p7_B"),
              ("t", "，则 "), ("m", "p7_cap"), ("t", "（　）")],
        opts=["p7_oA", "p7_oB", "p7_oC", "p7_oD"],
    ),
    dict(  # slide 8 -- PDF #24
        title="题型七　集合关系与元素个数",
        stem=[("t", "已知集合 "), ("m", "p8_U"), ("t", "，若集合 "), ("m", "p8_AB"),
              ("t", " 满足 "), ("m", "p8_sub"), ("t", "，")],
        stem2=[("t", "则集合对 "), ("m", "p8_pair"), ("t", " 共有（　）个．")],
        opts=["p8_oA", "p8_oB", "p8_oC", "p8_oD"],
    ),
    dict(  # slide 9 -- PDF #148
        title="题型八　特殊元素与几何计数",
        stem=[("t", "已知集合 "), ("m", "p9_U"), ("t", "，")],
        stem2=[("t", "则集合 "), ("m", "p9_U2"), ("t", " 中的元素个数为 "),
               ("m", "p9_blank"), ("t", "．")],
        opts=None,
    ),
]


# ---------------------------------------------------------------------------
def build():
    with open(os.path.join(BASE, "manifest.json"), encoding="utf-8") as fh:
        manifest = json.load(fh)
    ctx = Ctx(manifest)

    prs = Presentation()
    prs.slide_width = Pt(SLIDE_W)
    prs.slide_height = Pt(SLIDE_H)
    blank = prs.slide_layouts[6]

    # ---------------- slide 1: cover -------------------------------------
    s = prs.slides.add_slide(blank)
    add_textbox(s, 120.0, 250.0 - TITLE_BASELINE_EM * 54.0, 720.0, 96.0,
                "高三数学专题复习", TITLE_FONT, 54.0, bold=True,
                color=TITLE_COLOR, align=PP_ALIGN.CENTER)
    add_textbox(s, 120.0, 322.0 - TITLE_BASELINE_EM * 30.0, 720.0, 60.0,
                "集合——八大典型题型", TITLE_FONT, 30.0, bold=False,
                color="2E5496", align=PP_ALIGN.CENTER)

    # ---------------- slides 2..9 ----------------------------------------
    for page in PAGES:
        s = prs.slides.add_slide(blank)
        tag = page["title"].split("　")[0]
        add_textbox(s, MARGIN_L, TITLE_BL - TITLE_BASELINE_EM * TITLE_SIZE,
                    720.0, TITLE_SIZE * 1.8, page["title"], TITLE_FONT,
                    TITLE_SIZE, bold=True, color=TITLE_COLOR)

        slots = [STEM_BL, OPT1_BL, OPT2_BL, OPT2_BL + 36.0, OPT2_BL + 72.0]
        used_slots = 0

        stems = wrap_segments(ctx, page["stem"], AVAIL)
        if page.get("stem2"):
            stems = stems + [page["stem2"]]
        for i, ln in enumerate(stems):
            draw_line(ctx, s, ln, slots[i], MARGIN_L, "%s/stem%d" % (tag, i + 1))
        used_slots = len(stems)

        if page.get("opts"):
            layout = option_layout(ctx, page["opts"])
            rows_used = max(r for r, _c, _s in layout) + 1
            for row, col_x, segs in layout:
                draw_line(ctx, s, segs, slots[used_slots + row], col_x,
                          "%s/opt%d" % (tag, used_slots + row + 1))
            used_slots += rows_used
        deepest = slots[used_slots - 1]
        ctx.pages.append((tag, deepest))

    prs.save(OUT_PPTX)
    info = finalize_pptx(OUT_PPTX, "Times New Roman", BODY_FONT,
                         slide_count=1 + len(PAGES),
                         title="高三数学专题复习 集合——八大典型题型",
                         author="数学备课",
                         subject="高三数学·集合专题课堂板书课件（9 页）")
    print("finalized:", info)

    # ---------------- diagnostics ----------------------------------------
    print("%-14s %10s %10s %6s %7s" % ("line", "used(pt)", "avail(pt)", "fit", "bl(pt)"))
    bad = 0
    for tag, used, avail, ok, bl in ctx.report:
        if not ok:
            bad += 1
        print("%-14s %10.2f %10.2f %6s %7.1f"
              % (tag, used, avail, "OK" if ok else "OVERFLOW", bl))
    print("overflowing lines:", bad)
    print("\n%-8s %10s %10s %8s" % ("page", "last BL", "ink bottom", "blank%"))
    worst = 1.0
    for tag, bl in ctx.pages:
        bottom = bl + 6.6                      # deepest math descender at 25pt
        blank = (SLIDE_H - bottom) / SLIDE_H
        worst = min(worst, blank)
        flag = "" if bottom <= BLANK_LIMIT else "   <-- EXCEEDS 35%"
        print("%-8s %10.1f %10.1f %7.1f%%%s" % (tag, bl, bottom, blank * 100, flag))
    print("worst blank area: %.1f%%  (requirement >= 65%%)" % (worst * 100))
    if worst < 0.65:
        bad += 1
    print("wrote", OUT_PPTX, os.path.getsize(OUT_PPTX), "bytes")
    return bad


if __name__ == "__main__":
    sys.exit(1 if build() else 0)
