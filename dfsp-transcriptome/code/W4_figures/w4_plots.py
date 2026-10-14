"""W4 出图: Fig4 FS-ness 谱系定位（10 类肿瘤箱线图）+ TCGA 签名投影（背景验证）"""
import pandas as pd, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

OUTD = r"D:/文章/Kimi_Agent_DFSP单细胞研究/DFSP/analysis/W1_数据整理/out"
W4D = r"D:/文章/Kimi_Agent_DFSP单细胞研究/DFSP/analysis/W4_写作"

# ---------- Fig4a: FS-ness 在 10 类纤维性肿瘤中的分布 ----------
sc = pd.read_csv(f"{W4D}/FSness_scores_GSE42948.csv")
order = sc.groupby("group")["fsness"].median().sort_values().index.tolist()
order_en = {"DFSP": "DFSP", "FC": "Fibrosarcoma", "DTF": "Desmoid", "SFT": "SFT", "EF": "EF",
            "IF": "IF", "PF": "PF", "NPAF": "NPAF", "FOTS": "FOTS", "NF": "NF"}
sc["group_en"] = sc["group"].map(order_en)
palette = {g: ("#E24B4A" if g == "DFSP" else "#3B6D11" if g == "Fibrosarcoma" else "#B4B2A9") for g in sc["group_en"].unique()}
fig, ax = plt.subplots(figsize=(9, 4.5))
sns.boxplot(data=sc, x="group_en", y="fsness", order=[order_en[g] for g in order],
            palette=palette, width=0.6, fliersize=3, ax=ax)
sns.stripplot(data=sc, x="group_en", y="fsness", order=[order_en[g] for g in order],
              color="#2C2C2A", size=3, alpha=0.6, jitter=0.15, ax=ax)
ax.set_xticklabels(ax.get_xticklabels(), rotation=40, ha="right", fontsize=9)
ax.set_ylabel("FS-ness score (fibrosarcoma program ssGSEA)")
ax.set_title("Fibrosarcomatous-program score across 10 fibrous tumor types (GSE42948)")
ax.annotate("DFSP vs FC: p=0.0095", xy=(0.02, 0.95), xycoords="axes fraction", fontsize=10, color="#A32D2D")
plt.tight_layout()
fig.savefig(f"{W4D}/Fig4_FSness_spectrum.png", dpi=300, bbox_inches="tight")
plt.close()
print("Fig4a 已保存")

# ---------- Fig4b: DFSP vs FC 差异火山图数据（供仙桃/备用）----------
mat = pd.read_csv(f"{OUTD}/GSE42948_matrix.csv.gz", index_col=0, compression="gzip")
mat.index = mat.index.astype(str).str.upper()
ann = pd.read_csv(f"{OUTD}/GSE42948_annotation.csv").set_index("sample")
dfsp, fc = mat.loc[:, ann.loc[mat.columns, "group"] == "DFSP"], mat.loc[:, ann.loc[mat.columns, "group"] == "FC"]
logFC = np.log2(dfsp.median(axis=1) + 0.5) - np.log2(fc.median(axis=1) + 0.5)
from scipy import stats
pvals = []
for g in mat.index:
    try:
        u, p = stats.mannwhitneyu(dfsp.loc[g], fc.loc[g])
    except Exception:
        p = 1.0
    pvals.append(p)
vdf = pd.DataFrame({"gene": mat.index, "logFC": logFC.values, "p": pvals})
vdf.to_csv(f"{W4D}/volcano_input_DFSP_vs_FC.csv", index=False)
print("Fig4b 数据已保存", vdf.shape)

# ---------- Fig4c: 诊断签名在 TCGA-SARC 6 亚型中的投影 ----------
def ssgsea(expr, sig):
    ranks = expr.rank(ascending=True)
    s = ranks.reindex(sig).dropna()
    if len(s) < 5:
        return np.nan
    N = len(ranks); P = np.sort(s.values / N); K = len(P)
    return np.sum(P - np.arange(1, K + 1) / (K + 1)) / K

sig_genes = pd.read_csv(r"D:/文章/Kimi_Agent_DFSP单细胞研究/DFSP/analysis/W2_诊断签名/signature_consensus_genes.csv")["gene"].tolist()
tcga = pd.read_csv(f"{OUTD}/TCGA-SARC_matrix.csv.gz", index_col=0, compression="gzip")
tcga.index = tcga.index.astype(str).str.upper()
tann = pd.read_csv(f"{OUTD}/TCGA-SARC_annotation.csv")
tann = tann[tann["sample"].isin(tcga.columns)].set_index("sample")
tann["disease_short"] = tann["disease_type"].str.replace("Neoplasms", "").str.replace("Tumors and Sarcomas, NOS", "STS-NOS").str.strip()
scores = pd.DataFrame({"sample": tcga.columns,
                       "subtype": tann.loc[tcga.columns, "disease_short"],
                       "diag_score": [ssgsea(tcga[s], sig_genes) for s in tcga.columns]})
scores = scores.dropna(subset=["diag_score"])
scores.to_csv(f"{W4D}/TCGA_signature_projection.csv", index=False)
fig, ax = plt.subplots(figsize=(9, 4))
sns.boxplot(data=scores, x="subtype", y="diag_score", palette="Set2", width=0.6, fliersize=2, ax=ax)
ax.set_xticklabels(ax.get_xticklabels(), rotation=25, ha="right", fontsize=9)
ax.set_ylabel("DFSP diagnostic signature ssGSEA score")
ax.set_title("DFSP diagnostic signature in TCGA-SARC subtypes (background)")
plt.tight_layout()
fig.savefig(f"{W4D}/Fig4c_TCGA_projection.png", dpi=300, bbox_inches="tight")
plt.close()
print("Fig4c 已保存")
print(scores.groupby("subtype")["diag_score"].median().sort_values().round(3).to_string())
