import os, json
from pypdf import PdfReader
WS = r"C:\Users\lihao\Desktop\家教\高三数学\10.8"
OUT = os.path.join(WS, "_acc_check")
lines = []
def w(s=""): lines.append(str(s))

for tag, path in [("DELIVERED PDF", os.path.join(WS, "集合专题_课堂板书版.pdf")),
                  ("SOURCE PDF 集合专题.pdf", os.path.join(WS, "集合专题.pdf")),
                  ("SOURCE PDF 集合答案.pdf", os.path.join(WS, "集合答案.pdf"))]:
    r = PdfReader(path)
    w(f"\n===== {tag} : {path}")
    w(f"pages = {len(r.pages)}")
    p0 = r.pages[0]
    w(f"page0 mediabox = {p0.mediabox}  (w={float(p0.mediabox.width):.2f}pt h={float(p0.mediabox.height):.2f}pt)")
    for i, pg in enumerate(r.pages[:9], 1):
        w(f"  page{i}: mediabox={pg.mediabox}  rotate={pg.get('/Rotate')}")
    # extract text of delivered pdf
    if tag == "DELIVERED PDF":
        w("\n--- DELIVERED PDF text per page ---")
        for i, pg in enumerate(r.pages, 1):
            t = pg.extract_text() or ""
            w(f"\n>>> page {i}: {t!r}")
        # count images per page
        w("\n--- DELIVERED PDF XObject counts per page ---")
        for i, pg in enumerate(r.pages, 1):
            res = pg.get("/Resources")
            xo = res.get("/XObject") if res else None
            n = 0
            if xo:
                try:
                    xo = xo.get_object()
                    n = len(xo)
                except Exception:
                    n = -1
            w(f"  page{i}: xobjects={n}")

open(os.path.join(OUT, "pdf_probe.txt"), "w", encoding="utf-8").write("\n".join(lines))
print("ok")
