import os
from PIL import Image
WS = r"C:\Users\lihao\Desktop\家教\高三数学\10.8"
PREV = os.path.join(WS, "_build_sets", "prev2")
OUT = os.path.join(WS, "_acc_check", "crops")
os.makedirs(OUT, exist_ok=True)
for pg in range(1, 10):
    im = Image.open(os.path.join(PREV, f"page-{pg:04d}.png")).convert("RGB")
    W, H = im.size  # 2667 x 1501
    # content band: y 60 .. 540 px  (i.e. up to ~194pt)
    c = im.crop((140, 60, W-140, 540))
    c = c.resize((c.width, c.height), Image.LANCZOS)
    c.save(os.path.join(OUT, f"pg{pg}_content.png"))
    print(pg, c.size)
