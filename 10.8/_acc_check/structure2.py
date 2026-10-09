# -*- coding: utf-8 -*-
import zipfile, os, re, json
from lxml import etree
WS = r"C:\Users\lihao\Desktop\家教\高三数学\10.8"
PPTX = os.path.join(WS, "集合专题_课堂板书版.pptx")
OUT = os.path.join(WS, "_acc_check")
z = zipfile.ZipFile(PPTX)
L = []
def w(*a): L.append(" ".join(str(x) for x in a))

A = "http://schemas.openxmlformats.org/drawingml/2006/main"
P = "http://schemas.openxmlformats.org/presentationml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
SLIDE_W, SLIDE_H = 12192000, 6858000

def xfrm_of(sh):
    x = sh.find(f".//{{{A}}}xfrm")
    if x is None: return None, None
    return x.find(f"{{{A}}}off"), x.find(f"{{{A}}}ext")

w("=== 1. notesSlide / comment parts ===")
w("  notesSlide/comment parts:", [n for n in z.namelist() if "notesSlide" in n or "comment" in n] or "NONE")
w(f"  total parts = {len(z.namelist())}")

w("\n=== 2. presentation order vs slide file order ===")
pres = etree.fromstring(z.read("ppt/presentation.xml"))
prels = etree.fromstring(z.read("ppt/_rels/presentation.xml.rels"))
rmap = {c.get("Id"): c.get("Target") for c in prels}
order = [rmap[sid.get(f"{{{R}}}id")].replace("slides/", "") for sid in pres.find(f"{{{P}}}sldIdLst")]
w("  sldIdLst order ->", order)
w("  matches slide1..slide9 in order:", order == [f"slide{i}.xml" for i in range(1, 10)])

w("\n=== 3. background fills ===")
for name in [f"ppt/slides/slide{i}.xml" for i in range(1, 10)] + ["ppt/slideLayouts/slideLayout7.xml", "ppt/slideMasters/slideMaster1.xml"]:
    root = etree.fromstring(z.read(name))
    bg = root.find(f".//{{{P}}}bg")
    w(f"  {name}: bg={'NONE' if bg is None else etree.tostring(bg, encoding='unicode')[:200]}")

w("\n=== 4. per-slide shape census ===")
for i in range(1, 10):
    root = etree.fromstring(z.read(f"ppt/slides/slide{i}.xml"))
    spTree = root.find(f".//{{{P}}}spTree")
    n_sp = n_pic = n_cxn = n_grp = n_gf = 0
    n_sp_with_t = 0
    maxpic = 0.0; total_pic = 0.0
    for sh in spTree:
        tag = etree.QName(sh).localname
        if tag == "sp":
            n_sp += 1
            if sh.findall(f".//{{{A}}}t"): n_sp_with_t += 1
        elif tag == "pic":
            n_pic += 1
            o, x = xfrm_of(sh)
            if x is not None:
                a = int(x.get("cx"))*int(x.get("cy"))/(SLIDE_W*SLIDE_H)*100
                total_pic += a
                if a > maxpic: maxpic = a
        elif tag == "cxnSp": n_cxn += 1
        elif tag == "grpSp": n_grp += 1
        elif tag == "graphicFrame": n_gf += 1
    geoms = [g.get("prst") for g in root.findall(f".//{{{A}}}prstGeom")]
    w(f"  slide{i}: sp={n_sp}(with a:t={n_sp_with_t}) pic={n_pic} cxnSp={n_cxn} grpSp={n_grp} graphicFrame={n_gf} "
      f"maxPicArea={maxpic:.2f}%  totalPicArea={total_pic:.2f}%  prstGeoms={sorted(set(geoms))}")

w("\n=== 5. LEAK SCAN: forbidden strings in slide text ===")
bad = ["答案", "解析", "故选", "选C", "选 C", "参考", "正确选项", "提示", "总结", "知识点", "思路",
       "解答", "易错", "评析", "【答案】", "因此", "所以选", "解得", "分析", "点评", "方法"]
for i in range(1, 10):
    root = etree.fromstring(z.read(f"ppt/slides/slide{i}.xml"))
    txt = "".join("".join(t.itertext()) for t in root.findall(f".//{{{A}}}t"))
    hits = [b for b in bad if b in txt]
    w(f"  slide{i}: forbidden-hits={hits}   full-text={txt!r}")

w("\n=== 6. SVG/XML leak scan ===")
svgs = [n for n in z.namelist() if n.endswith(".svg")]
withtext = [n for n in svgs if ("<text" in z.read(n).decode("utf-8","replace") or "<tspan" in z.read(n).decode("utf-8","replace"))]
w(f"  SVG parts containing <text>/<tspan>: {len(withtext)} of {len(svgs)}  {withtext[:5]}")
for n in z.namelist():
    if n.endswith(".xml") or n.endswith(".rels"):
        raw = z.read(n).decode("utf-8", "replace")
        for b in ["答案", "解析", "故选"]:
            if b in raw: w(f"  !! {n} contains {b}")

w("\n=== 7. largest picture shapes across deck ===")
pics = []
for i in range(1, 10):
    root = etree.fromstring(z.read(f"ppt/slides/slide{i}.xml"))
    for sh in root.find(f".//{{{P}}}spTree"):
        if etree.QName(sh).localname != "pic": continue
        o, x = xfrm_of(sh)
        cx, cy = int(x.get("cx")), int(x.get("cy"))
        pics.append((cx*cy/(SLIDE_W*SLIDE_H)*100, i, int(o.get("x"))/914400, int(o.get("y"))/914400, cx/914400, cy/914400))
pics.sort(reverse=True)
for p in pics[:6]:
    w(f"   {p[0]:.2f}% of slide  slide{p[1]}  at ({p[2]:.2f},{p[3]:.2f})in  size {p[4]:.2f}x{p[5]:.2f}in")

w("\n=== 8. bottom-most shape edge per slide (from XML geometry, 540pt tall) ===")
for i in range(1, 10):
    root = etree.fromstring(z.read(f"ppt/slides/slide{i}.xml"))
    mx = 0; who = ""
    for sh in root.find(f".//{{{P}}}spTree"):
        o, x = xfrm_of(sh)
        if x is None or o is None: continue
        bot = int(o.get("y")) + int(x.get("cy"))
        if bot > mx:
            mx = bot
            who = f"{etree.QName(sh).localname} " + repr("".join("".join(t.itertext()) for t in sh.findall(f'.//{{{A}}}t'))[:16])
    botpt = mx/12700
    w(f"  slide{i}: bottom edge {botpt:.1f}pt = {botpt/540*100:.1f}% -> lower blank {100-botpt/540*100:.2f}%   [{who}]")

open(os.path.join(OUT, "structure.txt"), "w", encoding="utf-8").write("\n".join(L))
print("ok")
