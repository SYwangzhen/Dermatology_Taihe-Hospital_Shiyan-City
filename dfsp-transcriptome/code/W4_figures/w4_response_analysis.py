# -*- coding: utf-8 -*-
"""
GSE150787 (Delyon 2021, pazopanib phase II) EGFR-axis resistance analysis.
- Individual RECIST responses are not publicly available (paper reports 5/23 PR,
  EGF/EGFR-panel enrichment associated with non-response, P=0.035).
- We quantify the EGFR-axis program in the 20 baseline tumor samples and test its
  association with proliferative/angiogenic pathway activity and its relationship
  to the PDGF axis, recapitulating the resistance-axis described by Delyon et al.
"""
import pandas as pd
import numpy as np
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

OUTD = r"D:/文章/Kimi_Agent_DFSP单细胞研究/DFSP/analysis/W1_数据整理/out"
W4D = r"D:/文章/Kimi_Agent_DFSP单细胞研究/DFSP/analysis/W4_写作"

# ---------- 1. 数据 ----------
mat = pd.read_csv(f"{OUTD}/GSE150787_matrix.csv")
mat["gene"] = mat["gene"].str.strip()
mat = mat.set_index("gene")
pw = pd.read_csv(f"{OUTD}/GSE150787_pathway_scores.csv").set_index("pathway")
samples = mat.columns.tolist()

# ---------- 2. 轴评分 ----------
EGFR_GENES = ["EGF", "EGFR", "TGFA", "EREG", "ERBB2"]          # 在 qPCR 面板中的 EGFR 轴
PDGF_GENES = ["PDGFB", "PDGFRB", "PDGFRA"]                      # PDGF 轴（帕唑帕尼主要靶点）
VEGF_GENES = ["VEGFA", "KDR", "FLT1", "PGF"]                    # VEGFR 轴

def axis_score(gene_list, m):
    sub = m.loc[[g for g in gene_list if g in m.index]]
    z = (sub - sub.mean(axis=1).values[:, None]) / (sub.std(axis=1).values[:, None] + 1e-9)
    return z.mean(axis=0)

egfr_s = axis_score(EGFR_GENES, mat)
pdgf_s = axis_score(PDGF_GENES, mat)
vegfr_s = axis_score(VEGF_GENES, mat)

df = pd.DataFrame({
    "sample": samples,
    "EGFR_axis": egfr_s.values,
    "PDGF_axis": pdgf_s.values,
    "VEGFR_axis": vegfr_s.values,
})
for pw_name in pw.index:
    df[pw_name] = pw.loc[pw_name, samples].values

# 高/低 EGFR 轴分层（中位数）
med = df["EGFR_axis"].median()
df["EGFR_group"] = np.where(df["EGFR_axis"] >= med, "High-EGFR", "Low-EGFR")
print(f"EGFR 轴评分: median={med:.3f}, range {df['EGFR_axis'].min():.3f}~{df['EGFR_axis'].max():.3f}")
print(f"分层: High={sum(df['EGFR_group']=='High-EGFR')}, Low={sum(df['EGFR_group']=='Low-EGFR')}")

# ---------- 3. 统计 ----------
print("\n=== EGFR轴高 vs 低组：通路活性 Mann-Whitney ===")
pw_stats = {}
for pw_name in ["Angiogenesis", "Cell cycle", "Cell proliferation & survival", "Apoptosis", "Adhesion-Invasion-Migration"]:
    hi = df.loc[df["EGFR_group"] == "High-EGFR", pw_name]
    lo = df.loc[df["EGFR_group"] == "Low-EGFR", pw_name]
    u, p = stats.mannwhitneyu(hi, lo)
    pw_stats[pw_name] = p
    d = np.median(hi) - np.median(lo)
    print(f"  {pw_name:35s}: High med={hi.median():+.3f} vs Low med={lo.median():+.3f}  diff={d:+.3f}  p={p:.3f}")

print("\n=== EGFR轴 vs PDGF轴 / VEGFR轴 / 通路 Spearman ===")
for col in ["PDGF_axis", "VEGFR_axis", "Angiogenesis", "Cell proliferation & survival", "Cell cycle"]:
    r, p = stats.spearmanr(df["EGFR_axis"], df[col])
    print(f"  EGFR_axis vs {col:35s}: rho={r:+.3f}  p={p:.3f}")

# EGF vs PDGFRB 单基因（RTK 切换证据）
egf_v = mat.loc["EGF"]; pdgfrb_v = mat.loc["PDGFRB"]
r, p = stats.spearmanr(egf_v, pdgfrb_v)
print(f"  EGF vs PDGFRB: rho={r:+.3f}  p={p:.3f}")

# 各基因表达统计
print("\n=== EGFR 轴基因表达（n=20）===")
for g in EGFR_GENES + PDGF_GENES:
    if g in mat.index:
        row = mat.loc[g]
        print(f"  {g:8s}: median={row.median():6.2f}  CV={row.std()/row.mean():.2f}")

