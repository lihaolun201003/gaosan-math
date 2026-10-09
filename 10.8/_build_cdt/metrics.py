# -*- coding: utf-8 -*-
"""微软雅黑 metrics bridge: exact advance widths and ink extents (relative to baseline).

Calibrated against LibreOffice render of calib2.pptx:
  * text box (top-anchored, zero insets, word_wrap=False) baseline == box_top + font_size
  * PIL ink extents match the render within ~0.5pt
  * CJK advance == 1.000 em exactly  -> pure-CJK run width is exact
"""
from PIL import ImageFont

PX = 512                                     # design size for metric sampling
_PATH_R = r"C:\Windows\Fonts\msyh.ttc"       # 微软雅黑 Regular
_PATH_B = r"C:\Windows\Fonts\msyhbd.ttc"     # 微软雅黑 Bold

_F = {False: ImageFont.truetype(_PATH_R, PX, index=0),
      True:  ImageFont.truetype(_PATH_B, PX, index=0)}

EM_TOL = 1e-3


def _f(bold):
    return _F[bool(bold)]


def advance(text, size, bold=False):
    """Advance width in pt (what the renderer uses to move the pen)."""
    return _f(bold).getlength(text) * size / PX


def ink(text, size, bold=False):
    """(up, down, x0, x1) in pt relative to the baseline origin.

    up   : ink extent above the baseline (positive number)
    down : ink extent below the baseline (positive number)
    x0,x1: horizontal ink offsets from the pen origin
    """
    bb = _f(bold).getbbox(text, anchor="ls")
    k = size / PX
    return (-bb[1] * k, bb[3] * k, bb[0] * k, bb[2] * k)


def is_cjk(ch):
    o = ord(ch)
    return (0x3000 <= o <= 0x303F or 0x4E00 <= o <= 0x9FFF or 0xFF00 <= o <= 0xFFEF
            or 0x2014 <= o <= 0x2015 or o == 0x00B7 or o == 0x22EF)


def check_pure_cjk(text, size, bold=False):
    """Return the exact width of a run that must be laid out as N full-width ems."""
    w = 0.0
    for ch in text:
        cw = advance(ch, size, bold)
        if abs(cw - size) > EM_TOL * size:
            raise ValueError("non full-width char %r in CJK run %r (advance %.3f vs %d)"
                             % (ch, text, cw, size))
        w += cw
    return w
