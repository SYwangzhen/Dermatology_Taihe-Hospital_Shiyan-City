# -*- coding: utf-8 -*-
"""
修正：为多面板图添加 A、B 标签
- Figure 4.png: 双 panel (左右)  → 加 A、B
- Figure 6: Figure6A.png 本身含双 panel (箱线图+火山图) → 加 A、B，保存为 Figure 6.png；Figure6B.png 删除
- Figure 8.png: 双 panel (上下)  → 加 A、B
"""
import os
from PIL import Image, ImageDraw, ImageFont

FIG = r"D:/文章/Kimi_Agent_DFSP单细胞研究/DFSP/analysis/W4_写作/JTM_submission/figures"

FONT_CANDIDATES = [
    r"C:/Windows/Fonts/arialbd.ttf",
    r"C:/Windows/Fonts/arial.ttf",
]
font = None
for fp in FONT_CANDIDATES:
    if os.path.exists(fp):
        try:
            font = ImageFont.truetype(fp, 60)
            break
        except Exception:
            pass
if font is None:
    font = ImageFont.load_default()

def add_label(img, x, y, text):
    d = ImageDraw.Draw(img)
    bbox = d.textbbox((x, y), text, font=font)
    pad = 12
    rx1, ry1, rx2, ry2 = bbox[0]-pad, bbox[1]-pad, bbox[2]+pad, bbox[3]+pad
    overlay = Image.new("RGBA", img.size, (0,0,0,0))
    od = ImageDraw.Draw(overlay)
    od.rectangle([rx1, ry1, rx2, ry2], fill=(0, 0, 0, 200))
    img.paste(Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB"))
    d = ImageDraw.Draw(img)
    d.text((x, y), text, fill="white", font=font)

# ============ 删除之前的错误 Figure6.png ============
for f in ["Figure6.png"]:
    p = os.path.join(FIG, f)
    if os.path.exists(p):
        os.remove(p)
        print(f"删除 {f}")

# ============ Figure 4: 左右双 panel (左 A 箱线, 右 B 药物) ============
im4 = Image.open(f"{FIG}/Figure4.png")
w4, _ = im4.size
add_label(im4, 30, 25, "A")
add_label(im4, int(w4 * 0.53) + 30, 25, "B")
im4.save(f"{FIG}/Figure4.png")
print(f"Figure 4.png: 加 A、B | {im4.size}")

# ============ Figure 6: Figure6A.png (本身已含箱线+火山双 panel) 加 A、B → Figure 6.png ============
im6 = Image.open(f"{FIG}/Figure6A.png")
w6, _ = im6.size
# 左 panel (箱线图) ~0-0.55*w, 右 panel (火山图) ~0.55*w-w
add_label(im6, 30, 25, "A")
add_label(im6, int(w6 * 0.57) + 30, 25, "B")
im6.save(f"{FIG}/Figure6.png")
print(f"Figure 6.png (来自 Figure6A.png): 加 A、B | {im6.size}")

# 删除冗余 Figure6B.png
p6b = os.path.join(FIG, "Figure6B.png")
if os.path.exists(p6b):
    os.remove(p6b)
    print("删除 Figure6B.png (与 Figure 6 重复)")

# ============ Figure 8: 上下双 panel ============
im8 = Image.open(f"{FIG}/Figure8.png")
w8, h8 = im8.size
add_label(im8, 30, 25, "A")
add_label(im8, 30, int(h8 * 0.52) + 10, "B")
im8.save(f"{FIG}/Figure8.png")
print(f"Figure 8.png: 加 A、B | {im8.size}")
