import os, re
WS = r"C:\Users\lihao\Desktop\家教\高三数学\10.8"
OUT = os.path.join(WS, "_acc_check")
txt = open(os.path.join(WS, "_src_answers.txt"), encoding="utf-8", errors="replace").read()
L = txt.splitlines()
out = []
def w(*a): out.append(" ".join(str(x) for x in a))

targets = [13, 7, 34, 9, 27, 126, 24, 148]

w("=== occurrences of '第N题' markers ===")
for n in targets:
    hits = [i for i, ln in enumerate(L) if re.search(rf"第\s*{n}\s*题", ln)]
    w(f"Q{n}: '第{n}题' at lines {hits[:20]}  (total {len(hits)})")

w("")
w("=== ALL '第N题' markers found (first 60) ===")
allm = [(i, re.search(r"第\s*(\d+)\s*题", ln).group(1)) for i, ln in enumerate(L) if re.search(r"第\s*\d+\s*题", ln)]
w(f"total {len(allm)}")
w(str([(i+1, n) for i, n in allm[:80]]))

w("")
w("=== windows around each target 第N题 ===")
for n in targets:
    hits = [i for i, ln in enumerate(L) if re.search(rf"第\s*{n}\s*题", ln)]
    if not hits:
        w(f"\n########## Q{n}: NO '第{n}题' marker")
        continue
    for h in hits[:3]:
        w(f"\n########## Q{n} @ line {h+1}")
        for k in range(max(0, h-2), min(len(L), h+40)):
            w(f"{k+1:5d}| {L[k]}")

# Also: extract all 参考答案 in order with the nearest preceding 第N题
w("\n\n=== ORDERED: nearest preceding 第N题 for each 参考答案 ===")
marks = []
for i, ln in enumerate(L):
    m = re.search(r"第\s*(\d+)\s*题", ln)
    if m:
        marks.append((i, int(m.group(1))))
ans = []
for i, ln in enumerate(L):
    m = re.search(r"参考答案[：:]\s*([^\s，,。；;]*)", ln)
    if m:
        prev = [n for j, n in marks if j < i]
        ans.append((i, prev[-1] if prev else None, m.group(1), ln.strip()[:110]))
for a in ans:
    w(f"  line {a[0]+1:5d} 第{a[1]}题  ans={a[2]!r}  | {a[3]}")

open(os.path.join(OUT, "ans_locate.txt"), "w", encoding="utf-8").write("\n".join(out))
print("ok")
