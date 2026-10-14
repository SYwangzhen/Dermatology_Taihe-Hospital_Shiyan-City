"""W3 步骤1: scRNA-informed ssGSEA 微环境解卷积
Ge2023 每亚群 top50 marker → 对 GSE42948/GSE2553 每样本 ssGSEA 打分 → DFSP vs 对照比较
"""
import pandas as pd, numpy as np
from scipy import stats
from collections import Counter

W1 = r"D:/文章/Kimi_Agent_DFSP单细胞研究/DFSP/analysis/W1_数据整理/out"
W2D = r"D:/文章/Kimi_Agent_DFSP单细胞研究/DFSP/analysis/W2_诊断签名"
W3D = r"D:/文章/Kimi_Agent_DFSP单细胞研究/DFSP/analysis/W3_微环境药物"
import os
os.makedirs(W3D, exist_ok=True)

# 1) Ge2023 每亚群 top50 marker
deg = pd.read_csv(f"{W1}/Ge2023_cluster_DEG_all.csv")
deg = deg[deg["avg_log2FC"] > 0.3]
sig_genes = {}
for c, g in deg.groupby("cluster"):
    genes = g.sort_values("avg_log2FC", ascending=False).head(50)["gene"].tolist()
    sig_genes[int(c)] = genes
print("亚群 signature 大小:", {k: len(v) for k, v in sig_genes.items()})

# 亚群注释
celltype = {0:'DFSP肿瘤(APOD+)',1:'DFSP肿瘤',2:'CAF/肌成纤维',3:'间质成纤维',4:'CD8/T',5:'巨噬(C1Q+)',6:'髓系炎性',7:'活化CAF',8:'T细胞',9:'间质(ECM)',10:'内皮',11:'平滑肌',12:'增殖',13:'巨噬(SPP1?)',14:'肥大'}

def ssgsea_score(expr, sig):
    """标准 ssGSEA（Barbie 2009 简化实现）：expr=Series(基因表达)"""
    ranks = expr.rank(ascending=True)
    s = ranks.reindex(sig).dropna()
    if len(s) < 5:
        return np.nan
    N = len(ranks)
    P = np.sort(s.values / N)  # 0-1
    K = len(P)
    k = np.arange(1, K + 1)
    # 经验 CDF 差分积分（近似标准公式）
    score = np.sum(P - k / (K + 1)) / K
    return score

def bh_fdr(pvals):
    p = np.asarray(pvals, float); n = len(p)
    o = np.argsort(p); r = p[o]
    fdr = np.minimum.accumulate((r * n / np.arange(1, n + 1))[::-1])[::-1]
    out = np.empty_like(p); out[o] = np.clip(fdr, 0, 1)
    return out

ann = pd.read_csv(f"{W1}/ALL_cohorts_annotation.csv")
results = {}
for cohort, mfile in [("GSE42948", "GSE42948_matrix.csv.gz"), ("GSE2553", "GSE2553_matrix.csv.gz")]:
    mat = pd.read_csv(f"{W1}/{mfile}", index_col=0, compression="gzip")
    mat.index = mat.index.astype(str).str.upper()
    a = ann[ann["cohort"] == cohort].set_index("sample")
    grp = a.loc[mat.columns, "disease"].eq("DFSP")
    # 每样本每亚群打分
    rows = {}
    for c, genes in sig_genes.items():
        scores = []
        for s in mat.columns:
            scores.append(ssgsea_score(mat[s], genes))
        rows[celltype[c]] = scores
    df = pd.DataFrame(rows, index=mat.columns)
    df["group"] = np.where(grp, "DFSP", "Control")
    results[cohort] = df
    # 差异检验
    tests = []
    for col in df.columns[:-1]:
        a_ = df.loc[df["group"] == "DFSP", col].dropna()
        b_ = df.loc[df["group"] == "Control", col].dropna()
        if len(a_) >= 3 and len(b_) >= 3:
            u, p = stats.mannwhitneyu(a_, b_)
            tests.append({"celltype": col, "p": p, "median_DFSP": a_.median(), "median_Ctrl": b_.median()})
    t = pd.DataFrame(tests)
    t["fdr"] = bh_fdr(t["p"])
    t["cohort"] = cohort
    t.to_csv(f"{W3D}/ssgsea_{cohort}_diff.csv", index=False)
    print(f"\n=== {cohort} 微环境差异（DFSP vs Control）===")
    print(t.sort_values("p").head(12).to_string(index=False))

    df.to_csv(f"{W3D}/ssgsea_{cohort}_scores.csv")

# 汇总两队列显著（fdr<0.1）的细胞程序
allt = pd.concat([pd.read_csv(f"{W3D}/ssgsea_{c}_diff.csv") for c in ["GSE42948", "GSE2553"]])
sig_ct = allt[allt["fdr"] < 0.1]["celltype"].unique()
print(f"\n两队列中任一 FDR<0.1 的细胞程序: {list(sig_ct)}")
