import os, json
from PIL import Image
import numpy as np

WS = r"C:\Users\lihao\Desktop\家教\高三数学\10.8"
PREV = os.path.join(WS, "_build_sets", "prev2")
OUT = os.path.join(WS, "_acc_check")
lines = []
def w(s=""): lines.append(str(s))

w("=== prev2/manifest.json ===")
w(open(os.path.join(PREV, "manifest.json"), encoding="utf-8").read())

SLIDE_H_PT = 540.0

for pg in range(1, 10):
    p = os.path.join(PREV, f"page-{pg:04d}.png")
    im = Image.open(p).convert("RGB")
    W, H = im.size
    a = np.asarray(im).astype(np.int16)
    # grayscale
    g = a.mean(axis=2)
    w(f"\n########## page {pg}  size={W}x{H}  px/pt = {H/SLIDE_H_PT:.5f} (vert), {W/(SLIDE_H_PT*16/9):.5f} (horiz)")
    # corner samples
    w(f"  corners: TL={a[0,0].tolist()} TR={a[0,W-1].tolist()} BL={a[H-1,0].tolist()} BR={a[H-1,W-1].tolist()}")
    w(f"  row0 unique={np.unique(a[0].reshape(-1,3),axis=0)[:6].tolist()}")
    w(f"  row1 unique={np.unique(a[1].reshape(-1,3),axis=0)[:6].tolist()}")
    # border profiling: mean gray of first/last rows & cols
    w(f"  mean gray row0={g[0].mean():.1f} row1={g[1].mean():.1f} row2={g[2].mean():.1f} row3={g[3].mean():.1f} row4={g[4].mean():.1f} row5={g[5].mean():.1f}")
    w(f"  mean gray col0={g[:,0].mean():.1f} col1={g[:,1].mean():.1f} col2={g[:,2].mean():.1f} col5={g[:,5].mean():.1f}")
    w(f"  mean gray rowH-1={g[H-1].mean():.1f} rowH-2={g[H-2].mean():.1f} rowH-6={g[H-6].mean():.1f}")

    MARGIN = 5
    crop = g[MARGIN:H-MARGIN, MARGIN:W-MARGIN]
    for thr in (250, 240, 200, 128):
        ink = crop < thr
        rows = np.where(ink.any(axis=1))[0]
        top = rows.min() + MARGIN if len(rows) else None
        bot = rows.max() + MARGIN if len(rows) else None
        if bot is None:
            w(f"  thr<{thr}: NO INK")
            continue
        bot_pt = (bot + 1) / H * SLIDE_H_PT
        top_pt = top / H * SLIDE_H_PT
        blank = (SLIDE_H_PT - bot_pt) / SLIDE_H_PT * 100
        w(f"  thr<{thr}: top_ink_y={top}px ({top_pt:.1f}pt)  bottom_ink_y={bot}px (bottom edge {bot_pt:.1f}pt)  lower-blank={blank:.2f}%")

    # strict: any pixel that is not pure white after margin
    nz = np.argwhere(crop < 250)
    if len(nz):
        w(f"  first non-white row (marg5)={nz[:,0].min()+MARGIN}  last non-white row={nz[:,0].max()+MARGIN}")
        w(f"  leftmost non-white col={nz[:,1].min()+MARGIN}  rightmost col={nz[:,1].max()+MARGIN}")

    # Look BELOW the main content block (gap detection) for stray marks
    ink = crop < 250
    rowany = ink.any(axis=1)
    # find contiguous ink bands
    bands = []
    i = 0
    while i < len(rowany):
        if rowany[i]:
            j = i
            while j+1 < len(rowany) and rowany[j+1]:
                j += 1
            bands.append((i+MARGIN, j+MARGIN))
            i = j+1
        else:
            i += 1
    w(f"  ink row-bands (thr250, gaps>=1px): {bands}")
    if bands:
        lastband = bands[-1]
        w(f"  LAST band ends at y={lastband[1]}  -> blank below = {(SLIDE_H_PT-(lastband[1]+1)/H*SLIDE_H_PT)/SLIDE_H_PT*100:.2f}%")
        # content below 60% of page?
        y60 = int(H*0.60)
        below = np.argwhere(g[y60:H-MARGIN, MARGIN:W-MARGIN] < 250)
        w(f"  non-white pixels in lower 40% (y>{y60}, margin {MARGIN}): {len(below)}")
        y65 = int(H*0.65)
        below65 = np.argwhere(g[y65:H-MARGIN, MARGIN:W-MARGIN] < 250)
        w(f"  non-white pixels in lower 35% (y>{y65}): {len(below65)}")
        # unique colors of stray pixels
        if len(below):
            cols = np.unique(a[y60:H-MARGIN, MARGIN:W-MARGIN].reshape(-1,3), axis=0)
            w(f"  lower-40% distinct colors (first 12): {cols[:12].tolist()}  total distinct={len(cols)}")

open(os.path.join(OUT, "whitespace.txt"), "w", encoding="utf-8").write("\n".join(lines))
print("ok")
