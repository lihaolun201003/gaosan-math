import os, re
WS = r"C:\Users\lihao\Desktop\家教\高三数学\10.8"
OUT = os.path.join(WS, "_acc_check", "glyph")
os.makedirs(OUT, exist_ok=True)
import pypdfium2 as pdfium

doc = pdfium.PdfDocument(os.path.join(WS, "集合专题.pdf"))
targets = {6: ("Q27", "∈"), 31: ("Q148", "∈")}
for p, (tag, needle) in targets.items():
    pg = doc[p-1]
    tp = pg.get_textpage()
    t = tp.get_text_range()
    print(f"--- page {p} ({tag}) ---")
    for m in re.finditer(re.escape(needle), t):
        cb = tp.get_charbox(m.start())
        nxt = t[m.start()+1:m.start()+4]
        print(f"   '∈' at idx {m.start()} box={tuple(round(x,1) for x in cb)} next={nxt!r} ord0={ord(t[m.start()+1]) if m.start()+1<len(t) else None}")
    # render page at 600 dpi and crop around each ∈
    scale = 600/72
    bmp = pg.render(scale=scale)
    img = bmp.to_pil()
    W, H = img.size
    print("   rendered:", W, H)
    k = 0
    for m in re.finditer(re.escape(needle), t):
        cb = tp.get_charbox(m.start())  # (x0, y0, x1, y1) in PDF pts, y from bottom
        x0, y0, x1, y1 = cb
        left = max(0, int((x0-10)*scale)); right = min(W, int((x1+90)*scale))
        top = max(0, int((H - (y1+22)*scale))); bot = min(H, int((H - (y0-22)*scale)))
        if bot <= top: continue
        c = img.crop((left, top, right, bot))
        c = c.resize((c.width*2, c.height*2), 1)
        c.save(os.path.join(OUT, f"p{p}_{tag}_in{k}.png"))
        print(f"   saved p{p}_{tag}_in{k}.png size={c.size}")
        k += 1
print("ok")
