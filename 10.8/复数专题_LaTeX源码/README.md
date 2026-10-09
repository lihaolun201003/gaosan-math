# 《复数》高三专题 · 课堂板书版 PPT —— 源码与重建说明

本目录保存生成 `复数专题_课堂板书版.pptx` 所需的全部 LaTeX 公式源码与脚本。

## 目录内容

| 文件 | 说明 |
| --- | --- |
| `复数专题_公式源码.tex` | **主源码**：8 道例题的完整中文题干 + LaTeX 公式，可直接 `xelatex` 编译成 PDF 校对/改题。 |
| `formulas/*.tex` | PPT 中实际用到的 26 个公式片段（每个片段一个独立 `.tex`）。 |
| `svg/*.svg` | 上述片段经 XeLaTeX 编译后的**矢量图**，即 PPT 里插入的公式本体。 |
| `content.json` | 每页的标题、行结构、中文段落与公式引用（版面唯一数据源）。 |
| `formulas.json` | 公式片段名 → LaTeX 源码 的映射。 |
| `manifest.json` | 每个片段的精确排版尺寸（宽/高/基线深度，单位 sp）。 |
| `build_formulas.py` | 编译公式：`xelatex → dvisvgm --no-fonts --exact → SVG` + `pdftocairo → 1200dpi PNG`。 |
| `build_pptx.py` | 用 python-pptx 组装 9 页 PPTX（中文为可编辑文本，公式为 SVG 矢量图）。 |

## 环境依赖

- MiKTeX（`xelatex`、`dvisvgm`、`pdftocairo`）
- Python 3 + `python-pptx`、`lxml`、`Pillow`
- 字体：微软雅黑（`Microsoft YaHei`）

## 如何更换题目

1. 改 `formulas.json` 里对应片段的 LaTeX 源码（或在 `content.json` 中替换中文与公式引用）。
2. 在 `_build` 目录下执行 `python build_formulas.py` 重新编译公式。
3. 执行 `python build_pptx.py` 重新生成 PPTX（输出到上一级目录）。

> 版面参数（标题字号、页边距、行距、留白下限）集中在 `content.json` 的 `layout` 段，
> 其中 `max_content_bottom = 216`（= 540pt × 40%）保证每题下方留白 ≥ 60%。

## 版面规格

- 16:9，960 × 540 pt（13.333 × 7.5 in），纯白背景 `#FFFFFF`
- 题型标题：36 pt 加粗，深蓝 `#1F3864`，左对齐
- 题干中文：28 pt，黑色 `#000000`，微软雅黑（**在 PPT 中可直接编辑**）
- 数学公式：XeLaTeX 编译（Computer Modern 数学字体），以 **SVG 矢量图**插入，另带 PNG 回退图
- 题号仅用于制作核对，不显示在幻灯片上
