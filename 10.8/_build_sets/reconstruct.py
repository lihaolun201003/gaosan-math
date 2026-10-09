# -*- coding: utf-8 -*-
"""Reconstruct every slide's content (text segments + LaTeX) as plain strings so
the deck can be diffed against the source paper."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_deck as B


def main():
    man = json.load(open(os.path.join(B.BASE, "manifest.json"), encoding="utf-8"))
    out_path = os.path.join(B.BASE, "reconstructed.txt")
    fh = open(out_path, "w", encoding="utf-8")
    W = lambda s="": (fh.write(s + "\n"), print(s))[0]

    def line(segs):
        out = []
        for kind, val in segs:
            if kind == "t":
                out.append(val)
            elif kind == "m":
                out.append("$%s$" % man[val]["math"])
            else:
                out.append(" ")
        return "".join(out)

    print("slide 1 (cover)")
    print("  标题: 高三数学专题复习")
    print("  副标题: 集合——八大典型题型")
    print()
    for i, page in enumerate(B.PAGES, start=2):
        print("slide %d  %s" % (i, page["title"]))
        for ln in B.wrap_segments(B.Ctx(man), page["stem"], B.AVAIL):
            print("  stem :", line(ln))
        if page.get("stem2"):
            print("  stem :", line(page["stem2"]))
        if page.get("opts"):
            keys = page["opts"]
            print("  opts : " + "   ".join(
                "%s. $%s$" % ("ABCD"[j], man[k]["math"]) for j, k in enumerate(keys)))
        print()


if __name__ == "__main__":
    main()
