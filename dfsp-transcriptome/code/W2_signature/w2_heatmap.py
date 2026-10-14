"""W2 出图: 签名基因表达热图（按 Group/Cohort 排序 + 顶部组样本色条）
v2: 隐藏左侧重叠的 yticklabels，改用方向分组 + 右侧 top 基因文本注释
"""
import pandas as pd, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

OUTD = r"D:/文章/Kimi_Agent_DFSP单细胞研究/DFSP/analysis/W1_数据整理/out"
W2D = r"D:/文章/Kimi_Agent_DFSP单细胞研究/DFSP/analysis/W2_诊断签名"

sig = pd.read_csv(f"{W2D}/signature_consensus_genes.csv")
top = sig.nsmallest(40, "effect_score")
genes = top["gene"].tolist()

ann = pd.read_csv(f"{OUTD}/ALL_cohorts_annotation.csv")
ann = ann[ann["cohort"].isin(["GSE42948", "GSE2553"])].dropna(subset=["sample"])

merged = pd.read_csv(f"{OUTD}/MERGED_zscore_matrix.csv.gz", index_col=0, compression="gzip")
merged.index = merged.index.astype(str).str.upper()
m = merged.loc[[g for g in genes if g in merged.index]]

def find_cols(sample):
    for p in ["G42948_", "G2553_"]:
        c = f"{p}{sample}"
        if c in m.columns:
            return c
    return None
ann["mcol"] = ann["sample"].apply(find_cols)
ann = ann.dropna(subset=["mcol"])

dir_map = dict(zip(top["gene"], top["direction"]))
# 自定义排序：DFSP 在最左，其余按字母升序（GSE2553 先于 GSE42948）
ann_sorted = ann.copy()
ann_sorted["disease_cat"] = pd.Categorical(
    ann_sorted["disease"], categories=["DFSP"] + sorted(ann_sorted["disease"].unique()[ann_sorted["disease"].unique() != "DFSP"].tolist())
)
ann_sorted = ann_sorted.sort_values(["disease_cat", "cohort"], ascending=[True, True])
ann_sorted = ann_sorted.drop(columns=["disease_cat"])

X = m[ann_sorted["mcol"].tolist()].T
X.columns = [g for g in genes if g in merged.index]
X = X[sorted(X.columns.tolist(), key=lambda g: (dir_map.get(g, ""), -top.set_index("gene").loc[g, "effect_score"]))]

group_color = ann_sorted["disease"].map(lambda d: "#E24B4A" if d == "DFSP" else "#B4B2A9").tolist()
cohort_color = ann_sorted["cohort"].map(lambda c: "#85B7EB" if c == "GSE42948" else "#5DCAA5").tolist()

# 方向分组：up 在前，down 在后
up_genes = [g for g in X.columns if dir_map.get(g) == "up"]
down_genes = [g for g in X.columns if dir_map.get(g) == "down"]
top_up = top[top["gene"].isin(up_genes)].sort_values("effect_score", ascending=False)["gene"].head(10).tolist()
top_down = top[top["gene"].isin(down_genes)].sort_values("effect_score", ascending=False)["gene"].head(10).tolist()

# 布局：上方色条 + 热图（y 标签隐藏）+ 右侧基因列表
fig = plt.figure(figsize=(15, 9))
gs = fig.add_gridspec(3, 2, height_ratios=[0.15, 0.15, 14], width_ratios=[20, 1.6], hspace=0.06, wspace=0.08)
ax_grp = fig.add_subplot(gs[0, 0])
ax_coh = fig.add_subplot(gs[1, 0])
ax_hm = fig.add_subplot(gs[2, 0])
ax_txt = fig.add_subplot(gs[2, 1])

ax_grp.imshow(np.array([[0, 1]] * len(group_color)), aspect="auto", cmap=matplotlib.colors.ListedColormap(group_color))
ax_grp.set_xticks([]); ax_grp.set_yticks([])
ax_grp.set_ylabel("Group", fontsize=9, rotation=0, labelpad=30, ha="right", va="center")
ax_coh.imshow(np.array([[0, 1]] * len(cohort_color)), aspect="auto", cmap=matplotlib.colors.ListedColormap(cohort_color))
ax_coh.set_xticks([]); ax_coh.set_yticks([])
ax_coh.set_ylabel("Cohort", fontsize=9, rotation=0, labelpad=30, ha="right", va="center")

sns.heatmap(X, ax=ax_hm, cmap="RdBu_r", center=0,
            xticklabels=False, yticklabels=False,
            cbar_kws={"label": "z-score", "shrink": 0.6, "pad": 0.02})

# 方向分组线 + 中点文本
n_up = len(up_genes)
ax_hm.axhline(y=n_up, color="black", lw=1.5, linestyle="--")
ax_hm.text(n_up / 2 - 0.5, n_up / 2 - 0.5, f"Up in DFSP\n(n = {n_up})", ha="center", va="center",
           fontsize=9, color="#B22222", fontweight="bold", alpha=0.7)
ax_hm.text(n_up + len(down_genes) / 2 - 0.5, n_up + len(down_genes) / 2 - 0.5,
           f"Down in DFSP\n(n = {len(down_genes)})", ha="center", va="center",
           fontsize=9, color="#1f77b4", fontweight="bold", alpha=0.7)

ax_hm.set_xlabel(f"Samples sorted: DFSP → Control, by cohort (n = {X.shape[0]})", fontsize=10)
ax_hm.set_ylabel("Top 40 signature genes (sorted by direction & effect)", fontsize=10)
ax_hm.set_yticks([])

# 右侧 top 基因文本列表
ax_txt.axis("off")
txt_lines = ["Top 10 up:", *[f"  {g}" for g in top_up], "", "Top 10 down:", *[f"  {g}" for g in top_down]]
ax_txt.text(0, 1, "\n".join(txt_lines), fontsize=8, va="top", ha="left", family="monospace")

plt.tight_layout()
fig.savefig(f"{W2D}/Fig2_heatmap_signature.png", dpi=300, bbox_inches="tight")
plt.close()
print("热图已保存: Fig2_heatmap_signature.png", X.shape)
print(f"Up in DFSP: {n_up} genes | Down in DFSP: {len(down_genes)} genes")
