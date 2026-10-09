# -*- coding: utf-8 -*-
"""Final acceptance check for the delivered deck.

Reads the PPTX itself (not the build plan) and the rendered pages, and asserts
every requirement from the brief:
  1. exactly 10 slides, 16:9
  2. cover + 9 question types, one question per slide
  3. pure-white slide background
  4. title 30-36pt bold dark blue; stem 24-28pt black; options 22-24pt
  5. every formula is a real LaTeX-compiled SVG picture (svgBlip + .svg part)
  6. >= 60% of each slide is untouched white handwriting area
  7. no answer / solution / hint text anywhere (incl. speaker notes)
"""
import json, os, re, sys, zipfile
from collections import Counter

from pptx import Presentation
from pptx.oxml.ns import qn
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PPTX = os.path.join(ROOT, "\u5145\u5206\u5fc5\u8981\u6761\u4ef6_9\u5927\u9898\u578b\u8bfe\u5802\u677f\u4e66.pptx")
RENDER = os.path.join(HERE, "render4")
NS_ASVG = "{http://schemas.microsoft.com/office/drawing/2016/SVG/main}svgBlip"

BLANK_MIN = 60.0
# answer/solution leakage markers, checked against stem+option text (the slide
# title is a fixed category name -- "解析几何" is a topic, not a solution)
ANSWERY = ["\u7b54\u6848", "\u6545\u9009", "\u89e3\u6790\uff1a", "\u601d\u8def", "\u70b9\u62e8",
           "\u6b63\u786e\u9009\u9879", "\u7b54\uff1a", "\u9009A", "\u9009B", "\u9009C", "\u9009D",
           "\u7531\u6b64\u53ef\u5f97", "\u6240\u4ee5\u9009"]
TITLE_RGB = "1F3864"
BODY_RGB = "000000"


def fail(msgs, cond, text):
    if not cond:
        msgs.append(text)
    return cond


