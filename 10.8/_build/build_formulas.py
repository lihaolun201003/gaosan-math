# -*- coding: utf-8 -*-
"""Build LaTeX formulas -> SVG (vector) + high-DPI PNG fallback, with exact metrics."""
import json, os, re, subprocess

BASE   = os.path.dirname(os.path.abspath(__file__))
TEXDIR = os.path.join(BASE, "formulas")
SVGDIR = os.path.join(BASE, "svg")
PNGDIR = os.path.join(BASE, "png")
for d in (TEXDIR, SVGDIR, PNGDIR):
    os.makedirs(d, exist_ok=True)

TEMPLATE = (
    "\\documentclass[border=0pt,12pt]{standalone}\n"
    "\\usepackage{amsmath,amssymb}\n"
    "\\newlength\\dsmW\\newlength\\dsmH\\newlength\\dsmD\n"
    "\\begin{document}\n"
    "\\settowidth\\dsmW{$%(m)s$}%%\n"
    "\\settoheight\\dsmH{$%(m)s$}%%\n"
    "\\settodepth\\dsmD{$%(m)s$}%%\n"
    "\\typeout{DSHMETRIC:\\number\\dsmW:\\number\\dsmH:\\number\\dsmD}%%\n"
    "$%(m)s$%%\n"
    "\\end{document}\n"
)

def run(cmd, cwd=None):
    p = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.returncode, p.stdout.decode("utf-8", "replace")

def main():
    spec = json.load(open(os.path.join(BASE, "formulas.json"), encoding="utf-8"))
    manifest, errs = {}, []
    for name, math in spec["snippets"].items():
        with open(os.path.join(TEXDIR, name + ".tex"), "w", encoding="utf-8") as f:
            f.write(TEMPLATE % {"m": math})
        rc, out = run(["xelatex", "-interaction=nonstopmode", "-halt-on-error", name + ".tex"], cwd=TEXDIR)
        log = os.path.join(TEXDIR, name + ".log")
        m = None
        if os.path.exists(log):
            m = re.search(r"DSHMETRIC:(-?\d+):(-?\d+):(-?\d+)",
                          open(log, encoding="utf-8", errors="replace").read())
        if not m:
            errs.append((name, "no metric rc=%d" % rc, out[-500:])); continue
        wd, ht, dp = (int(x) for x in m.groups())
        pdf = os.path.join(TEXDIR, name + ".pdf")
        svg = os.path.join(SVGDIR, name + ".svg")
        png = os.path.join(PNGDIR, name + ".png")
        for p in (svg, png):
            if os.path.exists(p): os.remove(p)
        rc1, o1 = run(["dvisvgm", "--pdf", "--no-fonts", "--exact", "-o", svg, pdf])
        rc2, o2 = run(["pdftocairo", "-png", "-transp", "-r", "1200", "-singlefile", pdf,
                       os.path.join(PNGDIR, name)])
        gs = re.search(r"graphic size:\s*([\d.]+)pt x ([\d.]+)pt", o1)
        vb = None
        if os.path.exists(svg):
            mm = re.search(r"viewBox='([-\d.]+) ([-\d.]+) ([-\d.]+) ([-\d.]+)'",
                           open(svg, encoding="utf-8", errors="replace").read(600))
            if mm: vb = [float(x) for x in mm.groups()]
        manifest[name] = {
            "math": math, "wd_sp": wd, "ht_sp": ht, "dp_sp": dp,
            "svg": "svg/" + name + ".svg", "png": "png/" + name + ".png",
            "graphic_pt": [float(gs.group(1)), float(gs.group(2))] if gs else None,
            "viewBox": vb,
        }
        if rc1 != 0 or not os.path.exists(svg): errs.append((name, "dvisvgm", o1[-300:]))
        if rc2 != 0 or not os.path.exists(png): errs.append((name, "pdftocairo", o2[-300:]))
    json.dump(manifest, open(os.path.join(BASE, "manifest.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    print("built %d snippets, %d errors" % (len(manifest), len(errs)))
    for e in errs: print("ERR", e[0], e[1], e[2][:200])
    bad = 0
    print("%-10s %8s %8s %8s | %8s %8s | %s" % ("name","wd_pt","ht_pt","dp_pt","svg_w","svg_h","ok"))
    for k, v in manifest.items():
        ew = v["wd_sp"]/65536.0; eh = (v["ht_sp"]+v["dp_sp"])/65536.0
        gw, gh = (v["graphic_pt"] or [0,0])
        ok = abs(gw-ew) <= 0.02 and abs(gh-eh) <= 0.02
        if not ok: bad += 1
        print("%-10s %8.3f %8.3f %8.3f | %8.3f %8.3f | %s" % (k, ew, v["ht_sp"]/65536.0,
              v["dp_sp"]/65536.0, gw, gh, "OK" if ok else "MISMATCH"))
    print("bbox mismatches:", bad)

main()
