# -*- coding: utf-8 -*-
"""Pure-geometry layout engine for the 板书 deck.

Produces an explicit placement plan (text boxes + vector math pictures, all in
PowerPoint points) from content.json + manifest.json, and checks the hard
acceptance rules (content stays above max_content_bottom so that >=60% of the
slide is untouched white; nothing crosses the right margin).

Text model (calibrated against a LibreOffice render, see calib2_*):
    * text box: top-anchored, zero insets, word_wrap=False
    * first-line baseline == box_top + font_size
    * advance widths / ink extents from metrics.py (微软雅黑)
Baseline alignment puts native text and LaTeX pictures on one baseline.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import metrics

PUNCT_AFTER = set("，。、；：！？")
CLOSE_AFTER = set("）】》”’")
OPEN_MARK = set("“‘（《【")
CLOSE_MARK = set("，。、；：！？）】》”’")
# break preferences: a clause boundary is the natural place to break; a break
# after a closing quote is acceptable; anything else is a last resort.
PEN_CLAUSE, PEN_CLOSE, PEN_MATH, PEN_OTHER = 0.0, 250.0, 400.0, 800.0
SLACK_WEIGHT = 1000.0


# ----------------------------------------------------------------- atomising
def _split_atom(seg, size, bold=False):
    """Split one content segment into measurable atoms.

    Native text is split per character so a paragraph can break anywhere, but
    consecutive ASCII letters/digits stay glued into words (e.g. option labels).
    """
    if seg.startswith("@"):
        return [{"kind": "m", "name": seg[1:], "size": size}]
    if seg.startswith("#"):
        return [{"kind": "l", "text": seg[1:], "size": size, "bold": True}]
    out, buf = [], ""
    for ch in seg:
        if ch.isascii() and not ch.isspace():
            buf += ch
        else:
            if buf:
                out.append({"kind": "t", "text": buf, "size": size, "bold": bold})
                buf = ""
            out.append({"kind": "t", "text": ch, "size": size, "bold": bold})
    if buf:
        out.append({"kind": "t", "text": buf, "size": size, "bold": bold})
    return out


def _measure(atom, man):
    """Fill w / up / down (pt, relative to the baseline) for one atom."""
    if atom["kind"] == "m":
        m = man[atom["name"]]
        atom["w"] = m["wd_disp"]
        atom["up"] = m["ht_disp"]
        atom["down"] = m["dp_disp"]
    else:
        t, s, b = atom["text"], atom["size"], atom.get("bold", False)
        atom["w"] = metrics.advance(t, s, b)
        up, down, _x0, _x1 = metrics.ink(t, s, b)
        atom["up"], atom["down"] = up, down
    return atom


def build_atoms(segments, size, man):
    atoms = []
    for seg in segments:
        for a in _split_atom(seg, size):
            atoms.append(_measure(a, man))
    return atoms


# ------------------------------------------------------------------- wrapping
def gap_before(prev, cur, small, big):
    """Space where native text meets a LaTeX picture.

    Characters of one native run are laid out contiguously by the renderer, so a
    boundary between two text atoms gets no gap -- otherwise the accumulated
    slack would push every following formula to the right.

    A formula sandwiched between ordinary Chinese gets the usual 1/4-em
    CJK/Latin space (`big`), but one that already sits inside quotes or brackets
    only gets a hair space (`small`), because the full-width mark supplies its own
    padding.
    """
    if prev is None:
        return 0.0
    if prev["kind"] == "m" or cur["kind"] == "m":
        if prev["kind"] == "t" and prev["text"][-1:] in OPEN_MARK:
            return small
        if cur["kind"] == "t" and cur["text"][:1] in CLOSE_MARK:
            return small
        return big
    return 0.0


def pack(atoms, maxw, small, big):
    """Optimal line breaking (DP, minimise squared slack + break penalties)."""
    n = len(atoms)
    if n == 0:
        return []
    g = [0.0] + [gap_before(atoms[i - 1], atoms[i], small, big) for i in range(1, n)]
    pre = [0.0]                                   # prefix sums of width+gap
    for i, a in enumerate(atoms):
        pre.append(pre[-1] + a["w"] + g[i])

    def width(i, j):                              # atoms i..j-1 on one line
        return pre[j] - pre[i] - g[i]

    best = [None] * (n + 1)
    best[n] = (0.0, None)
    for i in range(n - 1, -1, -1):
        for j in range(i + 1, n + 1):
            w = width(i, j)
            if w > maxw:
                break
            pen = 0.0
            if j < n:
                tail = atoms[j - 1].get("text", "")[-1:]
                if tail in PUNCT_AFTER:
                    pen = PEN_CLAUSE
                elif tail in CLOSE_AFTER:
                    pen = PEN_CLOSE
                elif atoms[j]["kind"] == "m" or atoms[j - 1]["kind"] == "m":
                    pen = PEN_MATH
                else:
                    pen = PEN_OTHER
            if best[j] is None:
                continue
            cost = SLACK_WEIGHT * ((maxw - w) / maxw) ** 2 + pen + best[j][0]
            if best[i] is None or cost < best[i][0]:
                best[i] = (cost, j)
    lines, i = [], 0
    while i < n:
        j = best[i][1]
        lines.append(atoms[i:j])
        i = j
    return lines


# ---------------------------------------------------------------- slide plan
def plan_slide(sl, L, man):
    stem_size = float(L["stem_size"])
    opt_size = float(L["opt_size"])
    content_w = L["slide_w"] - L["margin_l"] - L["margin_r"]
    gs = float(L["seg_gap_small"])
    gb = float(L["seg_gap_big"])
    indents = sl.get("stem_indent") or [0] * len(sl["stem"])

    # ---- stem paragraphs -> visual lines
    lines = []                                     # (atoms, indent)
    stem_max = float(L.get("stem_max_width", content_w))
    for para, ind in zip(sl["stem"], indents):
        atoms = build_atoms(para, stem_size, man)
        maxw = min(content_w, stem_max) - ind
        for ln in pack(atoms, maxw, gs * stem_size, gb * stem_size):
            lines.append((ln, ind))

    # ---- options -> 2 x 2 grid
    opts = [build_atoms(o, opt_size, man) for o in sl["options"]][:4]

    plan = {"n": sl["n"], "title": sl["title"], "texts": [], "math": [], "lines": []}
    y = float(L["content_top"])

    for ln, ind in lines:
        A = max(a["up"] for a in ln)
        D = max(a["down"] for a in ln)
        base = y + A
        x0_line = float(L["margin_l"]) + ind
        x = x0_line
        run_text, run_x = None, None
        for i, a in enumerate(ln):
            if i:
                x += gap_before(ln[i - 1], a, gs * stem_size, gb * stem_size)
            if a["kind"] == "t":
                if run_text is None:
                    run_text, run_x = a["text"], x
                else:
                    run_text += a["text"]
                x += a["w"]
                continue
            if run_text is not None:
                plan["texts"].append({"s": run_text, "x": run_x, "base": base,
                                      "size": stem_size, "bold": False})
                run_text = None
            if a["kind"] == "l":
                plan["texts"].append({"s": a["text"], "x": x, "base": base,
                                      "size": stem_size, "bold": True})
            else:
                plan["math"].append({"name": a["name"], "x": x, "base": base})
            x += a["w"]
        if run_text is not None:
            plan["texts"].append({"s": run_text, "x": run_x, "base": base,
                                  "size": stem_size, "bold": False})
        plan["lines"].append({"base": round(base, 2), "A": round(A, 2), "D": round(D, 2),
                              "right": round(x, 2), "left": round(x0_line, 2)})
        y = base + D + L["row_gap"]

    y = y - L["row_gap"] + L["block_gap"]

    for row in range(2):
        items = opts[row * 2:row * 2 + 2]
        if not items:
            break
        A = max(a["up"] for it in items for a in it)
        D = max(a["down"] for it in items for a in it)
        base = y + A
        rx0, rx1 = 1e9, -1e9
        for c, it in enumerate(items):
            x = float(L["opt_col_x"][c])
            x_start = x
            for i, a in enumerate(it):
                if i:
                    if it[i - 1]["kind"] == "l":
                        x += float(L["label_gap"])
                    else:
                        x += gap_before(it[i - 1], a, gs * opt_size, gb * opt_size)
                if a["kind"] == "m":
                    plan["math"].append({"name": a["name"], "x": x, "base": base})
                else:
                    plan["texts"].append({"s": a["text"], "x": x, "base": base,
                                          "size": opt_size, "bold": a["kind"] == "l"})
                x += a["w"]
            rx0, rx1 = min(rx0, x_start), max(rx1, x)
        plan["lines"].append({"base": round(base, 2), "A": round(A, 2), "D": round(D, 2),
                              "right": round(rx1, 2), "left": round(rx0, 2),
                              "option": True})
        y = base + D + L["opt_row_gap"]
    y = y - L["opt_row_gap"]
    plan["content_bottom"] = round(y, 2)
    return plan


def build(content_path=None):
    content_path = content_path or os.path.join(HERE, "content.json")
    C = json.load(open(content_path, encoding="utf-8"))
    man = json.load(open(os.path.join(HERE, "manifest.json"), encoding="utf-8"))
    L = C["layout"]
    plans = [plan_slide(sl, L, man) for sl in C["slides"]]
    return C, L, man, plans


def check(C, L, man, plans):
    """Return (ok, list_of_problems)."""
    problems = []
    right_limit = L["slide_w"] - L["margin_r"]
    for p in plans:
        if p["content_bottom"] > L["max_content_bottom"] + 1e-6:
            problems.append("slide %d: content bottom %.1f > %.1f"
                            % (p["n"], p["content_bottom"], L["max_content_bottom"]))
        for t in p["texts"]:
            r = t["x"] + metrics.advance(t["s"], t["size"], t["bold"])
            if r > right_limit + 0.5:
                problems.append("slide %d: text %r right edge %.1f > %.1f"
                                % (p["n"], t["s"], r, right_limit))
        for m in p["math"]:
            w = man[m["name"]]["wd_disp"]
            if m["x"] + w > right_limit + 0.5:
                problems.append("slide %d: math %s right edge %.1f > %.1f"
                                % (p["n"], m["name"], m["x"] + w, right_limit))
    return (not problems), problems


def report(C, L, man, plans):
    print("slide  title                              bottom  blank%  lines   right  math  ok")
    for p in plans:
        h = L["slide_h"]
        blank = (h - p["content_bottom"]) / h * 100.0
        right = max((l["right"] for l in p["lines"]), default=0.0)
        good = p["content_bottom"] <= L["max_content_bottom"] + 1e-6
        print("%5d  %-34s %6.1f  %5.1f%%  %5d  %6.1f  %4d  %s"
              % (p["n"], p["title"], p["content_bottom"], blank, len(p["lines"]),
                 right, len(p["math"]), "OK" if good else "TOO LOW"))
    ok, problems = check(C, L, man, plans)
    for x in problems:
        print("  PROBLEM:", x)
    return ok


if __name__ == "__main__":
    C, L, man, plans = build()
    ok = report(C, L, man, plans)
    for p in plans:
        print("\n--- slide %d : %s" % (p["n"], p["title"]))
        for l in p["lines"]:
            print("    line base=%7.2f A=%6.2f D=%6.2f right=%7.2f %s"
                  % (l["base"], l["A"], l["D"], l["right"], "OPT" if l.get("option") else ""))
    print("\nALL CHECKS PASS:", ok)
