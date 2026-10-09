# -*- coding: utf-8 -*-
import os
import numpy as np
from PIL import Image
from lxml import etree
import zipfile
WS = r"C:\Users\lihao\Desktop\家教\高三数学\10.8"
OUT = os.path.join(WS, "_acc_check")
L = []
def w(*a): L.append(" ".join(str(x) for x in a))

w("=== master background ===")
z = zipfile.ZipFile(os.path.join(WS, "集合专题_课堂板书版.pptx"))
P = "http://schemas.openxmlformats.org/presentationml/2006/main"
master = etree.fromstring(z.read("ppt/slideMasters/slideMaster1.xml"))
bg = master.find(f".//{{{P}}}bg")
w(etree.tostring(bg, encoding="unicode", pretty_print=True) if bg is not None else "no bg")

w("\n=== A. pdfcheck (from DELIVERED PDF) lower-ink vs prev2 (from DELIVERED PPTX) ===")
H_PT = 540.0
for tag, d, npages in [("prev2 (pptx 200dpi)", "prev2", 9), ("pdfcheck (pdf 150dpi)", "pdfcheck", 9)]:
    w(f"\n--- {tag} ---")
    for pg in range(2, npages+1):
        p = os.path.join(WS, "_build_sets", d, f"page-{pg:04d}.png")
        im = Image.open(p).convert("RGB")
        W, H = im.size
        a = np.asarray(im).astype(np.int16)
        g = a.mean(axis=2)
        M = 6
        crop = g[M:H-M, M:W-M]
        ink = crop < 250
        rows = np.where(ink.any(axis=1))[0]
        bot = rows.max() + M
        botpt = (bot+1)/H*H_PT
        blank = (H_PT-botpt)/H_PT*100
        lower = np.argwhere(g[int(H*0.65):H-M, M:W-M] < 250)
        w(f"  page{pg}: {W}x{H}  bottom ink y={bot}px = {botpt:.1f}pt  lower-blank={blank:.2f}%  "
          f"nonwhite-below-65%={len(lower)}")

w("\n=== B. cover page (page 1) ink geometry ===")
for tag, d in [("prev2", "prev2"), ("pdfcheck", "pdfcheck")]:
    im = Image.open(os.path.join(WS, "_build_sets", d, "page-0001.png")).convert("RGB")
    W, H = im.size
    g = np.asarray(im).astype(np.int16).mean(axis=2)
    M = 6
    ink = g[M:H-M, M:W-M] < 250
    rows = np.where(ink.any(axis=1))[0]; cols = np.where(ink.any(axis=0))[0]
    w(f"  {tag} page1: {W}x{H} ink rows {rows.min()+M}..{rows.max()+M}  cols {cols.min()+M}..{cols.max()+M}")
    # row bands
    rowany = ink.any(axis=1); bands=[]; i=0
    while i < len(rowany):
        if rowany[i]:
            j=i
            while j+1<len(rowany) and rowany[j+1]: j+=1
            bands.append((i+M,j+M)); i=j+1
        else: i+=1
    w(f"     bands={bands}")

open(os.path.join(OUT, "crosscheck.txt"), "w", encoding="utf-8").write("\n".join(L))
print("ok")
