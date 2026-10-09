# -*- coding: utf-8 -*-
"""Generate latex_source/ : one compilable XeLaTeX document per question plus the
exact formula fragments that were compiled into the deck's vector SVGs.

Everything is derived from content.json / formulas.json so the sources can never
drift from what the PPTX actually shows.  Each document is compile-tested.
"""
import json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "latex_source")
FRAG = os.path.join(OUT, "\u516c\u5f0f\u7247\u6bb5")

SRC_TITLE = {
    2: ("\u9898\u578b\u4e00\u2014\u2014\u4e0d\u7b49\u5f0f\u4e0e\u89e3\u96c6\u5305\u542b", 63),
    3: ("\u9898\u578b\u4e8c\u2014\u2014\u6307\u6570\u3001\u5bf9\u6570\u4e0e\u5b9a\u4e49\u57df", 42),
    4: ("\u9898\u578b\u4e09\u2014\u2014\u4ee3\u6570\u8fd0\u7b97\u4e0e\u53cd\u4f8b\u5224\u65ad", 40),
    5: ("\u9898\u578b\u56db\u2014\u2014\u51fd\u6570\u5355\u8c03\u6027\u4e0e\u53c2\u6570\u8303\u56f4", 61),
    6: ("\u9898\u578b\u4e94\u2014\u2014\u4e09\u89d2\u51fd\u6570\u4e0e\u5468\u671f\u6027", 125),
    7: ("\u9898\u578b\u516d\u2014\u2014\u5411\u91cf\u4e0e\u51e0\u4f55\u5173\u7cfb", 4),
    8: ("\u9898\u578b\u4e03\u2014\u2014\u6570\u5217\u6027\u8d28\u4e0e\u6761\u4ef6\u5224\u65ad", 17),
    9: ("\u9898\u578b\u516b\u2014\u2014\u89e3\u6790\u51e0\u4f55\u4e0e\u76f4\u7ebf\u5173\u7cfb", 28),
    10: ("\u9898\u578b\u4e5d\u2014\u2014\u903b\u8f91\u7efc\u5408\u4e0e\u6761\u4ef6\u9009\u53d6", 59),
}

PREAMBLE = r"""\documentclass[12pt,a4paper]{article}
\usepackage[margin=2.5cm]{geometry}
\usepackage{xeCJK}
\usepackage{amsmath,amssymb}
\usepackage{xcolor}
\setCJKmainfont{Microsoft YaHei}[BoldFont = Microsoft YaHei Bold]
\setlength{\parindent}{0pt}
\pagestyle{empty}
% 题型标题：深蓝色加粗（与 PPT 一致）
\newcommand{\qtitle}[1]{{\Large\bfseries\color[HTML]{1F3864}#1}\par\vspace{0.9em}}
"""


def seg_to_tex(seg, man, in_math=True):
    if seg.startswith("@"):
        return "$%s$" % man[seg[1:]]["tex"]
    if seg.startswith("#"):
        return seg[1:].replace(".", "\uff0e")          # A.  ->  A．
    return seg


def line_to_tex(segs, man):
    out = []
    for i, s in enumerate(segs):
        if s.startswith("@") and i and segs[i - 1].startswith("@"):
            out.append(r"\,")
        out.append(seg_to_tex(s, man))
    return "".join(out)


def build_question(sl, man, idx, fname):
    title, origin = SRC_TITLE[sl["n"]]
    body = []
    for para in sl["stem"]:
        body.append(line_to_tex(para, man) + r"\par")
    body.append(r"\vspace{0.9em}")
    opts = [line_to_tex(o, man) for o in sl["options"]]
    for a, b in ((0, 1), (2, 3)):
        if b < len(opts):
            body.append("%s \\qquad\\qquad %s\\par" % (opts[a], opts[b]))
            body.append(r"\vspace{0.45em}")
    header = (
        "%% !TEX program = xelatex\n"
        "%% ================================================================\n"
        "%% %s\n"
        "%% 对应原卷：第 %d 题      对应幻灯片：第 %d 页\n"
        "%% 编译：xelatex %s\n"
        "%% ================================================================\n"
        % (title, origin, sl["n"], fname)
    )
    return header + PREAMBLE + "\n\\begin{document}\n\n" + \
        "\\qtitle{%s}\n\n" % title + "\n".join(body) + "\n\n\\end{document}\n"


