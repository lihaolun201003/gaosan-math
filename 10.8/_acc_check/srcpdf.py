import os, re
WS = r"C:\Users\lihao\Desktop\家教\高三数学\10.8"
OUT = os.path.join(WS, "_acc_check")
lines_out = []
def w(*a):
    lines_out.append(" ".join(str(x) for x in a))

try:
    import pypdfium2 as pdfium
    w("pypdfium2 OK")
except Exception as e:
    w("pypdfium2 NO: %r" % (e,)); pdfium = None
try:
    import pdfplumber
    w("pdfplumber OK")
except Exception as e:
    w("pdfplumber NO: %r" % (e,)); pdfplumber = None

if pdfium:
    doc = pdfium.PdfDocument(os.path.join(WS, "集合专题.pdf"))
    w("source 集合专题.pdf pages:", len(doc))
    for i in range(len(doc)):
        t = doc[i].get_textpage().get_text_range()
        head = " / ".join([x for x in t.strip().split("\n")[:2]])[:90] if t.strip() else ""
        w(f"  page {i+1}: {head!r}")
    outdir = os.path.join(OUT, "srcpages"); os.makedirs(outdir, exist_ok=True)
    # render all pages at 200dpi for later inspection
    for i in range(len(doc)):
        pg = doc[i]
        bmp = pg.render(scale=200/72)
        img = bmp.to_pil()
        img.save(os.path.join(outdir, f"src-{i+1:02d}.png"))
    w("rendered source pages to", outdir)

    # find pages containing the 8 question numbers at line start
    targets = [13, 7, 34, 9, 27, 126, 24, 148]
    for i in range(len(doc)):
        t = doc[i].get_textpage().get_text_range()
        for n in targets:
            if re.search(rf"(?m)^\s*{n}\s*[.．、]", t):
                w(f"  Q{n} appears on source page {i+1}")

# also probe 集合答案.pdf
if pdfium:
    d2 = pdfium.PdfDocument(os.path.join(WS, "集合答案.pdf"))
    w("\n集合答案.pdf pages:", len(d2))
    for i in range(min(len(d2), 6)):
        t = d2[i].get_textpage().get_text_range()
        w(f"  page {i+1} head: {t.strip()[:200]!r}")

open(os.path.join(OUT, "srcpdf.txt"), "w", encoding="utf-8").write("\n".join(lines_out))
print("ok")
