import os, re
WS = r"C:\Users\lihao\Desktop\家教\高三数学\10.8"
OUT = os.path.join(WS, "_acc_check")
import pypdfium2 as pdfium
L = []
def w(*a): L.append(" ".join(str(x) for x in a))

doc = pdfium.PdfDocument(os.path.join(WS, "集合答案.pdf"))
w("集合答案.pdf pages:", len(doc))
pageheads = {}
for i in range(len(doc)):
    t = doc[i].get_textpage().get_text_range()
    heads = re.findall(r"第\s*(\d+)\s*题", t)
    pageheads[i+1] = heads
    w(f"  page {i+1:2d}: 第N题 headers = {heads}")

targets = [13, 7, 34, 9, 27, 126, 24, 148]
w("\n=== pages containing target headers ===")
for n in targets:
    pgs = [p for p, hh in pageheads.items() if str(n) in hh]
    w(f"  Q{n}: pages {pgs}")

# stems
stems = {
 13: ["M = {1, 3, 6}"],
 7:  ["{−1, 1, 2, 4}"],
 34: ["− 2 < x < 2}，B = {x| − 1"],
 9:  ["log2 x < 1"],
 27: ["x2 − 4x"],
 126:["y = 2x − 1"],
 24: ["U = {1, 2, 3, 4}"],
 148:["x2 + y 2"],
}
w("\n=== stem search in answers PDF (page, snippet) ===")
for n, ss in stems.items():
    hit = []
    for i in range(len(doc)):
        t = doc[i].get_textpage().get_text_range()
        for s in ss:
            if s in t:
                hit.append((i+1, s))
    w(f"  Q{n} stems={ss} -> pages {hit}")
open(os.path.join(OUT, "anspdf_pages.txt"), "w", encoding="utf-8").write("\n".join(L))
print("ok")
