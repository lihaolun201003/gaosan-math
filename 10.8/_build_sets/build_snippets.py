# -*- coding: utf-8 -*-
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mathlib import build_all, report, BASE
from snippets import SNIPPETS

if __name__ == "__main__":
    mf = os.path.join(BASE, "manifest.json")
    man, errs = build_all(SNIPPETS, mf)
    bad = report(man, errs)
    print("manifest ->", mf)
    sys.exit(1 if (errs or bad) else 0)
