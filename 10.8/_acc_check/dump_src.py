import re, os
WS = r"C:\Users\lihao\Desktop\家教\高三数学\10.8"
src = open(os.path.join(WS, "_src_sets.txt"), encoding="utf-8", errors="replace").read()
lines = src.splitlines()
pat = re.compile(r"^\s*(\d{1,3})\s*[.．、]\s*")
starts = []
for i, ln in enumerate(lines):
    m = pat.match(ln)
    if m:
        starts.append((int(m.group(1)), i))
# map num -> line index (first occurrence)
pos = {}
for n, i in starts:
    if n not in pos:
        pos[n] = i
order = sorted(pos.items(), key=lambda kv: kv[1])

out = []
want = [13, 7, 34, 9, 27, 126, 24, 148]
for n in want:
    i = pos[n]
    # end = next start line
    nxt = None
    for m, j in order:
        if j > i:
            nxt = j
            break
    end = nxt if nxt is not None else len(lines)
    out.append(f"########## SOURCE QUESTION {n}  (file lines {i+1}..{end}) ##########")
    for k in range(i, end):
        out.append(f"{k+1:5d}| {lines[k]}")
    out.append("")
txt = "\n".join(out)
open(os.path.join(WS, "_acc_check", "src_questions.txt"), "w", encoding="utf-8").write(txt)
print("written, chars:", len(txt))
