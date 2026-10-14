"""W2 步骤1: per-cohort 差异分析（DFSP vs 对照）
GSE42948: DFSP(4) vs 其余49对照; GSE2553: DFSP(5) vs 其余176肉瘤
输出 per-gene: Wilcoxon p / AUC / median diff / BH-FDR, 仅交集基因(6752)
"""
import pandas as pd, numpy as np
from scipy import stats

OUTD = r"D:/文章/Kimi_Agent_DFSP单细胞研究/DFSP/analysis/W1_数据整理/out"
W2D = r"D:/文章/Kimi_Agent_DFSP单细胞研究/DFSP/analysis/W2_诊断签名"
import os
os.makedirs(W2D, exist_ok=True)

def bh_fdr(pvals):
    p = np.asarray(pvals, dtype=float)
    n = len(p)
    order = np.argsort(p)
    ranked = p[order]
    fdr = ranked * n / np.arange(1, n + 1)
    fdr = np.minimum.accumulate(fdr[::-1])[::-1]
    fdr = np.clip(fdr, 0, 1)
    out = np.empty_like(p)
    out[order] = fdr
    return out

def de_analysis(mat, group, test="DFSP"):
    """mat: genes x samples; group: Series[bool]; returns DataFrame per gene"""
    pos = group[group].index
    neg = group[~group].index
    genes = mat.index
    rows = []
    X = mat.values.astype(float)
    i_pos = mat.columns.get_indexer(pos)
    i_neg = mat.columns.get_indexer(neg)
    for k, g in enumerate(genes):
        a = X[k, i_pos]
        b = X[k, i_neg]
        if np.all(np.isnan(a)) or np.all(np.isnan(b)):
            rows.append((g, np.nan, np.nan, np.nan))
            continue
        try:
            u, p = stats.mannwhitneyu(a, b, alternative="two-sided")
        except Exception:
            rows.append((g, np.nan, np.nan, np.nan)); continue
        auc = u / (len(a) * len(b))
        mdiff = np.nanmedian(a) - np.nanmedian(b)
        rows.append((g, p, auc, mdiff))
    df = pd.DataFrame(rows, columns=["gene", "p", "auc", "median_diff"])
    df["fdr"] = bh_fdr(df["p"].fillna(1))
    df = df.sort_values("p")
    return df

# 载入矩阵与注释
ann = pd.read_csv(f"{OUTD}/ALL_cohorts_annotation.csv")
common = pd.read_csv(f"{OUTD}/common_genes_3cohorts.csv")["gene"].tolist()

results = {}
for cohort, mfile, tag in [
    ("GSE42948", "GSE42948_matrix.csv.gz", "g42948"),
    ("GSE2553", "GSE2553_matrix.csv.gz", "g2553"),
]:
    mat = pd.read_csv(f"{OUTD}/{mfile}", index_col=0, compression="gzip")
    mat.index = mat.index.astype(str).str.strip().str.upper()
    mat = mat.loc[[g for g in common if g in mat.index]]
    a = ann[ann["cohort"] == cohort]
    a = a[a["sample"].isin(mat.columns)]
    grp = a.set_index("sample")["disease"].eq("DFSP")
    grp = grp.reindex(mat.columns).fillna(False)
    res = de_analysis(mat, grp)
    res.to_csv(f"{W2D}/DEG_{tag}_DFSP_vs_rest.csv", index=False)
    results[tag] = res
    up = res[(res["fdr"] < 0.05) & (res["median_diff"] > 0)]
    dn = res[(res["fdr"] < 0.05) & (res["median_diff"] < 0)]
    print(f"{cohort}: DFSP {grp.sum()} vs rest {(~grp).sum()}, 基因 {len(res)}, "
          f"上调 {len(up)}, 下调 {len(dn)}")

# 方向一致的显著基因（两队列同向 + FDR<0.05）
m = pd.DataFrame({
    "p_42948": results["g42948"].set_index("gene")["p"],
    "p_2553": results["g2553"].set_index("gene")["p"],
    "md_42948": results["g42948"].set_index("gene")["median_diff"],
    "md_2553": results["g2553"].set_index("gene")["median_diff"],
})
m["dir"] = np.sign(m["md_42948"]) * np.sign(m["md_2553"])
consistent = m[(m["dir"] == 1) & (m["p_42948"] < 0.05) & (m["p_2553"] < 0.05)].dropna()
consistent.to_csv(f"{W2D}/DEG_consistent_both_cohorts.csv")
print(f"\n两队列方向一致且均显著（p<0.05）: {len(consistent)} 个基因（上调 {sum(consistent['md_42948']>0)} / 下调 {sum(consistent['md_42948']<0)}）")
