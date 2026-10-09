# -*- coding: utf-8 -*-
"""Validate PIL-derived metrics (advance + ink bbox at baseline anchor) against
the measured LibreOffice render of calib2.  Establishes the text layout model."""
from PIL import ImageFont

PX = 400  # render size for precision
REG = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", PX, index=0)
BLD = ImageFont.truetype(r"C:\Windows\Fonts\msyhbd.ttc", PX, index=0)

def met(text, size, bold=False):
    f = BLD if bold else REG
    adv = f.getlength(text) / PX * size
    bb = f.getbbox(text, anchor="ls")          # relative to baseline origin
    return adv, (bb[0] / PX * size, bb[1] / PX * size, bb[2] / PX * size, bb[3] / PX * size)

print("PIL getmetrics @400:", REG.getmetrics(), BLD.getmetrics())
print()
print("%-14s %5s | %8s | %-32s" % ("text", "size", "advance", "ink bbox (x0,y0,x1,y1) rel baseline"))
for text, size, bold in [("国", 26, False), ("国", 23, False), ("国", 32, True),
                         ("Hxg", 26, False), ("A.", 23, False), ("国Hxg国", 26, False)]:
    adv, bb = met(text, size, bold)
    print("%-14r %5d | %8.3f | (%7.3f,%7.3f,%7.3f,%7.3f)  inkW=%7.3f" %
          (text, size, adv, bb[0], bb[1], bb[2], bb[3], bb[2] - bb[0]))

print()
print("=== compare with measured render (baseline = box_top + size) ===")
meas = {  # name: (size, inkTop_above_baseline, inkBot_below_baseline, inkWidth)
    "C26":  (26, 26.0 - 5.829,  29.103 - 26.0, 22.835),
    "C23":  (23, 23.0 - 5.009,  25.644 - 23.0, 20.435),
    "C32B": (32, 32.0 - 6.828,  35.621 - 32.0, 28.833),
    "L26":  (26, 26.0 - 6.488,  32.162 - 26.0, 45.629),
    "L23":  (23, 23.0 - 5.669,  22.944 - 23.0, 20.675),
    "M26":  (26, 26.0 - 5.809,  32.202 - 26.0, 111.132),
}
cases = {"C26": ("国", 26, False), "C23": ("国", 23, False), "C32B": ("国", 32, True),
         "L26": ("Hxg", 26, False), "L23": ("A.", 23, False), "M26": ("国Hxg国", 26, False)}
for k, (text, size, bold) in cases.items():
    adv, bb = met(text, size, bold)
    m_up, m_dn, m_w = meas[k][1], meas[k][2], meas[k][3]
    p_up, p_dn, p_w = -bb[1], bb[3], bb[2] - bb[0]
    print("%-5s %-8r  up: PIL %7.3f vs meas %7.3f (%+.3f) | dn: PIL %7.3f vs meas %7.3f (%+.3f) "
          "| W: PIL %7.3f vs meas %7.3f (%+.3f)"
          % (k, text, p_up, m_up, p_up - m_up, p_dn, m_dn, p_dn - m_dn, p_w, m_w, p_w - m_w))