FRAG_TPL = r"""%% !TEX program = xelatex
%% 公式片段 %(name)s  —— 幻灯片第 %(page)d 页
%% 真实字号 %(size)dpt（与 PPT 中 1:1 放置一致）
%% 编译产物即 PPTX 内嵌的矢量 SVG 来源：xelatex -> pdf -> dvisvgm --no-fonts
\documentclass[border=0pt,12pt]{standalone}
\usepackage{amsmath,amssymb}
\begin{document}
\fontsize{%(size)d}{%(lead).1f}\selectfont
$%(tex)s$%%
\end{document}
"""

README = """# 《充分必要条件》课堂板书 PPT —— LaTeX 源码

本目录保存全部题目的 LaTeX 源码。PPT 中所有数学公式都是**用 XeLaTeX 真正编译**出来的
矢量图形（PDF -> SVG，字形已转成路径），不是用普通字符串模拟的。

## 目录结构

| 文件 | 说明 |
| --- | --- |
| `题目01_….tex` ~ `题目09_….tex` | 9 道题的完整源码（题干 + A/B/C/D 选项），各自可独立编译 |
| `公式片段/*.tex` | PPT 中逐条插入的公式片段源码（共 33 条），文件名与构建脚本中的编号一致 |

## 编译方式

需要 XeLaTeX（本机为 MiKTeX）。中文使用微软雅黑，数学使用 amsmath / amssymb。

```sh
xelatex 题目01_不等式与解集包含.tex
```

## 与最终 PPT 的对应关系

* 题目文件中的题干、选项与 PPT 幻灯片**逐字一致**；
* `公式片段/*.tex` 的 `\\fontsize` 就是该公式在幻灯片上的实际字号
  （题干公式 26pt，选项公式 23pt），因此在 PPT 中是 1:1 放置，不做任何缩放，
  不会出现公式被压缩变形的情况；
* 修改题目后重新生成 PPT 的流程见 PPT 所在目录的 `_build_cdt/`：
  `formulas.json`（公式清单）→ `build_math.py`（编译为 SVG+PNG）
  → `content.json`（页面内容与版式）→ `build_pptx.py`（生成 PPTX）。
"""


def run(cmd, cwd):
    p = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return p.returncode, p.stdout.decode("utf-8", "replace")


def main():
    C = json.load(open(os.path.join(HERE, "content.json"), encoding="utf-8"))
    spec = json.load(open(os.path.join(HERE, "formulas.json"), encoding="utf-8"))["snippets"]
    man = json.load(open(os.path.join(HERE, "manifest.json"), encoding="utf-8"))
    os.makedirs(FRAG, exist_ok=True)

    # ---- question documents
    written = []
    for idx, sl in enumerate(C["slides"], 1):
        title, origin = SRC_TITLE[sl["n"]]
        name = "\u9898\u76ee%02d_%s.tex" % (idx, title.split("\u2014\u2014")[1])
        path = os.path.join(OUT, name)
        open(path, "w", encoding="utf-8").write(build_question(sl, man, idx, name))
        written.append((name, path))

    # ---- formula fragments
    for name, item in spec.items():
        page = int(re.search(r"p(\d+)_", name).group(1))
        txt = FRAG_TPL % {"name": name, "page": page, "size": int(item["size"]),
                          "lead": int(item["size"]) * 1.2, "tex": item["tex"]}
        open(os.path.join(FRAG, name + ".tex"), "w", encoding="utf-8").write(txt)

    open(os.path.join(OUT, "README.md"), "w", encoding="utf-8").write(README)

    # ---- compile test
    print("questions written: %d" % len(written))
    bad = 0
    for name, path in written:
        for ext in (".aux", ".log", ".pdf"):
            p = path[:-4] + ext
            if os.path.exists(p):
                os.remove(p)
        rc, out = run(["xelatex", "-interaction=nonstopmode", "-halt-on-error", name], OUT)
        ok = os.path.exists(path[:-4] + ".pdf")
        if not ok:
            bad += 1
            print("  FAIL %s (rc=%d)\n%s" % (name, rc, out[-800:]))
        else:
            print("  OK   %-46s %.1f KB" % (name, os.path.getsize(path[:-4] + ".pdf") / 1024.0))
        for ext in (".aux", ".log", ".pdf"):
            p = path[:-4] + ext
            if os.path.exists(p):
                os.remove(p)
    print("compile failures:", bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
