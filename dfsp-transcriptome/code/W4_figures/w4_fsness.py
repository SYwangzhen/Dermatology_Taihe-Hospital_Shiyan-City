"""W4: FS-ness 纤维肉瘤转化连续谱
FC(纤维肉瘤) 程序 signature（FC vs 良性纤维性对照 DEG）→ ssGSEA 打分 → 10 类肿瘤谱系定位 + GSE2553 验证
"""
import pandas as pd, numpy as np
from scipy import stats

OUTD = r"D:/文章/Kimi_Agent_DFSP单细胞研究/DFSP/analysis/W1_数据整理/out"
W4D = r"D:/文章/Kimi_Agent_DFSP单细胞研究/DFSP/analysis/W4_写作"
import os
os.makedirs(W4D, exist_ok=True)

def ssgsea_score(expr, sig):
    ranks = expr.rank(ascending=True)
    s = ranks.reindex(sig).dropna()
    if len(s) < 5:
        return np.nan
    N = len(ranks); P = np.sort(s.values / N); K = len(P)
    return np.sum(P - np.arange(1, K + 1) / (K + 1)) / K

def bh_fdr(pvals):
    p = np.asarray(pvals, float); n = len(p)
    o = np.argsort(p); r = p[o]
    fdr = np.minimum.accumulate((r * n / np.arange(1, n + 1))[::-1])[::-1]
    out = np.empty_like(p); out[o] = np.clip(fdr, 0, 1)
    return out

# GSE42948
mat = pd.read_csv(f"{OUTD}/GSE42948_matrix.csv.gz", index_col=0, compression="gzip")
mat.index = mat.index.astype(str).str.upper()
ann = pd.read_csv(f"{OUTD}/GSE42948_annotation.csv").set_index("sample")

# 分组：DFSP / FC / 良性对照（其余）
grp = ann.loc[mat.columns, "group"]
fc = grp == "FC"
dfsp = grp == "DFSP"
benign = ~(fc | dfsp)
print(f"GSE42948: DFSP {dfsp.sum()} / FC {fc.sum()} / 良性对照 {benign.sum()}")

# FC signature：FC vs 良性对照 的 Wilcoxon DEG（上调，FDR<0.05）
pos, neg = mat.loc[:, fc], mat.loc[:, benign]
pvals, aucs = [], []
for g in mat.index:
    try:
        u, p = stats.mannwhitneyu(pos.loc[g], neg.loc[g])
    except Exception:
        p, u = 1.0, 0
    pvals.append(p); aucs.append(u / (pos.shape[1] * neg.shape[1]))
fc_sig = pd.DataFrame({"gene": mat.index, "p": pvals, "auc": aucs})
fc_sig["fdr"] = bh_fdr(fc_sig["p"])
# 稳健策略：按效应量(AUC)排序取 top100 上调基因作为 FS 程序（小样本下避免 FDR 过严）
fc_up = fc_sig[fc_sig["auc"] > 0.6].sort_values("auc", ascending=False).head(100)
print(f"FC 程序 signature（AUC>0.6 取 top100 上调）: {len(fc_up)} 基因")
print("Top:", fc_up.head(20)["gene"].tolist())
fc_up.to_csv(f"{W4D}/FS_signature_genes.csv", index=False)

# FS-ness score（GSE42948 全部样本）
fs_genes = fc_up["gene"].tolist()
scores = pd.DataFrame({
    "sample": mat.columns,
    "group": grp,
    "fsness": [ssgsea_score(mat[s], fs_genes) for s in mat.columns],
})

# 谱系排序（按中位 FS-ness）
order = scores.groupby("group")["fsness"].median().sort_values().index.tolist()
print("\nFS-ness 中位排名（低→高）:")
for g in order:
    sub = scores[scores["group"] == g]["fsness"]
    print(f"  {g:6s}: median={sub.median():.4f} (n={len(sub)})")

# 统计：DFSP vs 良性 / DFSP vs FC
for name, a, b in [("DFSP vs 良性对照", dfsp, benign), ("DFSP vs FC", dfsp, fc)]:
    x = scores.loc[a, "fsness"]; y = scores.loc[b, "fsness"]
    u, p = stats.mannwhitneyu(x, y)
    print(f"{name}: DFSP median={x.median():.4f} vs 对照 median={y.median():.4f}, p={p:.4f}")

scores.to_csv(f"{W4D}/FSness_scores_GSE42948.csv", index=False)

# GSE2553 验证：同一 FS signature 打分
mat2 = pd.read_csv(f"{OUTD}/GSE2553_matrix.csv.gz", index_col=0, compression="gzip")
mat2.index = mat2.index.astype(str).str.upper()
ann2 = pd.read_csv(f"{OUTD}/GSE2553_annotation.csv").set_index("sample")
grp2 = ann2.loc[mat2.columns, "group"]
d2 = pd.DataFrame({
    "sample": mat2.columns,
    "group": np.where(grp2 == "Dermatofibrosarcoma", "DFSP", "Other_sarcoma"),
    "fsness": [ssgsea_score(mat2[s], fs_genes) for s in mat2.columns],
})
d2.to_csv(f"{W4D}/FSness_scores_GSE2553.csv", index=False)
x, y = d2.loc[d2["group"] == "DFSP", "fsness"], d2.loc[d2["group"] == "Other_sarcoma", "fsness"]
u, p = stats.mannwhitneyu(x, y)
print(f"\nGSE2553 验证: DFSP fsness={x.median():.4f} vs 其他肉瘤={y.median():.4f}, p={p:.4f}")
# 修复：取 GSE2553 中 Fibrosarcoma 样本的 fsness
fc_idx = d2.index[ann2.loc[d2["sample"], "group"].values == "Fibrosarcoma"]
if len(fc_idx):
    print(f"  纤维肉瘤(FC)单独 fsness={d2.loc[fc_idx, 'fsness'].median():.4f}")

# 保存 GSE2553 DFSP vs FC 比较
fc_2553 = d2.loc[fc_idx, "fsness"] if len(fc_idx) else pd.Series(dtype=float)
d2.to_csv(f"{W4D}/FSness_scores_GSE2553.csv", index=False)
print("完成。")
