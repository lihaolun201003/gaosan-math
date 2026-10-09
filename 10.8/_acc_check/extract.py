import zipfile, re, sys, os, json
from lxml import etree

PPTX = r"C:\Users\lihao\Desktop\家教\高三数学\10.8\集合专题_课堂板书版.pptx"
z = zipfile.ZipFile(PPTX)
names = z.namelist()

print("=== ZIP CONTENTS (ppt/media, ppt/slides, rels) ===")
for n in sorted(names):
    if n.startswith("ppt/media/") or n.startswith("ppt/slides/") or n.endswith(".rels") or n.startswith("ppt/presentation"):
        print(f"  {n:55s} {z.getinfo(n).file_size}")

A = "http://schemas.openxmlformats.org/drawingml/2006/main"
P = "http://schemas.openxmlformats.org/presentationml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
SVGNS = "http://schemas.microsoft.com/office/drawing/2016/SVG/main"

slides = sorted([n for n in names if re.match(r"ppt/slides/slide\d+\.xml$", n)],
                key=lambda s: int(re.search(r"(\d+)", os.path.basename(s)).group(1)))
print("\n=== SLIDE COUNT:", len(slides), "===")

summary = []
for s in slides:
    idx = int(re.search(r"(\d+)", os.path.basename(s)).group(1))
    root = etree.fromstring(z.read(s))
    sp = root.findall(f".//{{{P}}}sp")
    pic = root.findall(f".//{{{P}}}pic")
    graphicFrame = root.findall(f".//{{{P}}}graphicFrame")
    # svgBlip anywhere
    svgblips = root.findall(f".//{{{SVGNS}}}svgBlip")
    # count a:t
    ts = root.findall(f".//{{{A}}}t")
    texts = ["".join(t.itertext()) for t in ts]
    naked = root.findall(f".//{{{A}}}blip")
    summary.append(dict(slide=idx, sp=len(sp), pic=len(pic), gf=len(graphicFrame),
                        svgblip=len(svgblips), n_t=len(ts), n_blip=len(naked)))
    print(f"\n----- slide{idx}: sp={len(sp)} pic={len(pic)} graphicFrame={len(graphicFrame)} svgBlip={len(svgblips)} a:t={len(ts)} a:blip={len(naked)}")
    for i, t in enumerate(texts):
        print(f"   [t{i:02d}] {t!r}")

print("\n=== SUMMARY TABLE ===")
for r in summary:
    print(r)

# rels
print("\n=== SLIDE RELS: svg / image targets ===")
for n in sorted(names):
    if re.match(r"ppt/slides/_rels/slide\d+\.xml\.rels$", n):
        rr = etree.fromstring(z.read(n))
        tgts = [(c.get("Type","").rsplit("/",1)[-1], c.get("Target")) for c in rr]
        print(f"  {n}: {tgts}")

# presentation.xml sldSz
print("\n=== PRESENTATION.XML ===")
pres = z.read("ppt/presentation.xml").decode("utf-8")
m = re.search(r"<p:sldSz[^>]*/>", pres)
print(m.group(0) if m else "no sldSz")
print("sldIdLst count:", len(re.findall(r"<p:sldId ", pres)))
