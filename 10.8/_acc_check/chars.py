import os, re, unicodedata
WS = r"C:\Users\lihao\Desktop\家教\高三数学\10.8"
OUT = os.path.join(WS, "_acc_check")
import pypdfium2 as pdfium
L = []
def w(*a): L.append(" ".join(str(x) for x in a))

doc = pdfium.PdfDocument(os.path.join(WS, "集合答案.pdf"))
want = {10: "Q27", 51: "Q148", 6: "Q13", 4: "Q7"}
for p, tag in want.items():
    t = doc[p-1].get_textpage().get_text_range()
    w(f"\n##### page {p} ({tag}) special-char scan")
    for ch in sorted(set(t)):
        if ord(ch) > 0x2000:
            try: nm = unicodedata.name(ch)
            except Exception: nm = "?"
            w(f"   U+{ord(ch):04X} {ch!r} {nm}")
    # find the relevant line
    for ln in t.splitlines():
        if re.search(r"\bin\b|∈", ln):
            w(f"   LINE: {ln!r}")

doc2 = pdfium.PdfDocument(os.path.join(WS, "集合专题.pdf"))
w("\n\n##### 集合专题.pdf pages with ∈ lines")
for p in [2, 3, 5, 6, 7, 27, 31]:
    t = doc2[p-1].get_textpage().get_text_range()
    w(f"\n--- page {p} ---")
    for ln in t.splitlines():
        if "∈" in ln:
            w(f"   {ln!r}")
    chars = sorted(set(c for c in t if ord(c) > 0x2000))
    w("   specials: " + ", ".join(f"U+{ord(c):04X}{c}" for c in chars))
open(os.path.join(OUT, "chars.txt"), "w", encoding="utf-8").write("\n".join(L))
print("ok")
