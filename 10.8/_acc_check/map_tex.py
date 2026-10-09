import zipfile, os, hashlib, re
from lxml import etree

WS = r"C:\Users\lihao\Desktop\家教\高三数学\10.8"
PPTX = os.path.join(WS, "集合专题_课堂板书版.pptx")
BUILD = os.path.join(WS, "_build_sets")
OUT = os.path.join(WS, "_acc_check")
z = zipfile.ZipFile(PPTX)

def h(b): return hashlib.sha256(b).hexdigest()[:16]
media = {n: h(z.read(n)) for n in z.namelist() if n.startswith("ppt/media/")}
buildsvg = {}
for fn in os.listdir(os.path.join(BUILD, "svg")):
    buildsvg[h(open(os.path.join(BUILD, "svg", fn), "rb").read())] = fn

A = "http://schemas.openxmlformats.org/drawingml/2006/main"
P = "http://schemas.openxmlformats.org/presentationml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
SVGNS = "http://schemas.microsoft.com/office/drawing/2016/SVG/main"

lines = []
def w(s=""): lines.append(str(s))
for si in range(1, 10):
    rels = etree.fromstring(z.read(f"ppt/slides/_rels/slide{si}.xml.rels"))
    idmap = {c.get("Id"): c.get("Target").replace("../", "ppt/") for c in rels}
    root = etree.fromstring(z.read(f"ppt/slides/slide{si}.xml"))
    w(f"\n---------- slide{si} ----------")
    n_svg = 0
    for sh in root.find(f".//{{{P}}}spTree"):
        if etree.QName(sh).localname != "pic":
            continue
        svg = sh.find(f".//{{{SVGNS}}}svgBlip")
        png_blip = sh.find(f".//{{{A}}}blip")
        png_id = png_blip.get(f"{{{R}}}embed") if png_blip is not None else None
        svg_id = svg.get(f"{{{R}}}embed") if svg is not None else None
        xfrm = sh.find(f".//{{{A}}}xfrm")
        o = xfrm.find(f"{{{A}}}off"); e = xfrm.find(f"{{{A}}}ext")
        svgtgt = idmap.get(svg_id); pngtgt = idmap.get(png_id)
        bn = buildsvg.get(media.get(svgtgt, ""), "??")
        texp = os.path.join(BUILD, "tex", bn.replace(".svg", ".tex"))
        body = ""
        if os.path.exists(texp):
            t = open(texp, encoding="utf-8", errors="replace").read()
            body = t.split(r"\begin{document}", 1)[-1].split(r"\end{document}")[0]
            body = re.sub(r"\s+", " ", body).strip()
            body = re.sub(r"^\$+\s*|\s*\$+$", "", body)
        n_svg += 1
        w(f"  svg#{n_svg} {svgtgt} (png {pngtgt}) build={bn}")
        w(f"        pos=({int(o.get('x'))/914400:.2f},{int(o.get('y'))/914400:.2f})in  sz={int(e.get('cx'))/914400:.2f}x{int(e.get('cy'))/914400:.2f}in  szMB={int(e.get('cx'))/12700:.0f}x{int(e.get('cy'))/12700:.0f}pt")
        w(f"        LATEX: {body}")
    w(f"  >> svgBlip total on slide{si} = {n_svg}")

open(os.path.join(OUT, "svg_tex_map.txt"), "w", encoding="utf-8").write("\n".join(lines))
print("ok")
