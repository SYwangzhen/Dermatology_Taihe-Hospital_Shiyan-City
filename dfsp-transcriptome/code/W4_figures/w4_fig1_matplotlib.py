"""Fig1: 研究设计总览（matplotlib 手绘，出版级）— 简化版 v3
四层：数据源 → 整合 → 分析模块 → 验证/输出
微调要点：去掉底部结论条；分析模块合并为 3 个；AUC 更新为泄漏安全重跑值 0.973/0.954；
副标题精简；保留 4 类图例。
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

fig, ax = plt.subplots(figsize=(12.5, 7.2))
ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")

# 调色板
C_DATA = {"fc": "#E6F1FB", "ec": "#185FA5", "tc": "#0C447C"}
C_INT  = {"fc": "#B5D4F4", "ec": "#185FA5", "tc": "#042C53"}
C_ANAL = {"fc": "#EEEDFE", "ec": "#534AB7", "tc": "#3C3489"}
C_OUT  = {"fc": "#FAEEDA", "ec": "#BA7517", "tc": "#633806"}
C_TITLE = "#042C53"

def card(x, y, w, h, title, sub="", style=C_ANAL, fs=10, subfs=8.2, lw=1.2):
    p = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.008,rounding_size=0.015",
                       fc=style["fc"], ec=style["ec"], lw=lw)
    ax.add_patch(p)
    ax.text(x + w/2, y + h - 0.026, title, ha="center", va="center",
            fontsize=fs, fontweight="bold", color=style["tc"])
    if sub:
        ax.text(x + w/2, y + h*0.30, sub, ha="center", va="center",
                fontsize=subfs, color=style["tc"], alpha=0.9)

def arrow(x1, y1, x2, y2, color="#888780", lw=1.4, style="-|>", ms=11):
    a = FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style, mutation_scale=ms,
                        color=color, lw=lw, shrinkA=2, shrinkB=2)
    ax.add_patch(a)

# ===== 标题 =====
ax.text(0.5, 0.965, "Figure 1. Study design: fully public-data integration of DFSP transcriptomes",
        ha="center", va="center", fontsize=13.5, fontweight="bold", color=C_TITLE)

XL = 0.06          # 左边界
W  = 0.88          # 可用宽度
gap = 0.014

# ===== Layer 1: 数据源 =====
ly = 0.845; h = 0.095
data_cards = [
    ("GSE42948", "3SEQ  |  4 DFSP + 49 ctrl"),
    ("GSE2553", "cDNA  |  5 DFSP + 176 sarcoma"),
    ("GSE150787", "qPCR  |  20 DFSP (pazopanib II)"),
    ("TCGA-SARC", "RNA-seq  |  265 sarcoma (bg)"),
    ("Ge2023 scRNA", "15 subclusters (metastatic)"),
]
n = len(data_cards); w = (W - (n-1)*gap) / n
data_cx = []
for i, (t, s) in enumerate(data_cards):
    x = XL + i * (w + gap)
    data_cx.append(x + w/2)
    card(x, ly, w, h, t, s, C_DATA, fs=9.5, subfs=7.6)

# ===== Layer 2: 整合 =====
iy = 0.695
card(0.36, iy, 0.28, 0.07, "Integration", "gene-symbol intersection (6,752 genes)", C_INT, fs=10, subfs=8)
for cx in data_cx:
    arrow(cx, ly + h + 0.006, 0.5, iy + 0.076)

# ===== Layer 3: 分析模块（3 个） =====
ay = 0.50; ah = 0.095
an_cards = [
    ("Diagnostic signature + ML panel", "151 genes  |  LASSO + SVM-RFE (\u22648)"),
    ("Microenvironment & drug repurposing", "scRNA-informed ssGSEA  |  ChEMBL"),
    ("FS-ness & cell-of-origin", "fibrosarcoma program  |  scRNA mapping"),
]
w3 = (W - 2*gap) / 3
an_cx = []
for i, (t, s) in enumerate(an_cards):
    x = XL + i * (w3 + gap)
    an_cx.append(x + w3/2)
    card(x, ay, w3, ah, t, s, C_ANAL, fs=10, subfs=7.8)
    arrow(0.5, iy - 0.004, x + w3/2, ay + ah + 0.006, color="#7F77DD", lw=1.2)

# ===== Layer 4: 验证/输出（4 个） =====
vy = 0.255; vh = 0.095
out_cards = [
    ("Bidirectional external ROC", "AUC 0.973 / 0.954  |  P = .001"),
    ("Immune-cold microenvironment", "stroma-high, immune-low"),
    ("Therapy map", "imatinib (PDGFRB)  |  pazopanib (FGFR1)"),
    ("FS transcriptional divergence", "DFSP vs FC, p = 0.0095"),
]
w4 = (W - 3*gap) / 4
out_cx = []
for i, (t, s) in enumerate(out_cards):
    x = XL + i * (w4 + gap)
    out_cx.append(x + w4/2)
    card(x, vy, w4, vh, t, s, C_OUT, fs=8.8, subfs=7.2)

# 箭头：分析 → 输出（4 条，按逻辑对应）
arrow(an_cx[0], ay - 0.004, out_cx[0], vy + vh + 0.006, color="#BA7517", lw=1.2)   # 签名/panel → ROC
arrow(an_cx[1], ay - 0.004, out_cx[1], vy + vh + 0.006, color="#BA7517", lw=1.2)   # 微环境 → TME
arrow(an_cx[1], ay - 0.004, out_cx[2], vy + vh + 0.006, color="#BA7517", lw=1.2)   # 药物 → 疗法图
arrow(an_cx[2], ay - 0.004, out_cx[3], vy + vh + 0.006, color="#BA7517", lw=1.2)   # FS-ness → FS 分离

# ===== 图例 =====
leg = [("Data sources (GEO / TCGA / scRNA)", C_DATA["fc"], C_DATA["ec"]),
       ("Integration", C_INT["fc"], C_INT["ec"]),
       ("Analysis modules", C_ANAL["fc"], C_ANAL["ec"]),
       ("Validation / outputs", C_OUT["fc"], C_OUT["ec"])]
for i, (lab, fc, ec) in enumerate(leg):
    x0 = 0.06 + i * 0.225
    p = FancyBboxPatch((x0, 0.055), 0.02, 0.026, boxstyle="round,pad=0.002",
                       fc=fc, ec=ec, lw=1)
    ax.add_patch(p)
    ax.text(x0 + 0.028, 0.068, lab, ha="left", va="center", fontsize=7.8, color="#2C2C2A")

out = r"D:/文章/Kimi_Agent_DFSP单细胞研究/DFSP/analysis/W4_写作/Fig1_study_design_v2"
fig.savefig(out + ".pdf", dpi=300, bbox_inches="tight", facecolor="white")
fig.savefig(out + ".png", dpi=300, bbox_inches="tight", facecolor="white")
plt.close()
print("Fig1 v3（简化版）已保存（PDF + PNG 300dpi）")
