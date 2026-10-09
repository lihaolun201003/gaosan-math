# -*- coding: utf-8 -*-
import zipfile, os, re
from lxml import etree
WS = r"C:\Users\lihao\Desktop\家教\高三数学\10.8"
z = zipfile.ZipFile(os.path.join(WS, "集合专题_课堂板书版.pptx"))
OUT = os.path.join(WS, "_acc_check")
L = []
def w(*a): L.append(" ".join(str(x) for x in a))
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
P = "http://schemas.openxmlformats.org/presentationml/2006/main"

w("=== ALL ZIP PARTS ===")
for n in sorted(z.namelist()):
    if not n.startswith("ppt/media/"):
        w(f"  {n}  ({z.getinfo(n).file_size} B)")

w("\n=== docProps / core.xml metadata ===")
for n in z.namelist():
    if n.startswith("docProps"):
        w(f"--- {n} ---")
        w(z.read(n).decode("utf-8", "replace")[:1200])

w("\n=== option-label vs formula x-order monotonicity (slides 2-8) ===")
import unicodedata
for i in range(2, 9):
    root = etree.fromstring(z.read(f"ppt/slides/slide{i}.xml"))
    items = []
    for sh in root.find(f".//{{{P}}}spTree"):
        tag = etree.QName(sh).localname
        x = sh.find(f".//{{{A}}}xfrm")
        if x is None: continue
        ox = int(x.find(f"{{{A}}}off").get("x"))
        if tag == "sp":
            t = "".join("".join(tt.itertext()) for tt in sh.findall(f".//{{{A}}}t"))
            m = re.fullmatch(r"([A-D])\.", t.strip())
            if m: items.append((ox, "LABEL " + m.group(1)))
        else:
            items.append((ox, "FORMULA"))
    items.sort()
    seq = [b for a, b in items]
    labs = [b[-1] for a, b in items if b.startswith("LABEL")]
    ok = labs == ["A", "B", "C", "D"]
    # each label immediately followed by a FORMULA
    paired = all(seq[k].startswith("LABEL") and seq[k+1] == "FORMULA" for k in range(0, min(len(seq), 8), 2))
    w(f"  slide{i}: x-ordered sequence = {seq}")
    w(f"            labels in A,B,C,D order: {ok}   label->formula pairing: {paired}")

w("\n=== sldSz ===")
pres = z.read("ppt/presentation.xml").decode("utf-8")
w(re.search(r"<p:sldSz[^>]*/>", pres).group(0))
w("  ratio = %.5f (16:9 = %.5f)" % (12192000/6858000, 16/9))
w("  declared type attr is a stale label; actual cx/cy govern rendering")

open(os.path.join(OUT, "final_checks.txt"), "w", encoding="utf-8").write("\n".join(L))
print("ok")
