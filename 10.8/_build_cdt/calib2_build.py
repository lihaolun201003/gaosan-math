# -*- coding: utf-8 -*-
"""Clean baseline calibration for 微软雅黑 in DrawingML textboxes.
Items are 80pt apart so ink bands never merge.  Renders via LibreOffice @600dpi.
"""
import os
from pptx import Presentation
from pptx.util import Pt, Emu
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn

BASE = os.path.dirname(os.path.abspath(__file__))
PT = 12700
YAHEI = "\u5fae\u8f6f\u96c5\u9ed1"      # 微软雅黑
BLACK = "000000"

# (name, box_top, size, bold, color, text)
CASES = [
    ("C26",  40, 26, False, "国"),
    ("C23", 120, 23, False, "国"),
    ("C32B",200, 32, True,  "国"),
    ("L26", 280, 26, False, "Hxg"),
    ("L23", 360, 23, False, "A."),
    ("M26", 440, 26, False, "国Hxg国"),
]

prs = Presentation()
prs.slide_width = Emu(960 * PT)
prs.slide_height = Emu(540 * PT)
s = prs.slides.add_slide(prs.slide_layouts[6])

# explicit pure-white slide background (default master is a grey gradient)
from lxml import etree
cSld = s._element.find(qn('p:cSld'))
bg = etree.SubElement(cSld, qn('p:bg'))
cSld.remove(bg)
cSld.insert(0, bg)
bgPr = etree.SubElement(bg, qn('p:bgPr'))
fill = etree.SubElement(bgPr, qn('a:solidFill'))
clr = etree.SubElement(fill, qn('a:srgbClr'))
clr.set('val', 'FFFFFF')
etree.SubElement(bgPr, qn('a:effectLst'))

for name, top, size, bold, text in CASES:
    tb = s.shapes.add_textbox(Emu(100 * PT), Emu(int(top * PT)), Emu(600 * PT), Emu(int(size * 2 * PT)))
    tf = tb.text_frame
    tf.word_wrap = False
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.TOP
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    r = p.add_run()
    r.text = text
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.name = YAHEI
    from pptx.dml.color import RGBColor
    r.font.color.rgb = RGBColor.from_string(BLACK)
    rPr = r._r.get_or_add_rPr()
    for tag in ("a:ea", "a:cs"):
        rPr.append(rPr.makeelement(qn(tag), {"typeface": YAHEI}))
    tb.name = name

out = os.path.join(BASE, "calib2.pptx")
prs.save(out)
print("saved", out)
for c in CASES:
    print("  %-6s top=%3d size=%2d bold=%d text=%r" % (c[0], c[1], c[2], c[3], c[4]))
