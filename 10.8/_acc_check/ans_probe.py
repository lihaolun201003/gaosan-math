import os, re
WS = r"C:\Users\lihao\Desktop\家教\高三数学\10.8"
OUT = os.path.join(WS, "_acc_check")
txt = open(os.path.join(WS, "_src_answers.txt"), encoding="utf-8", errors="replace").read()
lines = txt.splitlines()
out = []
def w(s=""): out.append(str(s))
w("total lines: %d, chars: %d" % (len(lines), len(txt)))
w("count '参考答案' = %d" % txt.count("参考答案"))
w("count '答案' = %d" % txt.count("答案"))
w("count '解析' = %d" % txt.count("解析"))
w("count '【答案】' = %d" % txt.count("【答案】"))
w("count '答案：' = %d" % txt.count("答案："))
w("count '答案:' = %d" % txt.count("答案:"))
# sample of answer-like patterns
pats = [r"参考答案[：:]\s*([A-D])", r"【答案】\s*([A-D])", r"答案[：:]\s*([A-D])", r"^\s*([A-D])\s*$"]
for p in pats:
    m = re.findall(p, txt, re.M)
    w(f"pattern {p!r}: {len(m)} matches -> {m[:40]}")
w("\n--- first 80 lines ---")
for i, ln in enumerate(lines[:80]):
    w(f"{i+1:4d}| {ln}")
open(os.path.join(OUT, "ans_probe.txt"), "w", encoding="utf-8").write("\n".join(out))
print("ok")
