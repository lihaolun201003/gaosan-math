# -*- coding: utf-8 -*-
"""Generate 复数专题_公式源码.tex from content.json + formulas.json (hand-off source)."""
import json, os, sys
sys.stdout.reconfigure(encoding="utf-8")
DEST = os.path.dirname(os.path.abspath(__file__))
C = json.load(open(os.path.join(DEST, "content.json"), encoding="utf-8"))
F = json.load(open(os.path.join(DEST, "formulas.json"), encoding="utf-8"))
SRC = {
 2: "天津市九校联考 2024--2025 学年高三下学期第一次模拟数学试卷（第 10 题）",
 3: "天津市新华中学 2024--2025 学年高三下学期高考校模拟 2 数学试题（第 10 题）",
 4: "天津市武清区杨村第一中学 2025 届高三下学期第一次阶段性检测数学试卷（第 10 题）",
 6: "2026·南开中学五月考",
 8: "天津市河西区 2024--2025 学年高三下学期总复习质量调查二（二模）数学试题（第 10 题）",
}
QNO = {2:26, 3:39, 4:40, 5:36, 6:137, 7:58, 8:45, 9:121}

L = []
w = L.append
w(r"% !TEX program = xelatex")
w(r"% =====================================================================")
w(r"%  《复数》高三专题 · 课堂板书版 PPT —— 例题与公式源码")
w(r"%  例题全部取自《复数专题.pdf》，原题号见每题上方注释。")
w(r"%  编译： xelatex 复数专题_公式源码.tex")
w(r"% =====================================================================")
w(r"\documentclass[12pt,a4paper]{article}")
w(r"\usepackage{amsmath,amssymb}")
w(r"\usepackage{xeCJK}")
w(r"\usepackage[margin=2.4cm]{geometry}")
w(r"\setCJKmainfont{Microsoft YaHei}")
w(r"\setmainfont{Times New Roman}")
w(r"\linespread{1.3}")
w(r"\setlength{\parindent}{0pt}")
w(r"\newcommand{\dsmtitle}[1]{\par\medskip\noindent{\large\bfseries #1}\par\smallskip}")
w(r"\newcommand{\dsmsource}[1]{\par\smallskip\noindent{\small\itshape 来源：#1}\par\medskip}")
w(r"\begin{document}")
w(r"\begin{center}")
w(r"{\LARGE\bfseries 复数}\\[4pt]")
w(r"{\small 高三数学专题 · 八种题型例题（LaTeX 公式源码）}")
w(r"\end{center}")
w(r"\vspace{0.4em}\hrule\vspace{0.8em}")
for sl in C["slides"]:
    w("")
    w("%% ---------- 原卷《复数专题》第 %d 题 ----------" % QNO[sl["n"]])
    w(r"\dsmtitle{%s}" % sl["title"])
    w(r"\noindent\textbf{例题}\quad")
    for row in sl["rows"]:
        segs = [s for s in row if s["k"] != "label"]
        if len(segs) == 1 and segs[0].get("display"):
            w("\\[%s\\]" % F["snippets"][segs[0]["s"]].replace("\\displaystyle ", ""))
        else:
            body = "".join("$%s$" % F["snippets"][s["s"]] if s["k"] == "m" else s["s"] for s in segs)
            w(body + r"\par")
    w(r"\dsmsource{%s}" % SRC.get(sl["n"], "《复数专题.pdf》原卷第 %d 题" % QNO[sl["n"]]))
w("")
w(r"\end{document}")
open(os.path.join(DEST, "复数专题_公式源码.tex"), "w", encoding="utf-8").write("\n".join(L) + "\n")
print("regenerated 复数专题_公式源码.tex")
