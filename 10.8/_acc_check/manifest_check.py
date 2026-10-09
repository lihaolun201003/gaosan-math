# -*- coding: utf-8 -*-
import json, os, re
WS = r"C:\Users\lihao\Desktop\家教\高三数学\10.8"
d = json.load(open(os.path.join(WS, "_build_sets", "manifest.json"), encoding="utf-8"))
order = ['p2_M','p2_N','p2_cap','p2_oA','p2_oB','p2_oC','p2_oD',
'p3_A','p3_B','p3_cap','p3_oA','p3_oB','p3_oC','p3_oD',
'p4_A','p4_B','p4_cup','p4_oA','p4_oB','p4_oC','p4_oD',
'p5_A','p5_B','p5_cap','p5_oA','p5_oB','p5_oC','p5_oD',
'p6_A','p6_B','p6_cap','p6_oA','p6_oB','p6_oC','p6_oD',
'p7_A','p7_B','p7_cap','p7_oA','p7_oB','p7_oC','p7_oD',
'p8_U','p8_AB','p8_sub','p8_pair','p8_oA','p8_oB','p8_oC','p8_oD',
'p9_U','p9_U2','p9_blank']
L = []
def w(s=""): L.append(str(s))
w(f"manifest entries = {len(d)}  (deck uses 53 SVG parts)")
mis = 0
for k in order:
    e = d[k]; m = e["math"]
    t = open(os.path.join(WS, "_build_sets", "tex", k + ".tex"), encoding="utf-8").read()
    body = t.split(r"\begin{document}", 1)[-1].split(r"\end{document}")[0]
    ss = re.findall(r"\$([^$]*)\$", body)
    realtex = ss[-1] if ss else ""
    same = realtex.strip() == m.strip()
    if not same: mis += 1
    w(f"{k:9s} manifest.math={m!r}")
    w(f"{'':9s} tex_last   ={realtex!r}  MATCH={same}  wd={e['wd_pt']:.1f}pt ht={e['ht_pt']:.1f}pt")
w(f"\nMISMATCHES: {mis} of {len(order)}")
open(os.path.join(WS, "_acc_check", "manifest_vs_tex.txt"), "w", encoding="utf-8").write("\n".join(L))
print("ok, mismatches:", mis)
