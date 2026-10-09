# -*- coding: utf-8 -*-
"""Compile each math snippet with XeLaTeX at its true point size, then emit
   * vector SVG  (dvisvgm --pdf --no-fonts --exact : glyphs become paths)
   * 1200-dpi transparent PNG fallback (for renderers that ignore svgBlip)
   and record exact TeX box metrics (width / height / depth) in manifest.json.
"""
import json, os, re, subprocess, sys

BASE = os.path.dirname(os.path.abspath(__file__))
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
    "\\fontsize{%(size)d}{%(lead).1f}\\selectfont\n"
    "\\settowidth\\dsmW{$%(m)s$}%%\n"
    "\\settoheight\\dsmH{$%(m)s$}%%\n"
    "\\settodepth\\dsmD{$%(m)s$}%%\n"
    "\\typeout{DSHMETRIC:\\number\\dsmW:\\number\\dsmH:\\number\\dsmD}%%\n"
    "$%(m)s$%%\n"
    "\\end{document}\n"
)

SP = 65536.0
TEXPT_TO_BP = 72.0 / 72.27      # TeX pt -> PowerPoint pt (1/72 in)


def run(cmd, cwd=None):
    p = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.returncode, p.stdout.decode("utf-8", "replace")


def main():
    spec = json.load(open(os.path.join(BASE, "formulas.json"), encoding="utf-8"))["snippets"]
    manifest, errs = {}, []
    for name, item in spec.items():
        math, size = item["tex"], int(item["size"])
        src = TEMPLATE % {"m": math, "size": size, "lead": size * 1.2}
        with open(os.path.join(TEXDIR, name + ".tex"), "w", encoding="utf-8") as f:
            f.write(src)
        rc, out = run(["xelatex", "-interaction=nonstopmode", "-halt-on-error",
                       name + ".tex"], cwd=TEXDIR)
        log = os.path.join(TEXDIR, name + ".log")
        metric = None
        if os.path.exists(log):
            metric = re.search(r"DSHMETRIC:(-?\d+):(-?\d+):(-?\d+)",
                               open(log, encoding="utf-8", errors="replace").read())
        if not metric:
            errs.append((name, "no DSHMETRIC rc=%d" % rc, out[-400:]))
            continue
        wd, ht, dp = (int(x) for x in metric.groups())
        pdf = os.path.join(TEXDIR, name + ".pdf")
        svg = os.path.join(SVGDIR, name + ".svg")
        png = os.path.join(PNGDIR, name + ".png")
        for p in (svg, png):
            if os.path.exists(p):
                os.remove(p)
        rc1, o1 = run(["dvisvgm", "--pdf", "--no-fonts", "--exact", "-o", svg, pdf])
        rc2, o2 = run(["pdftocairo", "-png", "-transp", "-r", "1200", "-singlefile", pdf,
                       os.path.join(PNGDIR, name)])
        gs = re.search(r"graphic size:\s*([\d.]+)pt x ([\d.]+)pt", o1)
        vb = None
        if os.path.exists(svg):
            mm = re.search(r"viewBox='([-\d.]+) ([-\d.]+) ([-\d.]+) ([-\d.]+)'",
                           open(svg, encoding="utf-8", errors="replace").read(800))
            if mm:
                vb = [float(x) for x in mm.groups()]
        manifest[name] = {
            "tex": math, "size": size,
            "wd_sp": wd, "ht_sp": ht, "dp_sp": dp,
            "wd_pt": wd / SP, "ht_pt": ht / SP, "dp_pt": dp / SP,
            "wd_disp": wd / SP * TEXPT_TO_BP,
            "ht_disp": ht / SP * TEXPT_TO_BP,
            "dp_disp": dp / SP * TEXPT_TO_BP,
            "svg": "svg/" + name + ".svg", "png": "png/" + name + ".png",
            "graphic_pt": [float(gs.group(1)), float(gs.group(2))] if gs else None,
            "viewBox": vb,
            "svg_bytes": os.path.getsize(svg) if os.path.exists(svg) else 0,
            "png_bytes": os.path.getsize(png) if os.path.exists(png) else 0,
        }
        if rc1 != 0 or not os.path.exists(svg):
            errs.append((name, "dvisvgm", o1[-300:]))
        if rc2 != 0 or not os.path.exists(png):
            errs.append((name, "pdftocairo", o2[-300:]))

    json.dump(manifest, open(os.path.join(BASE, "manifest.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    print("built %d snippets, %d errors" % (len(manifest), len(errs)))
    for e in errs:
        print("ERR", e[0], e[1], e[2][:300])

    bad = 0
    print("%-9s %4s | %8s %8s %8s | %8s %8s | %6s %6s | %s"
          % ("name", "size", "wd_pt", "ht_pt", "dp_pt", "svg_w", "svg_h", "kB", "kB", "bbox"))
    for k, v in manifest.items():
        ew = v["wd_sp"] / SP
        eh = (v["ht_sp"] + v["dp_sp"]) / SP
        gw, gh = (v["graphic_pt"] or [0, 0])
        ok = abs(gw - ew) <= 0.02 and abs(gh - eh) <= 0.02
        if not ok:
            bad += 1
        print("%-9s %4d | %8.3f %8.3f %8.3f | %8.3f %8.3f | %6.1f %6.1f | %s"
              % (k, v["size"], ew, v["ht_sp"] / SP, v["dp_sp"] / SP, gw, gh,
                 v["svg_bytes"] / 1024.0, v["png_bytes"] / 1024.0, "OK" if ok else "MISMATCH"))
    print("bbox mismatches:", bad)
    return 1 if (errs or bad) else 0


if __name__ == "__main__":
    sys.exit(main())
