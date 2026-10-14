# -*- coding: utf-8 -*-
"""
统一面板标签样式（仿 Figure 5 的 ABC：小号粗体、无背景框）
- Figure 4: A(左面板左上) B(右面板左上)
- Figure 6: A(左面板左上) B(右面板左上)
- Figure 8: A(上面板左上) B(下面板左上)
- Figure 2A/3A: 左上角 A; Figure 2B/3B: 左上角 B
"""
import os
from PIL import Image, ImageDraw, ImageFont

FIG = r"D:/文章/Kimi_Agent_DFSP单细胞研究/DFSP/analysis/W4_写作/JTM_submission/figures"

# 仿 Figure 5 标题内嵌字母：小号粗体黑色（Arial Bold ~30px）
FONT_CANDIDATES = [r"C:/Windows/Fonts/arialbd.ttf", r"C:/Windows/Fonts/arial.ttf"]
font = None
for fp in FONT_CANDIDATES:
    if os.path.exists(fp):
        try:
            font = ImageFont.truetype(fp, 30)
            break
        except Exception:
            pass
if font is None:
    font = ImageFont.load_default()

def add_label(im, x, y, text, size=30):
    """无背景框的粗体黑色小标签（如 Figure 5 的 ABC）"""
    if font is None or font.size != size:
        f = None
        for fp in FONT_CANDIDATES:
            if os.path.exists(fp):
                try:
                    f = ImageFont.truetype(fp, size)
                    break
                except Exception:
                    pass
    else:
        f = font
    d = ImageDraw.Draw(im)
    # 先画细白描边保证在深色背景上可读，再画黑色主体（无框）
    for dx, dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,-1),(1,-1),(-1,1)]:
        d.text((x+dx, y+dy), text, fill="white", font=f)
    d.text((x, y), text, fill="black", font=f)

# ============ Figure 4: 左右双面板 ============
im4 = Image.open(f"{FIG}/Figure4.png")
add_label(im4, 60, 30, "A")
add_label(im4, 1745, 90, "B")   # 右面板子标题下方，避开 "Drug repurposing" 标题
im4.save(f"{FIG}/Figure4.png")
print("Figure 4.png: A(左) B(右下) 无框小号")

# ============ Figure 6: 左右双面板 ============
im6 = Image.open(f"{FIG}/Figure6.png")
add_label(im6, 50, 30, "A")
add_label(im6, 1300, 30, "B")   # 右面板起点 ~1240
im6.save(f"{FIG}/Figure6.png")
print("Figure 6.png: A(左) B(右) 无框小号")

# ============ Figure 8: 上下双面板 ============
im8 = Image.open(f"{FIG}/Figure8.png")
add_label(im8, 30, 60, "A")     # 上面板
add_label(im8, 30, 760, "B")    # 下面板起点 ~708
im8.save(f"{FIG}/Figure8.png")
print("Figure 8.png: A(上) B(下) 无框小号")

# ============ Figure 2A/2B、3A/3B: 各自左上角 ============
for fn, lab in [("Figure2A.png", "A"), ("Figure2B.png", "B"),
                ("Figure3A.png", "A"), ("Figure3B.png", "B")]:
    p = os.path.join(FIG, fn)
    im = Image.open(p)
    add_label(im, 30, 30, lab)
    im.save(p)
    print(f"{fn}: 左上角 {lab}")
