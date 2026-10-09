import zipfile, re, os, json
from lxml import etree

WS = r"C:\Users\lihao\Desktop\家教\高三数学\10.8"
PPTX = os.path.join(WS, "集合专题_课堂板书版.pptx")
OUT = os.path.join(WS, "_acc_check")
os.makedirs(OUT, exist_ok=True)

z = zipfile.ZipFile(PPTX)
names = z.namelist()
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
P = "http://schemas.openxmlformats.org/presentationml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
SVGNS = "http://schemas.microsoft.com/office/drawing/2016/SVG/main"

lines = []
def w(s=""):
    lines.append(str(s))

slides = sorted([n for n in names if re.match(r"ppt/slides/slide\d+\.xml$", n)],
                key=lambda s: int(re.search(r"(\d+)", os.path.basename(s)).group(1)))

w("=== SVG MEDIA PARTS ===")
svgmedia = sorted([n for n in names if n.startswith("ppt/media/") and n.endswith(".svg")])
pngmedia = sorted([n for n in names if n.startswith("ppt/media/") and n.endswith(".png")])
w(f"ppt/media/*.svg count = {len(svgmedia)}")
w(f"ppt/media/*.png count = {len(pngmedia)}")

w("")
w("=== PER-SLIDE DETAIL ===")
for s in slides:
    idx = int(re.search(r"(\d+)", os.path.basename(s)).group(1))
    root = etree.fromstring(z.read(s))
    sps = root.findall(f".//{{{P}}}sp")
    pics = root.findall(f".//{{{P}}}pic")
    svgblips = root.findall(f".//{{{SVGNS}}}svgBlip")
    ts = root.findall(f".//{{{A}}}t")
    w(f"\n########## slide{idx}: sp={len(sps)} pic={len(pics)} svgBlip={len(svgblips)} a:t={len(ts)}")
    # walk shapes in document order with position
    spTree = root.find(f".//{{{P}}}spTree")
    for si, sh in enumerate(spTree):
        tag = etree.QName(sh).localname
        if tag not in ("sp", "pic", "graphicFrame", "grpSp", "cxnSp"):
            continue
        xfrm = sh.find(f".//{{{A}}}xfrm")
        off = ext = None
        if xfrm is not None:
            o = xfrm.find(f"{{{A}}}off"); e = xfrm.find(f"{{{A}}}ext")
            if o is not None: off = (int(o.get("x")), int(o.get("y")))
            if e is not None: ext = (int(e.get("cx")), int(e.get("cy")))
        txts = ["".join(t.itertext()) for t in sh.findall(f".//{{{A}}}t")]
        svg = sh.findall(f".//{{{SVGNS}}}svgBlip")
        blips = sh.findall(f".//{{{A}}}blip")
        embed_rels = [b.get(f"{{{R}}}embed") for b in blips]
        w(f"  [{si}] <{tag}> name={sh.get('name')!r} off={off} ext={ext} svgBlip={len(svg)} blipRels={embed_rels}")
        for t in txts:
            w(f"        TEXT: {t!r}")

with open(os.path.join(OUT, "pptx_dump.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

# Plain text per slide for leak-checking
leak = []
for s in slides:
    idx = int(re.search(r"(\d+)", os.path.basename(s)).group(1))
    root = etree.fromstring(z.read(s))
    txts = ["".join(t.itertext()) for t in root.findall(f".//{{{A}}}t")]
    leak.append(f"--- slide{idx} ---\n" + "\n".join(txts))
with open(os.path.join(OUT, "slide_text.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(leak))
print("done", os.path.join(OUT, "pptx_dump.txt"))
