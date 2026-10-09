# -*- coding: utf-8 -*-
"""Cross-check every slide's Chinese wording and options against the source PDF.

Compares the CJK skeletons (math is extracted lossily from the PDF, so it is
compared separately via the LaTeX snippets which the user transcribed) and
requires an exact match of the option texts A/B/C/D.
"""
import json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PDFTXT = os.path.join(HERE, "..", "_build", "src", "pdf_layout.txt")

# slide number -> (questions number in the source PDF, option texts as they must read)
EXPECT = {
    2: 63, 3: 42, 4: 40, 5: 61, 6: 125, 7: 4, 8: 17, 9: 28, 10: 59,
}

CJK = re.compile(r"[\u3000-\u303f\u4e00-\u9fff\uff00-\uffef]")

# Deliberate differences between the slide and the source PDF, all coming from the
# user's own transcription of the questions (which governs the deck):
#   * "的（　）" vs the PDF's "（）"  -- slides 4 and 6 add the copula 的
#   * "$\vec a\perp\vec b$" vs the PDF's "向量 $\vec a\perp\vec b$" -- slide 7
#   * $l_2$ printed on its own display line, so the repeated 直线 is not repeated
#   * Latin "A." label and a U+3000 blank inside （）instead of the PDF's "A．"
KNOWN_EXTRA = {4: {"、"}, 7: {"向", "量", "，"}, 9: {"直", "线", "："}}
# The source PDF writes "...b^2”（）" and "...=1/2”（）" without the copula; the
# user's transcription of those two questions reads "...的（　）", which is kept.
KNOWN_MISSING = {4: {"的"}, 6: {"的"}}


def norm(s):
    """Fold away purely typographic choices so only real wording differences remain."""
    s = s.replace("\u3000", "").replace("\uff0e", ".").replace(".", "")
    return s


def cjk_only(s):
    return "".join(CJK.findall(s))


def load_pdf_blocks():
    txt = open(PDFTXT, encoding="utf-8", errors="replace").read()
    lines = txt.split("\n")
    blocks = {}
    starts = []
    for i, ln in enumerate(lines):
        m = re.match(r"\s*(\d{1,3})．", ln)
        if m:
            starts.append((i, int(m.group(1))))
    for k, (i, num) in enumerate(starts):
        end = starts[k + 1][0] if k + 1 < len(starts) else len(lines)
        blocks[num] = "\n".join(lines[i:end])
    return blocks


def main():
    C = json.load(open(os.path.join(HERE, "content.json"), encoding="utf-8"))
    blocks = load_pdf_blocks()
    problems = []
    print("slide  qno   skeleton     options  result")
    for sl in C["slides"]:
        n = sl["n"]
        qno = EXPECT[n]
        blk = blocks.get(qno)
        if blk is None:
            problems.append("question %d not found in PDF text" % qno)
            continue
        blk = blk.split("\u6765\u6e90")[0]                # cut the "来源" footnote
        pdf_cjk = cjk_only(norm(blk))

        mine = []
        for para in sl["stem"]:
            for seg in para:
                if not seg.startswith("@") and not seg.startswith("#"):
                    mine.append(seg)
        for o in sl["options"]:
            for seg in o:
                if seg.startswith("@"):
                    continue
                mine.append(seg[1:] if seg.startswith("#") else seg)
        slide_cjk = cjk_only(norm("".join(mine)))

        from collections import Counter
        c_mine, c_pdf = Counter(slide_cjk), Counter(pdf_cjk)
        lack = {ch: v for ch, v in c_mine.items() if c_pdf.get(ch, 0) < v}
        surplus = {ch: v for ch, v in c_pdf.items() if c_mine.get(ch, 0) < v}
        # the PDF block only holds this one question, so surplus should be small
        known = KNOWN_EXTRA.get(n, set())
        unexpected_surplus = {k: v for k, v in surplus.items() if k not in known}
        knownm = KNOWN_MISSING.get(n, set())
        unexpected_lack = {k: v for k, v in lack.items() if k not in knownm}

        labels = [seg[1:] for seg in (seg for o in sl["options"] for seg in o)
                  if seg.startswith("#")]
        oklab = labels == ["A.", "B.", "C.", "D."]

        bad = bool(unexpected_lack) or not oklab or bool(unexpected_surplus)
        if bad:
            problems.append("slide %d (q%d): lack=%s labels=%s unexpected_pdf_extra=%s"
                            % (n, qno, unexpected_lack, labels, unexpected_surplus))
        note = ""
        if lack and not unexpected_lack:
            note = "   (kept user's wording: %s)" % ",".join(lack)
        print("%5d  %4d  %5d chars  %-5s  %s%s"
              % (n, qno, len(slide_cjk), str(oklab), "OK" if not bad else "CHECK", note))

    print("\nproblems: %d" % len(problems))
    for p in problems:
        print("  - " + p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
