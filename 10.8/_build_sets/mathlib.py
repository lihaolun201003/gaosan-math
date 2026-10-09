# -*- coding: utf-8 -*-
"""mathlib.py -- XeLaTeX -> PDF -> vector SVG (glyphs as paths) + high-DPI PNG fallback.

For every math snippet we record the EXACT TeX box metrics (width/height/depth) in
scaled points at the 12pt class size.  Because `standalone` with `border=0pt` crops
the page to the content box, the produced PDF -- and therefore the SVG viewBox --
matches those metrics exactly.  That lets the deck builder place a snippet so that
its *baseline* lands on an exact y coordinate.
"""
import json
import os
import re
import subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
TEXDIR = os.path.join(BASE, "tex")
SVGDIR = os.path.join(BASE, "svg")
PNGDIR = os.path.join(BASE, "png")
for _d in (TEXDIR, SVGDIR, PNGDIR):
    os.makedirs(_d, exist_ok=True)

CLASS_PT = 12.0          # class option of the standalone document
SP_PER_PT = 65536.0      # scaled points per point
TEX2BP = 72.0 / 72.27    # TeX pt (1/72.27in) -> big point (1/72in), used by PDF/SVG/PPTX
PNG_DPI = 1200           # raster fallback resolution (vector is the primary path)

TEMPLATE = (
    "\\documentclass[border=0pt,12pt]{standalone}\n"
    "\\usepackage{amsmath,amssymb}\n"
    "\\newlength\\dsmW\\newlength\\dsmH\\newlength\\dsmD\n"
    "\\begin{document}%\n"
    "\\settowidth\\dsmW{$@M@$}%\n"
    "\\settoheight\\dsmH{$@M@$}%\n"
    "\\settodepth\\dsmD{$@M@$}%\n"
    "\\typeout{DSHMETRIC:\\number\\dsmW:\\number\\dsmH:\\number\\dsmD}%\n"
    "\\noindent$@M@$%\n"
    "\\end{document}\n"
)


def _run(cmd, cwd=None):
    p = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.returncode, p.stdout.decode("utf-8", "replace")


def build(name, math):
    """Compile one snippet.  Returns a metrics dict (raises on hard failure)."""
    tex = os.path.join(TEXDIR, name + ".tex")
    with open(tex, "w", encoding="utf-8") as fh:
        fh.write(TEMPLATE.replace("@M@", math))

    rc, out = _run(["xelatex", "-interaction=nonstopmode", "-halt-on-error",
                    name + ".tex"], cwd=TEXDIR)
    log = os.path.join(TEXDIR, name + ".log")
    mm = None
    if os.path.exists(log):
        with open(log, encoding="utf-8", errors="replace") as fh:
            mm = re.search(r"DSHMETRIC:(-?\d+):(-?\d+):(-?\d+)", fh.read())
    if not mm:
        raise RuntimeError("xelatex failed for %s (rc=%d)\n%s" % (name, rc, out[-1500:]))
    w_sp, h_sp, d_sp = (int(x) for x in mm.groups())

    pdf = os.path.join(TEXDIR, name + ".pdf")
    if not os.path.exists(pdf):
        raise RuntimeError("no PDF for %s\n%s" % (name, out[-1500:]))

    svg = os.path.join(SVGDIR, name + ".svg")
    png = os.path.join(PNGDIR, name + ".png")
    for p in (svg, png):
        if os.path.exists(p):
            os.remove(p)

    rc1, o1 = _run(["dvisvgm", "--pdf", "--no-fonts", "--exact", "-o", svg, pdf])
    if rc1 != 0 or not os.path.exists(svg):
        raise RuntimeError("dvisvgm failed for %s\n%s" % (name, o1[-1500:]))

    rc2, o2 = _run(["pdftocairo", "-png", "-transp", "-r", str(PNG_DPI),
                    "-singlefile", pdf, os.path.join(PNGDIR, name)])
    if rc2 != 0 or not os.path.exists(png):
        raise RuntimeError("pdftocairo failed for %s\n%s" % (name, o2[-1500:]))

    gs = re.search(r"graphic size:\s*([\d.]+)pt x ([\d.]+)pt", o1)
    with open(svg, encoding="utf-8", errors="replace") as fh:
        head = fh.read(1200)
    vb = re.search(r"viewBox='([-\d.eE]+) ([-\d.eE]+) ([-\d.eE]+) ([-\d.eE]+)'", head)

    return {
        "math": math,
        "wd_pt": w_sp / SP_PER_PT,
        "ht_pt": h_sp / SP_PER_PT,
        "dp_pt": d_sp / SP_PER_PT,
        "graphic_pt": [float(gs.group(1)), float(gs.group(2))] if gs else None,
        "viewBox": [float(x) for x in vb.groups()] if vb else None,
        "svg": os.path.relpath(svg, BASE).replace("\\", "/"),
        "png": os.path.relpath(png, BASE).replace("\\", "/"),
    }


def build_all(snippets, manifest_path=None):
    manifest, errors = {}, []
    for name in sorted(snippets):
        try:
            manifest[name] = build(name, snippets[name])
        except Exception as exc:                       # noqa: BLE001
            errors.append((name, snippets[name], str(exc)[:800]))
    if manifest_path:
        with open(manifest_path, "w", encoding="utf-8") as fh:
            json.dump(manifest, fh, ensure_ascii=False, indent=1)
    return manifest, errors


def report(manifest, errors):
    print("compiled %d snippets, %d errors" % (len(manifest), len(errors)))
    for name, math, msg in errors:
        print("  ERR %-10s %s" % (name, math))
        print("      " + msg.replace("\n", "\n      ")[:900])
    bad = 0
    print("%-12s %8s %7s %7s | %8s %8s | %8s %8s %s"
          % ("name", "wd_tex", "ht_tex", "dp_tex", "pdf_w", "pdf_h", "svg_w", "svg_h", "ok"))
    for k in sorted(manifest):
        v = manifest[k]
        ew, eh = v["wd_pt"], v["ht_pt"] + v["dp_pt"]
        gw, gh = (v["graphic_pt"] or [0.0, 0.0])
        vw, vh = ((v["viewBox"][2], v["viewBox"][3]) if v["viewBox"] else (0.0, 0.0))
        # `graphic size` from dvisvgm is reported in TeX pt; the SVG root/viewBox use bp.
        ok = (abs(gw - ew) <= 0.03 and abs(gh - eh) <= 0.03
              and abs(vw - ew * TEX2BP) <= 0.02 and abs(vh - eh * TEX2BP) <= 0.02)
        if not ok:
            bad += 1
        print("%-12s %8.3f %7.3f %7.3f | %8.3f %8.3f | %8.3f %8.3f %s"
              % (k, ew, v["ht_pt"], v["dp_pt"], gw, gh, vw, vh, "OK" if ok else "MISMATCH"))
    print("bbox mismatches:", bad)
    return bad
