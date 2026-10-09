import re, os, sys
WS = r"C:\Users\lihao\Desktop\家教\高三数学\10.8"
src = open(os.path.join(WS, "_src_sets.txt"), encoding="utf-8", errors="replace").read()
lines = src.splitlines()
print("total lines:", len(lines))
# find lines that look like question starts: 数字. or 数字．
pat = re.compile(r"^\s*(\d{1,3})\s*[.．、]\s*")
idx = []
for i, ln in enumerate(lines):
    m = pat.match(ln)
    if m:
        idx.append((int(m.group(1)), i))
print("question-start candidates:", len(idx))
print("numbers found (first 200):", [n for n, _ in idx][:200])