df.to_csv(f"{W4D}/GSE150787_EGFR_axis_scores.csv", index=False)
print("\n轴评分表已保存: GSE150787_EGFR_axis_scores.csv", df.shape)

# ---------- 4. 出图 Fig8 ----------
sns.set_style("whitegrid")
fig = plt.figure(figsize=(17, 5.2))

# Panel A: EGFR 轴基因热图（按 EGFR 轴评分排序）
ax1 = fig.add_subplot(131)
order = df.sort_values("EGFR_axis")["sample"].tolist()
sub = mat.loc[[g for g in EGFR_GENES if g in mat.index], order]
sub = (sub - sub.mean(axis=1).values[:, None]) / (sub.std(axis=1).values[:, None] + 1e-9)
sns.heatmap(sub, cmap="RdBu_r", center=0, ax=ax1, cbar_kws={"shrink": 0.7},
            xticklabels=False, yticklabels=True, linewidths=0.4, linecolor="white")
ax1.set_title("A  EGFR-axis genes (20 baseline tumors)", fontsize=10)
ax1.set_ylabel("")
ax1.set_xlabel("Samples ordered by EGFR-axis score")
# 顶部分组条
hi_idx = [i for i, s in enumerate(order) if df.set_index("sample").loc[s, "EGFR_group"] == "High-EGFR"]
for i in range(len(order)):
    ax1.add_patch(plt.Rectangle((i, len(sub)), 1, 0.35,
                 color="#d62728" if i in hi_idx else "#1f77b4", clip_on=False))
ax1.set_ylim(len(sub) + 0.35, 0)

# Panel B: EGFR轴高 vs 低组通路活性
ax2 = fig.add_subplot(132)
pw_interest = ["Angiogenesis", "Cell proliferation & survival", "Cell cycle"]
plot_df = df.melt(id_vars=["EGFR_group"], value_vars=pw_interest, var_name="Pathway", value_name="score")
sns.boxplot(data=plot_df, x="Pathway", y="score", hue="EGFR_group", ax=ax2,
            palette={"High-EGFR": "#d62728", "Low-EGFR": "#1f77b4"},
            fliersize=3, width=0.6)
ax2.set_title("B  Pathway activity by EGFR-axis group", fontsize=10)
ax2.set_xticklabels([p.replace(" & ", " &\n") for p in pw_interest], fontsize=8)
ax2.set_ylabel("Pathway activity score")
ax2.legend(title="", fontsize=8, loc="upper right")
# p 值标注
for i, pw_name in enumerate(pw_interest):
    pv = pw_stats[pw_name]
    if pv < 0.1:
        hi = df.loc[df["EGFR_group"] == "High-EGFR", pw_name]
        lo = df.loc[df["EGFR_group"] == "Low-EGFR", pw_name]
        ymax = max(hi.max(), lo.max()) + 0.15
        ax2.plot([i - 0.2, i - 0.2, i + 0.2, i + 0.2], [ymax, ymax + 0.06, ymax + 0.06, ymax], lw=0.8, c="k")
        star = "***" if pv < 0.001 else "**" if pv < 0.01 else "*" if pv < 0.05 else "†"
        ax2.text(i, ymax + 0.09, f"p={pv:.3f}" + ("" if pv < 0.1 else ""), ha="center", fontsize=7, color="k")

# Panel C: EGFR轴 vs PDGF轴 散点
ax3 = fig.add_subplot(133)
r_all, p_all = stats.spearmanr(df["EGFR_axis"], df["PDGF_axis"])
colors = ["#d62728" if g == "High-EGFR" else "#1f77b4" for g in df["EGFR_group"]]
ax3.scatter(df["EGFR_axis"], df["PDGF_axis"], c=colors, s=45, edgecolor="white", linewidth=0.5, alpha=0.85)
z = np.polyfit(df["EGFR_axis"], df["PDGF_axis"], 1)
xs = np.linspace(df["EGFR_axis"].min() - 0.2, df["EGFR_axis"].max() + 0.2, 50)
ax3.plot(xs, np.polyval(z, xs), "k--", lw=0.8)
ax3.set_title("C  EGFR vs PDGF axis (Spearman rho)", fontsize=10)
ax3.set_xlabel("EGFR-axis score")
ax3.set_ylabel("PDGF-axis score")
ax3.text(0.05, 0.92, f"rho={r_all:+.3f}, p={p_all:.3f}", transform=ax3.transAxes,
         fontsize=9, bbox=dict(boxstyle="round", fc="w", ec="0.7"))

plt.tight_layout()
fig.savefig(f"{W4D}/Fig8_EGFR_response.png", dpi=300, bbox_inches="tight")
fig.savefig(f"{W4D}/Fig8_EGFR_response.pdf", bbox_inches="tight")
print("\nFig8 已保存: Fig8_EGFR_response.png/pdf")
