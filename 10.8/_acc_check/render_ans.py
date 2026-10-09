import os, re
WS = r"C:\Users\lihao\Desktop\家教\高三数学\10.8"
OUT = os.path.join(WS, "_acc_check", "anspages")
os.makedirs(OUT, exist_ok=True)
import pypdfium2 as pdfium
from PIL import Image

doc = pdfium.PdfDocument(os.path.join(WS, "集合答案.pdf"))
pages = [4, 5, 6, 9, 10, 13, 44, 51, 56]
info = []
for p in pages:
    pg = doc[p-1]
    tp = pg.get_textpage()
    txt = tp.get_text_range()
    # find y of 参考答案 occurrences on the page
    ys = []
    for m in re.finditer(r"参考答案", txt):
        ch = tp.get_charbox(m.start())
        ys.append((round(ch[1],1), round(ch[3],1), m.start()))
    info.append((p, ys, txt[:200].replace("\n"," | ")))
    bmp = pg.render(scale=150/72)
    img = bmp.to_pil()
    W, H = img.size
    # pdf points -> px factor 150/72
    f = 150/72
    for k, (y0, y1, off) in enumerate(ys):
        top = max(0, min(H-2, int((H - y1*f) - 170)))
        bot = max(top+1, min(H, int((H - y0*f) + 190)))
        crop = img.crop((0, top, W, bot))
        crop.save(os.path.join(OUT, f"ansp{p}_r{k}.png"))
    # also 3 vertical strips for full-page reading
    for s in range(3):
        t = int(H*s/3); b = min(H, int(H*(s+1)/3)+20)
        img.crop((0, t, W, b)).save(os.path.join(OUT, f"ansp{p}_strip{s}.png"))
    img.save(os.path.join(OUT, f"ansp{p}_full.png"))
    print(f"page {p}: size={W}x{H} 参考答案-count={len(ys)}")

with open(os.path.join(WS, "_acc_check", "anspage_info.txt"), "w", encoding="utf-8") as f:
    for p, ys, head in info:
        f.write(f"page {p}: 参考答案 boxes={ys}\n  head: {head}\n")
print("ok")