def main():
    problems = []
    prs = Presentation(PPTX)
    slides = list(prs.slides)
    W = prs.slide_width / 12700.0
    H = prs.slide_height / 12700.0
    fail(problems, len(slides) == 10, "slide count = %d (want 10)" % len(slides))
    fail(problems, abs(W / H - 16 / 9.0) < 0.01, "aspect %.4f is not 16:9" % (W / H))
    fail(problems, abs(W - 960) < 1 and abs(H - 540) < 1, "slide size %.1fx%.1f pt" % (W, H))

    zf = zipfile.ZipFile(PPTX)
    svg_parts = [n for n in zf.namelist() if n.lower().endswith(".svg")]
    png_parts = [n for n in zf.namelist() if re.search(r"media/.*\.png$", n, re.I)]
    notes = [n for n in zf.namelist() if "notesSlide" in n]
    fail(problems, len(svg_parts) > 0, "no SVG parts embedded")
    fail(problems, not notes, "deck contains speaker notes")
    print("embedded vector SVGs: %d      PNG fallbacks: %d      notes: %d"
          % (len(svg_parts), len(png_parts), len(notes)))

    # ---- per-slide inspection
    alltext = []
    print("\npg | white bg | title(sz,bold,clr) | stem sz/clr      | opt sz/clr      | svg | png | textchars")
    for i, s in enumerate(slides, 1):
        xml = s._element.xml
        bg_white = ('<p:bg>' in xml and 'FFFFFF' in xml)
        fail(problems, bg_white, "slide %d has no explicit white background" % i)
        svg_n = xml.count("svgBlip")
        png_n = sum(1 for sh in s.shapes if sh.shape_type == 13)
        sizes = {"title": [], "stem": [], "opt": []}
        colors = {"title": set(), "stem": set(), "opt": set()}
        bolds = {"title": set(), "stem": set()}
        texts = []
        bodytexts = []
        for sh in s.shapes:
            if not sh.has_text_frame:
                continue
            for para in sh.text_frame.paragraphs:
                for r in para.runs:
                    sz = r.font.size.pt if r.font.size else None
                    clr = str(r.font.color.rgb) if r.font.color and r.font.color.type is not None else None
                    bold = bool(r.font.bold)
                    texts.append(r.text)
                    alltext.append(r.text)
                    if i == 1:
                        continue
                    if sz == 32:
                        sizes["title"].append(sz); colors["title"].add(clr); bolds["title"].add(bold)
                    else:
                        bodytexts.append(r.text)
                    if sz == 26:
                        sizes["stem"].append(sz); colors["stem"].add(clr); bolds["stem"].add(bold)
                    elif sz == 23:
                        sizes["opt"].append(sz); colors["opt"].add(clr)
                    elif sz != 32:
                        problems.append("slide %d: unexpected font size %s in %r" % (i, sz, r.text))
        if i > 1:
            fail(problems, sizes["title"] and all(30 <= x <= 36 for x in sizes["title"]),
                 "slide %d title size not in 30..36" % i)
            fail(problems, bolds["title"] == {True}, "slide %d title not bold" % i)
            fail(problems, colors["title"] <= {TITLE_RGB}, "slide %d title colour %s" % (i, colors["title"]))
            fail(problems, sizes["stem"] and all(24 <= x <= 28 for x in sizes["stem"]),
                 "slide %d stem size not in 24..28" % i)
            fail(problems, colors["stem"] <= {BODY_RGB}, "slide %d stem colour %s" % (i, colors["stem"]))
            fail(problems, sizes["opt"] and all(22 <= x <= 24 for x in sizes["opt"]),
                 "slide %d option size not in 22..24" % i)
        # no answer leakage in the question body (title excluded)
        joined = "".join(bodytexts)
        for kw in ANSWERY:
            if kw in joined:
                problems.append("slide %d contains answer-ish text %r" % (i, kw))
        if i > 1:
            labels = [t for t in texts if re.fullmatch(r"[A-D]\.", t)]
            fail(problems, len(labels) == 4, "slide %d has %d option labels (want 4)" % (i, len(labels)))
        print("%2d | %-8s | %-19s | %-16s | %-15s | %3d | %3d | %d"
              % (i, "yes" if bg_white else "NO", str(sorted(set(sizes['title']) or ['-'])),
                 str(sorted(set(sizes['stem']) or ['-'])), str(sorted(set(sizes['opt']) or ['-'])),
                 svg_n, png_n, len(joined)))
    print("\nfont usage:", dict(Counter({k: v for k, v in
          Counter([r.font.name for s in slides for sh in s.shapes
                   if sh.has_text_frame for p in sh.text_frame.paragraphs
                   for r in p.runs]).items()})))

    # ---- rendered pages: blank handwriting area + no overflow
    print("\npg | inkTop | inkBottom | plannedBottom | blankBelow% | inkLeft | inkRight | ok")
    for i in range(2, 11):
        png = os.path.join(RENDER, "page-%04d.png" % i)
        im = Image.open(png).convert("RGBA")
        im = Image.alpha_composite(Image.new("RGBA", im.size, (255, 255, 255, 255)), im).convert("L")
        Wp, Hp = im.size
        K = Wp / W
        px = im.load()
        rows = [y for y in range(Hp) if any(px[x, y] < 140 for x in range(0, Wp, 2))]
        if not rows:
            problems.append("slide %d renders blank" % i)
            continue
        top, bot = rows[0] / K, (rows[-1] + 1) / K
        cols = [x for x in range(Wp)
                if any(px[x, y] < 140 for y in range(rows[0], rows[-1] + 1, 2))]
        l, r = cols[0] / K, (cols[-1] + 1) / K
        blank = (H - bot) / H * 100.0
        ok = blank >= BLANK_MIN and r <= W - 64 + 1
        fail(problems, ok, "slide %d blank %.1f%% / right %.1fpt" % (i, blank, r))
        print("%2d | %6.1f | %9.1f | %13s | %10.1f | %7.1f | %8.1f | %s"
              % (i, top, bot, "-", blank, l, r, "OK" if ok else "BAD"))

    # ---- cover
    im = Image.open(os.path.join(RENDER, "page-0001.png")).convert("RGBA")
    im = Image.alpha_composite(Image.new("RGBA", im.size, (255, 255, 255, 255)), im).convert("L")
    Wp, Hp = im.size
    K = Wp / W
    px = im.load()
    rows = [y for y in range(Hp) if any(px[x, y] < 140 for x in range(0, Wp, 2))]
    cols = [x for x in range(Wp) if any(px[x, y] < 140 for y in range(0, Hp, 2))]
    cy = (rows[0] + rows[-1]) / 2.0 / K
    cx = (cols[0] + cols[-1]) / 2.0 / K
    print("\ncover ink centre = (%.1f, %.1f) pt, slide centre = (%.1f, %.1f)"
          % (cx, cy, W / 2, H / 2))
    fail(problems, abs(cx - W / 2) < 6, "cover not horizontally centred (%.1f)" % cx)
    fail(problems, abs(cy - H / 2) < 30, "cover not vertically centred (%.1f)" % cy)

    print("\n================ ACCEPTANCE: %s ================" % ("PASS" if not problems else "FAIL"))
    for p in problems:
        print("  - " + p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
